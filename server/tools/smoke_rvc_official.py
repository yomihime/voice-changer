"""Run a real model directly through VCClient's Official RVC backend."""

import argparse
import json
import statistics
import time
import wave
from array import array
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from data.ModelSlot import RVCModelSlot
from voice_changer.RVC.RVCSettings import RVCSettings
from voice_changer.RVC.backend.base import RvcBackendConfig, RvcInferenceRequest
from voice_changer.RVC.backend.upstream import UpstreamRvcBackend
from voice_changer.RVC.backend.upstream_loader import load_upstream_module


def _load_pcm16_mono(path: Path) -> tuple[int, np.ndarray]:
    with wave.open(str(path), "rb") as wav_file:
        if wav_file.getsampwidth() != 2:
            raise ValueError("Input WAV must use signed 16-bit PCM")
        sample_rate = wav_file.getframerate()
        channels = wav_file.getnchannels()
        samples = np.frombuffer(
            wav_file.readframes(wav_file.getnframes()), dtype=np.int16
        )
    if channels > 1:
        samples = samples.reshape(-1, channels).astype(np.int32).mean(axis=1)
    return sample_rate, samples.astype(np.int16)


def _percentile(values: list[float], fraction: float) -> float:
    return float(np.percentile(values, fraction * 100))


def _cuda_graph_report(backend: UpstreamRvcBackend) -> dict[str, object]:
    if backend.engine is None:
        return {}
    cuda_graph = load_upstream_module("tools.cuda_graph")
    rmvpe = getattr(backend.engine, "model_rmvpe", None)
    owners = {
        "hubert": getattr(backend.engine, "model", None),
        "synthesizer": getattr(backend.engine, "net_g", None),
        "rmvpeNetwork": getattr(rmvpe, "model", None),
        "rmvpeMel": getattr(rmvpe, "mel_extractor", None),
    }
    return {
        "enabled": cuda_graph.cuda_graph_enabled(backend.device),
        "owners": {
            name: cuda_graph.get_cuda_graph_stats(owner)
            for name, owner in owners.items()
            if owner is not None
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--index", type=Path, required=True)
    parser.add_argument("--hubert-dir", type=Path, required=True)
    parser.add_argument("--rmvpe", type=Path, required=True)
    parser.add_argument("--wav", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--gpu", type=int, default=0)
    parser.add_argument("--speaker", type=int, default=0)
    parser.add_argument("--pitch", type=int, default=0)
    parser.add_argument("--f0", choices=("rmvpe", "pm", "fcpe"), default="rmvpe")
    parser.add_argument("--index-rate", type=float, default=0.0)
    parser.add_argument("--protect", type=float, default=0.5)
    parser.add_argument("--chunk-size", type=int, default=24000)
    parser.add_argument("--extra-size", type=int, default=131040)
    parser.add_argument("--requests", type=int, default=8)
    args = parser.parse_args()

    for path in (args.model, args.index, args.hubert_dir, args.rmvpe, args.wav):
        if not path.exists():
            parser.error(f"Path does not exist: {path}")
    if args.model.parent != args.index.parent:
        parser.error("Model and index must be in the same directory")
    if args.chunk_size <= 0 or args.requests <= 0:
        parser.error("chunk-size and requests must be positive")

    input_rate, samples = _load_pcm16_mono(args.wav)
    params = SimpleNamespace(
        model_dir=str(args.model.parent.parent),
        rvc_upstream_hubert=str(args.hubert_dir),
        rmvpe=str(args.rmvpe),
    )
    slot = RVCModelSlot(
        slotIndex=args.model.parent.name,
        modelFile=args.model.name,
        indexFile=args.index.name,
        samplingRate=48000,
        f0=True,
        version="v2",
        embChannels=768,
    )
    settings = RVCSettings(
        gpu=args.gpu,
        dstId=args.speaker,
        f0Detector=args.f0,
        tran=args.pitch,
        silentThreshold=0.0,
        extraConvertSize=args.extra_size,
        indexRatio=args.index_rate,
        protect=args.protect,
        rvcBackend="official",
    )
    backend = UpstreamRvcBackend(RvcBackendConfig(params, slot, settings))
    output = array("h")
    latencies: list[float] = []
    load_started = time.perf_counter()
    try:
        backend.load_model()
        load_ms = (time.perf_counter() - load_started) * 1000
        warmup_started = time.perf_counter()
        backend.warmup()
        warmup_ms = (time.perf_counter() - warmup_started) * 1000
        for sequence in range(args.requests):
            offset = sequence * args.chunk_size
            chunk = samples[offset : offset + args.chunk_size]
            if len(chunk) < args.chunk_size:
                chunk = np.pad(chunk, (0, args.chunk_size - len(chunk)))
            started = time.perf_counter()
            changed = backend.infer(
                RvcInferenceRequest(
                    audio=chunk,
                    crossfade_frame=0,
                    sola_search_frame=0,
                    input_sample_rate=input_rate,
                    output_sample_rate=48000,
                )
            )
            latencies.append((time.perf_counter() - started) * 1000)
            clipped = np.clip(changed, -32768, 32767).astype(np.int16)
            output.extend(clipped.tolist())

        report = {
            "model": str(args.model.resolve()),
            "index": str(args.index.resolve()),
            "input": str(args.wav.resolve()),
            "f0": args.f0,
            "pitch": args.pitch,
            "speaker": args.speaker,
            "indexRate": args.index_rate,
            "chunkSize": args.chunk_size,
            "requests": args.requests,
            "loadMs": load_ms,
            "warmupMs": warmup_ms,
            "latencyMs": {
                "mean": statistics.fmean(latencies),
                "p50": _percentile(latencies, 0.5),
                "p95": _percentile(latencies, 0.95),
                "samples": latencies,
            },
            "outputSamples": len(output),
            "outputPeak": max((abs(value) for value in output), default=0),
            "backend": backend.get_model_info(),
            "cudaGraph": _cuda_graph_report(backend),
        }
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with wave.open(str(args.output), "wb") as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(48000)
                wav_file.writeframes(output.tobytes())
            report["output"] = str(args.output.resolve())
        print(json.dumps(report, ensure_ascii=False, indent=2))
    finally:
        backend.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
