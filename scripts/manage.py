"""Windows source installation and relocatable distribution management."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / ".runtime"
LOCK = ROOT / "server/requirements/windows-cuda.lock"
VERSIONS = json.loads((ROOT / "scripts/runtime-versions.json").read_text(encoding="utf-8"))
PACKAGE_SUPPORT_FILES = (
    "start-windows.bat",
    "start-client-windows.bat",
    "server-gui-windows.bat",
    "scripts/windows.ps1",
    "scripts/start-client.ps1",
    "scripts/server-gui.ps1",
    "scripts/manage.py",
    "scripts/check_environment.py",
    "scripts/runtime-versions.json",
    "server/requirements/windows-cuda.lock",
    "docs/windows-setup.md",
)


def run(args, *, cwd=ROOT, env=None):
    print("+", subprocess.list2cmdline([str(x) for x in args]), flush=True)
    subprocess.run([str(x) for x in args], cwd=cwd, env=env, check=True)


def file_hash(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def verified_download(url, sha256, destination):
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        partial = destination.with_suffix(destination.suffix + ".partial")
        with urllib.request.urlopen(url, timeout=600) as response, partial.open("wb") as output:
            shutil.copyfileobj(response, output)
        if file_hash(partial) != sha256:
            raise RuntimeError(f"Download checksum mismatch: {url}")
        partial.replace(destination)
    if file_hash(destination) != sha256:
        raise RuntimeError(f"Cached download checksum mismatch: {destination}")


def node_environment():
    node = VERSIONS["node"]
    directory = RUNTIME / f"node-{node['version']}-win-x64"
    if not (directory / "npm.cmd").is_file():
        archive = RUNTIME / f"node-{node['version']}-win-x64.zip"
        verified_download(node["url"], node["sha256"], archive)
        with zipfile.ZipFile(archive) as bundle:
            bundle.extractall(RUNTIME)
    env = os.environ.copy()
    env["PATH"] = str(directory) + os.pathsep + env.get("PATH", "")
    env["npm_config_cache"] = str(RUNTIME / "npm-cache")
    return directory / "npm.cmd", env


def frontend_fingerprint():
    digest = hashlib.sha256()
    for part in ("lib", "demo"):
        folder = ROOT / "client" / part
        files = list(folder.glob("*.json")) + list(folder.glob("*.js"))
        for subdir in ("src", "worklet/src", "public"):
            files.extend(p for p in (folder / subdir).rglob("*") if p.is_file()
                         and "models" not in p.relative_to(folder).parts)
        for path in sorted(set(files)):
            digest.update(path.relative_to(ROOT).as_posix().encode())
            digest.update(bytes.fromhex(file_hash(path)))
    return digest.hexdigest()


def build_frontend():
    npm, env = node_environment()
    run([npm, "ci", "--no-audit", "--no-fund"], cwd=ROOT / "client/lib", env=env)
    run([npm, "run", "build:prod"], cwd=ROOT / "client/lib", env=env)
    # --install-links packs the local library instead of linking two React trees.
    run([npm, "ci", "--install-links", "--no-audit", "--no-fund"], cwd=ROOT / "client/demo", env=env)
    installed_library = ROOT / "client/demo/node_modules/@dannadori/voice-changer-client-js/dist/index.js"
    if file_hash(installed_library) != file_hash(ROOT / "client/lib/dist/index.js"):
        raise RuntimeError("Installed client library differs from the local build; refresh the demo's file dependency lock")
    run([npm, "run", "webpack:prod", "--", "--output-path", RUNTIME / "frontend"],
        cwd=ROOT / "client/demo", env=env)
    if not (RUNTIME / "frontend/index.html").is_file():
        raise RuntimeError("Frontend build did not produce index.html")
    (RUNTIME / "frontend.sha256").write_text(frontend_fingerprint(), encoding="ascii")


def install():
    if sys.version_info[:2] != (3, 12) or Path(sys.prefix).resolve() != (ROOT / ".venv").resolve():
        raise RuntimeError("Run install-windows.bat to use the repository's Python 3.12 virtual environment")
    uv = RUNTIME / "uv/uv.exe"
    run([uv, "pip", "sync", LOCK, "--python", sys.executable, "--require-hashes",
         "--index", VERSIONS["torch_index"], "--index-strategy", "unsafe-best-match"])
    run([uv, "pip", "check", "--python", sys.executable])
    build_frontend()
    check()
    (RUNTIME / "installed.sha256").write_text(file_hash(LOCK), encoding="ascii")
    print("Installation verified. Run start-windows.bat.")


def check():
    run([sys.executable, ROOT / "scripts/check_environment.py"], cwd=ROOT / "server")


def ensure_installed():
    if (RUNTIME / "portable/python.exe").is_file():
        return
    stamp = RUNTIME / "installed.sha256"
    if not stamp.is_file() or stamp.read_text(encoding="ascii") != file_hash(LOCK):
        install()
    else:
        frontend_stamp = RUNTIME / "frontend.sha256"
        if (not (RUNTIME / "frontend/index.html").is_file() or not frontend_stamp.is_file()
                or frontend_stamp.read_text(encoding="ascii") != frontend_fingerprint()):
            build_frontend()


def launch_env():
    env = os.environ.copy()
    env["VC_FRONTEND_DIR"] = str(RUNTIME / "frontend")
    env["PYTHONUTF8"] = "1"
    env["NUMBA_CACHE_DIR"] = str(RUNTIME / "numba-cache")
    import imageio_ffmpeg
    ffmpeg = RUNTIME / "bin/ffmpeg.exe"
    if not ffmpeg.is_file():
        ffmpeg.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(imageio_ffmpeg.get_ffmpeg_exe(), ffmpeg)
    env["PATH"] = str(ffmpeg.parent) + os.pathsep + env.get("PATH", "")
    return env


def start(extra):
    ensure_installed()
    # Backend settings/model slots continue to be owned by the application.
    run([sys.executable, "MMVCServerSIO.py", "--no-native-client", "--no-reload", *extra],
        cwd=ROOT / "server", env=launch_env())


def copy_tree(source, destination):
    shutil.copytree(source, destination,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".git", ".ruff_cache"),
                    dirs_exist_ok=True)


def prune_portable_runtime(portable):
    """Remove build/test-only payloads that cause long Windows ZIP paths."""
    portable = Path(portable).resolve()
    relative_paths = (
        "Lib/site-packages/onnx/backend/test",
        "Lib/site-packages/onnx/test",
        "Lib/site-packages/pkg_resources/tests",
        "Lib/site-packages/torch/include",
        "Lib/site-packages/torch/share/cmake",
    )
    for relative in relative_paths:
        target = (portable / relative).resolve()
        if not target.is_relative_to(portable):
            raise RuntimeError(f"Portable prune target escaped runtime: {target}")
        if target.is_dir():
            shutil.rmtree(target)


def application_files():
    """Allowlist application sources; never traverse user model/config folders."""
    files = list((ROOT / "server").glob("*.py"))
    for name in ("data", "downloader", "mods", "restapi", "sio", "voice_changer", "tools"):
        files.extend((ROOT / "server" / name).rglob("*"))
    files.extend((ROOT / "third_party/rvc").rglob("*"))
    allowed = {".py", ".json", ".txt", ".md", ".patch", ".yaml", ".yml", ".toml"}
    return sorted({p for p in files if p.is_file() and not p.is_symlink()
                   and "__pycache__" not in p.parts
                   and (p.suffix.lower() in allowed or p.name in {"LICENSE", "README"})})


def build(output):
    ensure_installed()
    check()
    if Path(sys.prefix).resolve() != (ROOT / ".venv").resolve():
        raise RuntimeError("Build requires the verified source virtual environment")
    output = output.resolve()
    if output.exists():
        raise RuntimeError(f"Output already exists; choose a new --output path: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    stage_parent = ROOT / "build"
    stage_parent.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="vcclient-", dir=stage_parent) as temporary:
        if not Path(temporary).resolve().is_relative_to(stage_parent.resolve()):
            raise RuntimeError("Packaging temporary directory escaped the build directory")
        stage = Path(temporary) / "vcclient-windows-cuda"
        stage.mkdir()
        for path in application_files():
            target = stage / path.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
        for name in PACKAGE_SUPPORT_FILES:
            target = stage / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, target)
        for path in ROOT.glob("LICENSE*"):
            shutil.copy2(path, stage / path.name)
        copy_tree(RUNTIME / "frontend", stage / ".runtime/frontend")
        print("Copying the portable Python runtime and dependencies...", flush=True)
        # Copy a relocatable standalone interpreter, never the absolute-path venv.
        portable = stage / ".runtime/portable"
        copy_tree(Path(sys.base_prefix), portable)
        copy_tree(Path(sys.prefix) / "Lib/site-packages", portable / "Lib/site-packages")
        prune_portable_runtime(portable)
        (stage / "server/model_dir").mkdir(exist_ok=True)
        # Test after relocation, before creating the distributable archive.
        run([portable / "python.exe", stage / "scripts/check_environment.py"], cwd=stage / "server")
        print("Creating the file manifest and ZIP archive...", flush=True)
        manifest = {"python": VERSIONS["python"], "requirementsSha256": file_hash(LOCK),
                    "files": {p.relative_to(stage).as_posix(): file_hash(p)
                              for p in sorted(stage.rglob("*")) if p.is_file() and "__pycache__" not in p.parts}}
        (stage / "package-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        partial = output.with_suffix(output.suffix + ".partial")
        try:
            with zipfile.ZipFile(partial, "w", zipfile.ZIP_DEFLATED, compresslevel=1, allowZip64=True) as bundle:
                for path in sorted(stage.rglob("*")):
                    if path.is_file() and "__pycache__" not in path.parts:
                        bundle.write(path, path.relative_to(Path(temporary)))
            partial.replace(output)
        finally:
            partial.unlink(missing_ok=True)
    print(f"Portable package: {output}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("install")
    sub.add_parser("check")
    sub.add_parser("start").add_argument("server_args", nargs=argparse.REMAINDER)
    sub.add_parser("build").add_argument("--output", type=Path, default=ROOT / "dist/vcclient-windows-cuda.zip")
    args = parser.parse_args()
    if args.action == "install":
        install()
    elif args.action == "check":
        check()
    elif args.action == "build":
        build(args.output)
    else:
        extra = args.server_args
        start(extra[1:] if extra[:1] == ["--"] else extra)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
    except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)
