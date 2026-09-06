from typing import Any, Mapping


def model_info_from_checkpoint(checkpoint: Mapping[str, Any]) -> dict[str, Any]:
    config = checkpoint.get("config", [])
    weights = checkpoint.get("weight", {})
    speaker_weight = weights.get("emb_g.weight") if hasattr(weights, "get") else None
    speaker_count = speaker_weight.shape[0] if hasattr(speaker_weight, "shape") else None
    return {
        "version": checkpoint.get("version", "v1"),
        "f0": bool(checkpoint.get("f0", 1)),
        "sampleRate": config[-1] if config else None,
        "speakerCount": speaker_count,
    }
