"""Extract only published web assets; never execute or copy the server/models/settings."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import zipfile

ROOT = Path(__file__).resolve().parent.parent
PREFIX = "dist/main/web_front/"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", nargs="?", default=r"E:\AI\vcclient_win_cuda_2.1.4-alpha.zip")
    parser.add_argument("--exe", default=r"E:\AI\voice-changer-native-client-win.exe")
    parser.add_argument("--verify-archive", action="store_true", help="Hash entire ZIP and compare saved Hugging Face LFS metadata")
    args = parser.parse_args()
    source = Path(args.archive).resolve()
    provenance = {}
    if args.verify_archive:
        with source.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        hf = json.loads((ROOT / "evidence/hf-root.json").read_text(encoding="utf-8"))
        remote = next(x for x in hf["data"] if x["path"] == source.name)
        expected = remote["lfs"]["oid"]
        if digest != expected:
            raise ValueError("ZIP SHA256 does not match saved official Hugging Face LFS metadata")
        provenance = {"archiveSha256": digest, "officialLfsSha256": expected, "officialArchiveExactMatch": True}
    output = ROOT / "web_front"
    entries = []
    with zipfile.ZipFile(source) as archive:
        native_path = "dist/main/_internal/native_client/voice-changer-native-client.exe"
        native_hash = hashlib.sha256(archive.read(native_path)).hexdigest()
        supplied_hash = hashlib.sha256(Path(args.exe).read_bytes()).hexdigest()
        if native_hash != supplied_hash:
            raise ValueError("The release native client does not match the supplied executable")
        for item in archive.infolist():
            if item.is_dir() or not item.filename.startswith(PREFIX):
                continue
            relative = PurePosixPath(item.filename[len(PREFIX):])
            target = output.joinpath(*relative.parts).resolve()
            if not target.is_relative_to(output.resolve()) or "\\" in str(relative):
                raise ValueError(f"Unsafe zip entry: {item.filename}")
            data = archive.read(item)  # zipfile verifies CRC for every extracted entry.
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            entries.append({"path": str(relative), "bytes": len(data), "crc32": f"{item.CRC:08x}",
                            "sha256": hashlib.sha256(data).hexdigest()})
    html = (output / "index.html").read_text(encoding="utf-8")
    active_js = re.search(r'<script[^>]+src="\./([^"]+)"', html).group(1)
    active_css = re.search(r'<link[^>]+href="\./([^"]+)"', html).group(1)
    report = {"archive": str(source), "archiveBytes": source.stat().st_size, **provenance,
              "archiveMemberPrefix": PREFIX, "nativeMember": native_path,
              "nativeSha256": native_hash, "suppliedExeSha256": supplied_hash,
              "nativeExactMatch": True,
              "version": (output / "assets/gui_settings/version.txt").read_text().strip(),
              "activeJs": active_js, "activeCss": active_css,
              "sourceMaps": [x["path"] for x in entries if x["path"].endswith(".map")],
              "files": entries}
    (ROOT / "evidence").mkdir(exist_ok=True)
    (ROOT / "evidence/release-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k != "files"}, indent=2))
    print(f"Recovered {len(entries)} files, {sum(x['bytes'] for x in entries):,} bytes")


if __name__ == "__main__":
    main()
