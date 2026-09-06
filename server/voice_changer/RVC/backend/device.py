import torch

from voice_changer.RVC.backend.exceptions import RvcDeviceError


def resolve_torch_device(gpu: int, cuda_count: int | None = None) -> torch.device:
    count = torch.cuda.device_count() if cuda_count is None else cuda_count
    if gpu < 0:
        return torch.device("cpu")
    if gpu >= count:
        raise RvcDeviceError(f"CUDA device cuda:{gpu} is not available (device count: {count})")
    return torch.device(f"cuda:{gpu}")
