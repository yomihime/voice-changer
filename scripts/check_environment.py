"""Fail installation/build on real runtime, CUDA, ONNX or application import errors."""

from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "server"))


def main():
    import numpy as np
    import torch
    import torchaudio
    import fairseq
    import faiss
    import pyworld
    import parselmouth
    import resampy
    import torchfcpe
    from transformers import HubertModel
    from voice_changer.RVC.backend.upstream_loader import load_upstream_module
    from voice_changer.RVC.backend.legacy import LegacyRvcBackend
    from restapi.MMVC_Rest import MMVC_Rest
    from mods.ssl import create_self_signed_cert

    if not torch.cuda.is_available():
        raise RuntimeError("NVIDIA CUDA is unavailable. Check the NVIDIA driver and Windows CUDA installation profile.")
    device = torch.device("cuda:0")
    value = torch.ones(16, device=device).sum().item()
    assert value == 16
    audio = torch.zeros(4800, device=device)
    assert torchaudio.transforms.Resample(48000, 16000).to(device)(audio).numel() == 1600
    assert resampy.resample(np.zeros(4800, dtype=np.float32), 48000, 16000).size == 1600
    load_upstream_module("infer.rtrvc")
    with tempfile.TemporaryDirectory() as directory:
        create_self_signed_cert("test.cert", "test.key", {
            "Country": "CN", "State": "Local", "City": "Local", "Organization": "VCClient", "Org. Unit": "Runtime"
        }, cert_dir=directory)
    # Installing ORT GPU is insufficient: exercise a CUDA inference session.
    import onnx
    import onnxruntime as ort
    from onnx import TensorProto, helper
    if hasattr(ort, "preload_dlls"):
        ort.preload_dlls()
    graph = helper.make_graph([helper.make_node("Add", ["x", "x"], ["y"])], "cuda-check",
                              [helper.make_tensor_value_info("x", TensorProto.FLOAT, [1])],
                              [helper.make_tensor_value_info("y", TensorProto.FLOAT, [1])])
    model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 17)])
    model.ir_version = 9
    onnx.checker.check_model(model)
    session = ort.InferenceSession(model.SerializeToString(), providers=["CUDAExecutionProvider"])
    assert session.get_providers()[0] == "CUDAExecutionProvider", session.get_providers()
    np.testing.assert_array_equal(session.run(None, {"x": np.array([2], dtype=np.float32)})[0], [4])
    print(f"Runtime OK: Python {sys.version.split()[0]}, torch {torch.__version__}, CUDA {torch.version.cuda}, "
          f"{torch.cuda.get_device_name(0)}, ORT {ort.__version__}")
    print("Legacy/Official modules, resamplers, HTTPS certificate and CUDA/ONNX execution passed.")
    print("Model inference and live audio quality require separate model/device validation.")


if __name__ == "__main__":
    main()
