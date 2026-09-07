"""Rebuild and verify the pinned Official RVC runtime slice.

The source tree is read with ``git show <commit>:<path>`` so local upstream
changes cannot leak into the vendor import. The checked-in patch is then
applied to an isolated directory before byte-for-byte comparison.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "third_party/rvc"
MANIFEST = VENDOR / "vendor-manifest.json"
PATCH = VENDOR / "patches/0001-vcclient-runtime-adapter.patch"

SOURCE_MAPPINGS = {
    "LICENSE": "LICENSE",
    "README.md": "README.upstream.md",
    "requirments_cu118_py312.txt": "requirements-upstream-cu118.txt",
    "requirments_cu128_py312.txt": "requirements-upstream-cu128.txt",
    "configs/config.json": "configs/config.json",
    "configs/config.py": "configs/config.py",
    "configs/v1/32k.json": "configs/v1/32k.json",
    "configs/v1/40k.json": "configs/v1/40k.json",
    "configs/v1/48k.json": "configs/v1/48k.json",
    "configs/v2/32k.json": "configs/v2/32k.json",
    "configs/v2/48k.json": "configs/v2/48k.json",
    "i18n/i18n.py": "i18n/i18n.py",
    "i18n/locale/en_US.json": "i18n/locale/en_US.json",
    "i18n/locale/es_ES.json": "i18n/locale/es_ES.json",
    "i18n/locale/fr_FR.json": "i18n/locale/fr_FR.json",
    "i18n/locale/it_IT.json": "i18n/locale/it_IT.json",
    "i18n/locale/ja_JP.json": "i18n/locale/ja_JP.json",
    "i18n/locale/ko_KR.json": "i18n/locale/ko_KR.json",
    "i18n/locale/pt_BR.json": "i18n/locale/pt_BR.json",
    "i18n/locale/ru_RU.json": "i18n/locale/ru_RU.json",
    "i18n/locale/tr_TR.json": "i18n/locale/tr_TR.json",
    "i18n/locale/zh_CN.json": "i18n/locale/zh_CN.json",
    "i18n/locale/zh_HK.json": "i18n/locale/zh_HK.json",
    "i18n/locale/zh_SG.json": "i18n/locale/zh_SG.json",
    "i18n/locale/zh_TW.json": "i18n/locale/zh_TW.json",
    "infer/fcpe.py": "infer/fcpe.py",
    "infer/hubert.py": "infer/hubert.py",
    "infer/rmvpe.py": "infer/rmvpe.py",
    "infer/rtrvc.py": "infer/rtrvc.py",
    "infer/module/attentions.py": "infer/module/attentions.py",
    "infer/module/commons.py": "infer/module/commons.py",
    "infer/module/models.py": "infer/module/models.py",
    "infer/module/modules.py": "infer/module/modules.py",
    "infer/module/transforms.py": "infer/module/transforms.py",
    "tools/cuda_graph.py": "tools/cuda_graph.py",
    "tools/file_io.py": "tools/file_io.py",
}
LOCAL_PACKAGE_FILES = {
    "__init__.py",
    "configs/__init__.py",
    "i18n/__init__.py",
    "infer/__init__.py",
    "infer/module/__init__.py",
    "tools/__init__.py",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_bytes(upstream: Path, commit: str, source: str) -> bytes:
    process = subprocess.run(
        [
            "git",
            "-c",
            f"safe.directory={upstream.resolve().as_posix()}",
            "-C",
            str(upstream),
            "show",
            f"{commit}:{source}",
        ],
        capture_output=True,
    )
    if process.returncode:
        raise RuntimeError(
            f"Unable to read {source} at {commit}: "
            f"{process.stderr.decode(errors='replace').strip()}"
        )
    return process.stdout


def load_manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def write_manifest(upstream: Path, commit: str) -> None:
    entries = []
    for source, destination in SOURCE_MAPPINGS.items():
        content = git_bytes(upstream, commit, source)
        entries.append(
            {
                "source": source,
                "destination": destination,
                "sha256": sha256(content),
            }
        )
    manifest = {
        "repository": "https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI",
        "upstreamCommit": commit,
        "files": entries,
        "localPackageFiles": sorted(LOCAL_PACKAGE_FILES),
        "patch": PATCH.relative_to(VENDOR).as_posix(),
    }
    MANIFEST.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def extract_source(upstream: Path, destination: Path, manifest: dict) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    commit = manifest["upstreamCommit"]
    for entry in manifest["files"]:
        content = git_bytes(upstream, commit, entry["source"])
        if sha256(content) != entry["sha256"]:
            raise RuntimeError(f"Source checksum mismatch: {entry['source']}")
        target = destination / entry["destination"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)


def apply_patch(destination: Path) -> None:
    subprocess.run(
        [
            "git",
            "apply",
            "--unsafe-paths",
            "--unidiff-zero",
            "--whitespace=nowarn",
            f"--directory={destination.resolve().as_posix()}",
            str(PATCH),
        ],
        cwd=ROOT,
        check=True,
    )


def runtime_paths(manifest: dict) -> set[str]:
    return {
        entry["destination"] for entry in manifest["files"]
    } | set(manifest["localPackageFiles"])


def compare_runtime(materialized: Path, manifest: dict) -> None:
    failures = []
    for relative in sorted(runtime_paths(manifest)):
        expected = materialized / relative
        actual = VENDOR / relative
        if not expected.is_file() or not actual.is_file():
            failures.append(f"missing: {relative}")
        elif sha256(expected.read_bytes().replace(b"\r\n", b"\n")) != sha256(
            actual.read_bytes().replace(b"\r\n", b"\n")
        ):
            failures.append(f"different: {relative}")
    if failures:
        raise RuntimeError("Vendor replay mismatch:\n" + "\n".join(failures))


def materialize(upstream: Path, destination: Path, manifest: dict) -> None:
    if destination.exists() and any(destination.iterdir()):
        raise RuntimeError(f"Output directory must be empty: {destination}")
    extract_source(upstream, destination, manifest)
    apply_patch(destination)


def refresh_patch(upstream: Path, manifest: dict) -> None:
    with tempfile.TemporaryDirectory(prefix="rvc-vendor-") as temporary:
        temporary_path = Path(temporary)
        original = temporary_path / "original"
        patched = temporary_path / "patched"
        extract_source(upstream, original, manifest)
        for relative in sorted(runtime_paths(manifest)):
            source = VENDOR / relative
            if not source.is_file():
                raise RuntimeError(f"Current vendor runtime is missing: {relative}")
            target = patched / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        process = subprocess.run(
            [
                "git",
                "diff",
                "--no-index",
                "--binary",
                "--unified=0",
                "--src-prefix=a/",
                "--dst-prefix=b/",
                "--",
                "original",
                "patched",
            ],
            cwd=temporary_path,
            capture_output=True,
        )
        if process.returncode not in (0, 1):
            raise RuntimeError(process.stderr.decode(errors="replace"))
        rendered = (
            process.stdout.replace(b"a/original/", b"a/")
            .replace(b"b/original/", b"b/")
            .replace(b"a/patched/", b"a/")
            .replace(b"b/patched/", b"b/")
        )
        PATCH.parent.mkdir(parents=True, exist_ok=True)
        PATCH.write_bytes(rendered)


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("check", "refresh-patch"):
        child = subparsers.add_parser(command)
        child.add_argument("--upstream", type=Path, required=True)
    refresh = subparsers.add_parser("refresh-manifest")
    refresh.add_argument("--upstream", type=Path, required=True)
    refresh.add_argument("--commit", required=True)
    replay = subparsers.add_parser("materialize")
    replay.add_argument("--upstream", type=Path, required=True)
    replay.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if args.command == "refresh-manifest":
        write_manifest(args.upstream, args.commit)
        print(f"Wrote {MANIFEST}")
        return 0

    manifest = load_manifest()
    if args.command == "refresh-patch":
        refresh_patch(args.upstream, manifest)
        print(f"Wrote {PATCH}")
        return 0
    if args.command == "materialize":
        materialize(args.upstream, args.output.resolve(), manifest)
        print(f"Materialized {manifest['upstreamCommit']} at {args.output.resolve()}")
        return 0

    with tempfile.TemporaryDirectory(prefix="rvc-vendor-check-") as temporary:
        rebuilt = Path(temporary) / "rvc"
        materialize(args.upstream, rebuilt, manifest)
        compare_runtime(rebuilt, manifest)
    print(
        json.dumps(
            {
                "status": "ok",
                "upstreamCommit": manifest["upstreamCommit"],
                "runtimeFiles": len(runtime_paths(manifest)),
                "patch": str(PATCH.relative_to(ROOT)),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
