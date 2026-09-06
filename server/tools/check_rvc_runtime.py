"""Diagnose an RVC runtime without masking CUDA or native-library failures."""

import argparse
import importlib.metadata
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


PACKAGE_IMPORTS = {
    "torch": "torch",
    "torchaudio": "torchaudio",
    "numpy": "numpy",
    "faiss-cpu": "faiss",
    "transformers": "transformers",
    "praat-parselmouth": "parselmouth",
    "torchfcpe": "torchfcpe",
    "resampy": "resampy",
}


def _probe_import(module: str, *, application_order: bool = True) -> dict[str, Any]:
    source = f"import {module}; print('ok')"
    if application_order and module != "numpy":
        source = f"import numpy; {source}"
    command = [
        sys.executable,
        "-c",
        source,
    ]
    try:
        process = subprocess.run(command, capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired as exc:
        return {
            "ok": False,
            "timedOut": True,
            "stdout": exc.stdout.strip() if isinstance(exc.stdout, str) else None,
            "stderr": exc.stderr.strip() if isinstance(exc.stderr, str) else None,
        }
    return {
        "ok": process.returncode == 0,
        "exitCode": process.returncode,
        "stderr": process.stderr.strip() or None,
    }


def _probe_torch(gpu: int) -> dict[str, Any]:
    source = f"""
import json
import numpy
import torch
gpu = {gpu}
result = {{
    'torch': torch.__version__,
    'cudaRuntime': torch.version.cuda,
    'cudaAvailable': torch.cuda.is_available(),
    'deviceCount': torch.cuda.device_count(),
}}
if gpu >= 0 and gpu < result['deviceCount']:
    result.update({{
        'selectedDevice': f'cuda:{{gpu}}',
        'gpuName': torch.cuda.get_device_name(gpu),
        'capability': list(torch.cuda.get_device_capability(gpu)),
        'memoryMiB': torch.cuda.get_device_properties(gpu).total_memory / 1024 / 1024,
    }})
elif gpu < 0:
    result['selectedDevice'] = 'cpu'
else:
    result['deviceError'] = f'cuda:{{gpu}} is unavailable'
print(json.dumps(result))
"""
    try:
        process = subprocess.run(
            [sys.executable, "-c", source],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "ok": False,
            "timedOut": True,
            "stdout": exc.stdout.strip() if isinstance(exc.stdout, str) else None,
            "stderr": exc.stderr.strip() if isinstance(exc.stderr, str) else None,
        }
    output = process.stdout.strip().splitlines()
    if process.returncode == 0 and output:
        try:
            result = json.loads(output[-1])
            result["ok"] = "deviceError" not in result
            result["stderr"] = process.stderr.strip() or None
            return result
        except json.JSONDecodeError:
            pass
    return {
        "ok": False,
        "exitCode": process.returncode,
        "stdout": process.stdout.strip() or None,
        "stderr": process.stderr.strip() or None,
    }


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser()
    parser.add_argument("--gpu", type=int, default=0)
    parser.add_argument(
        "--vendor-root", type=Path, default=repo_root / "third_party" / "rvc"
    )
    parser.add_argument(
        "--hubert-dir",
        type=Path,
        default=repo_root / "server" / "pretrain" / "rvc-upstream-hubert-base",
    )
    parser.add_argument(
        "--rmvpe", type=Path, default=repo_root / "server" / "pretrain" / "rmvpe.pt"
    )
    parser.add_argument("--json", type=Path)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    required_vendor_files = (
        "LICENSE",
        "UPSTREAM.md",
        "infer/rtrvc.py",
        "infer/hubert.py",
        "infer/rmvpe.py",
        "infer/module/models.py",
        "tools/cuda_graph.py",
    )
    required_hubert_files = (
        "config.json",
        "preprocessor_config.json",
        "pytorch_model.bin",
    )
    package_report = {}
    for distribution, module in PACKAGE_IMPORTS.items():
        try:
            version = importlib.metadata.version(distribution)
        except importlib.metadata.PackageNotFoundError:
            version = None
        package_report[distribution] = {
            "version": version,
            "import": _probe_import(module) if version else {"ok": False, "missing": True},
        }

    report = {
        "python": sys.version,
        "executable": sys.executable,
        "packages": package_report,
        "directTorchImport": _probe_import("torch", application_order=False),
        "torchProbe": _probe_torch(args.gpu),
        "vendor": {
            "root": str(args.vendor_root.resolve()),
            "files": {
                relative: (args.vendor_root / relative).is_file()
                for relative in required_vendor_files
            },
        },
        "assets": {
            "hubertDirectory": str(args.hubert_dir.resolve()),
            "hubertFiles": {
                relative: (args.hubert_dir / relative).is_file()
                for relative in required_hubert_files
            },
            "rmvpe": {
                "path": str(args.rmvpe.resolve()),
                "exists": args.rmvpe.is_file(),
            },
        },
    }
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(rendered + "\n", encoding="utf-8")

    failures = [
        not all(report["vendor"]["files"].values()),
        not all(report["assets"]["hubertFiles"].values()),
        not report["assets"]["rmvpe"]["exists"],
        not all(item["import"]["ok"] for item in package_report.values()),
        not report["torchProbe"]["ok"],
    ]
    return 1 if args.strict and any(failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
