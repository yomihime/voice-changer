"""Assemble the Windows desktop client from a pinned official Electron archive.

Only Python's standard library is needed; no npm installs or C++/Rust compiler.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from contextlib import contextmanager
from pathlib import Path, PurePosixPath
import shutil
import urllib.request
import uuid
import zipfile

ROOT = Path(__file__).resolve().parents[1]
APP_FILES = ("package.json", "main.cjs", "runtime.cjs", "policy.cjs", "self-test.cjs", "frontend-self-test.cjs", "icon.png", "README.md")
EXECUTABLE = "vcclient-desktop.exe"


def frontend_files(root=ROOT):
    """Explicit source inputs: no model, profile, reverse-engineering or dist trees."""
    source = Path(root) / "client/frontend"
    files = [source / name for name in ("index.html", "NOTICE.md", "server.cjs")]
    for folder in ("src", "public"):
        files.extend(sorted((source / folder).rglob("*")))
    return [path for path in files if path.is_file() and not path.is_symlink()]


def copy_frontend(application, root=ROOT):
    source = Path(root) / "client/frontend"
    destination = Path(application) / "frontend"
    for file in frontend_files(root):
        relative = file.relative_to(source)
        if relative.as_posix() == "server.cjs":
            output = destination / relative
        elif relative.parts[0] == "public":
            output = destination / "dist" / Path(*relative.parts[1:])
        else:
            output = destination / "dist" / relative
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(file, output)


def file_hash(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def specification(root=ROOT):
    return json.loads((Path(root) / "client/desktop/electron-runtime.json").read_text(encoding="utf-8"))


def source_fingerprint(root=ROOT):
    root = Path(root)
    digest = hashlib.sha256()
    files = [root / "client/desktop" / name for name in (*APP_FILES, "electron-runtime.json")]
    files += [root / "scripts/desktop.py", root / "LICENSE"]
    files += frontend_files(root)
    for path in files:
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(bytes.fromhex(file_hash(path)))
    return digest.hexdigest()


def verified_archive(spec, cache, supplied=None):
    cache = Path(cache)
    cache.parent.mkdir(parents=True, exist_ok=True)
    if supplied:
        supplied = Path(supplied)
        if file_hash(supplied) != spec["sha256"]:
            raise RuntimeError("Electron archive checksum mismatch")
        if supplied.resolve() != cache.resolve():
            shutil.copyfile(supplied, cache)
    if not cache.exists():
        partial = cache.with_suffix(".partial")
        try:
            with urllib.request.urlopen(spec["url"], timeout=120) as response, partial.open("wb") as output:
                shutil.copyfileobj(response, output)
            if file_hash(partial) != spec["sha256"]:
                raise RuntimeError("Electron download checksum mismatch")
            partial.replace(cache)
        finally:
            partial.unlink(missing_ok=True)
    if file_hash(cache) != spec["sha256"]:
        raise RuntimeError("Cached Electron archive checksum mismatch")
    return cache


def extract_archive(archive, destination):
    destination = Path(destination).resolve()
    with zipfile.ZipFile(archive) as bundle:
        for info in bundle.infolist():
            relative = PurePosixPath(info.filename.replace("\\", "/"))
            target = (destination / relative).resolve()
            if (relative.is_absolute() or ".." in relative.parts or ":" in str(relative)
                    or not target.is_relative_to(destination)
                    or (info.external_attr >> 16) & 0o170000 == 0o120000):
                raise RuntimeError(f"Unsafe Electron archive member: {info.filename}")
        bundle.extractall(destination)


def verify(directory, fingerprint=None):
    directory = Path(directory).resolve()
    manifest = json.loads((directory / "desktop-manifest.json").read_text(encoding="utf-8"))
    if fingerprint is not None and manifest["sourceFingerprint"] != fingerprint:
        raise RuntimeError("Desktop sources have changed; rebuild the desktop client")
    files = manifest["files"]
    for required in (EXECUTABLE, "LICENSE", "LICENSES.chromium.html", "resources/app/main.cjs"):
        if required not in files:
            raise RuntimeError(f"Desktop manifest missing {required}")
    for name, digest in files.items():
        path = (directory / name).resolve()
        if not path.is_relative_to(directory) or not path.is_file() or file_hash(path) != digest:
            raise RuntimeError(f"Desktop file verification failed: {name}")
    actual = {path.relative_to(directory).as_posix() for path in directory.rglob("*") if path.is_file()}
    if actual != set(files) | {"desktop-manifest.json"}:
        raise RuntimeError("Unexpected files in desktop distribution (profile/cache must stay outside it)")
    return manifest


@contextmanager
def build_directory(runtime):
    # Python's TemporaryDirectory uses a private Windows ACL. If it is renamed
    # into the installed app, sandboxed Chromium children cannot load the DLLs.
    # A regular directory inherits the destination's normal read/execute ACL.
    runtime = Path(runtime).resolve()
    temporary = runtime / f"desktop-build-{uuid.uuid4().hex}"
    temporary.mkdir()
    try:
        yield temporary
    finally:
        resolved = temporary.resolve()
        if resolved.parent != runtime or not resolved.name.startswith("desktop-build-"):
            raise RuntimeError("Desktop cleanup escaped its staging directory")
        shutil.rmtree(resolved)


def build(root=ROOT, archive=None):
    root = Path(root).resolve()
    runtime = root / ".runtime"
    runtime.mkdir(exist_ok=True)
    destination = runtime / "desktop"
    fingerprint = source_fingerprint(root)
    if destination.exists():
        try:
            verify(destination, fingerprint)
            return destination / EXECUTABLE
        except (OSError, ValueError, KeyError, RuntimeError):
            pass
    spec = specification(root)
    cache = runtime / "desktop-downloads" / f"electron-v{spec['version']}-{spec['platform']}.zip"
    verified_archive(spec, cache, archive)
    with build_directory(runtime) as temporary:
        temporary = Path(temporary).resolve()
        if not temporary.is_relative_to(runtime.resolve()):
            raise RuntimeError("Desktop staging escaped runtime")
        stage = temporary / "desktop"
        stage.mkdir()
        extract_archive(cache, stage)
        (stage / "electron.exe").rename(stage / EXECUTABLE)
        (stage / "resources/default_app.asar").unlink(missing_ok=True)
        application = stage / "resources/app"
        application.mkdir()
        for name in APP_FILES:
            shutil.copyfile(root / "client/desktop" / name, application / name)
        shutil.copyfile(root / "LICENSE", application / "LICENSE")
        copy_frontend(application, root)
        manifest = {
            "electron": spec, "sourceFingerprint": fingerprint,
            "files": {path.relative_to(stage).as_posix(): file_hash(path)
                      for path in sorted(stage.rglob("*")) if path.is_file()},
        }
        (stage / "desktop-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        verify(stage, fingerprint)
        previous = temporary / "previous"
        if destination.exists():
            destination.rename(previous)
        try:
            stage.rename(destination)
        except OSError:
            if previous.exists():
                previous.rename(destination)
            raise
    return destination / EXECUTABLE


def package(output, archive=None):
    executable = build(archive=archive)
    directory = executable.parent
    verify(directory, source_fingerprint())
    output = Path(output).resolve()
    if output.exists():
        raise RuntimeError(f"Output already exists: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    partial = output.with_suffix(output.suffix + ".partial")
    try:
        with zipfile.ZipFile(partial, "w", zipfile.ZIP_DEFLATED, compresslevel=1) as bundle:
            for file in sorted(directory.rglob("*")):
                if file.is_file():
                    bundle.write(file, Path("vcclient-desktop") / file.relative_to(directory))
        partial.replace(output)
    finally:
        partial.unlink(missing_ok=True)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("build", "verify", "package"))
    parser.add_argument("--archive", type=Path, help="Previously downloaded official archive (hash checked)")
    parser.add_argument("--output", type=Path, default=ROOT / "dist/vcclient-desktop-win-x64.zip")
    args = parser.parse_args()
    if args.action == "build":
        print(build(archive=args.archive))
    elif args.action == "package":
        print(package(args.output, archive=args.archive))
    else:
        manifest = verify(ROOT / ".runtime/desktop", source_fingerprint())
        print(f"Desktop verified: Electron {manifest['electron']['version']}")


if __name__ == "__main__":
    main()
