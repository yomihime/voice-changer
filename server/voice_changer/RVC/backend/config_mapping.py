from typing import Any

from voice_changer.RVC.backend.exceptions import RvcBackendConfigError

SUPPORTED_UPSTREAM_F0_METHODS = {"rmvpe", "fcpe", "pm"}


def validate_upstream_f0(method: str, model_uses_f0: bool = True) -> None:
    if model_uses_f0 and method not in SUPPORTED_UPSTREAM_F0_METHODS:
        raise RvcBackendConfigError(
            f"Official RVC does not support f0Detector={method!r}; "
            f"choose one of {sorted(SUPPORTED_UPSTREAM_F0_METHODS)}"
        )


def apply_upstream_runtime_setting(
    engine: Any, key: str, value: int | float | str
) -> bool:
    if key == "tran":
        engine.change_key(int(value))
    elif key == "indexRatio":
        engine.change_index_rate(float(value))
    elif key == "dstId":
        engine.change_speaker_id(int(value))
    else:
        return False
    return True
