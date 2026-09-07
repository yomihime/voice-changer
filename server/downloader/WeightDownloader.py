import os
import hashlib
from concurrent.futures import ThreadPoolExecutor

from downloader.Downloader import download
from mods.log_control import VoiceChangaerLogger
from voice_changer.utils.VoiceChangerParams import VoiceChangerParams
from Exceptions import WeightDownladException

logger = VoiceChangaerLogger.get_instance().getLogger()
RVC_UPSTREAM_ASSET_REVISION = "e6d0c1a17da07c33557852f9dfa2bd44cc75737d"
RVC_UPSTREAM_ASSET_BASE = (
    "https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/"
    f"{RVC_UPSTREAM_ASSET_REVISION}/hubert_base"
)
RVC_UPSTREAM_ASSETS = {
    "config.json": "0346950779dfb7f9316fa74ed846e2b8a22a08eedfdc5387b73f327cb1a4a7cf",
    "preprocessor_config.json": "7c1976a680fb7acc757cd36fb08eef878fa36c70b4c9d2d595df9c608bbbbf0e",
    "pytorch_model.bin": "cc8c20f4b90a520757260197a3ff2505705a7adbd20ad9eeaa4e1a9b38442ef5",
}


def _sha256(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _rvc_upstream_asset_paths(
    voiceChangerParams: VoiceChangerParams,
) -> dict[str, str]:
    return {
        filename: os.path.join(voiceChangerParams.rvc_upstream_hubert, filename)
        for filename in RVC_UPSTREAM_ASSETS
    }


def rvcUpstreamAssetsReady(voiceChangerParams: VoiceChangerParams) -> bool:
    return all(
        os.path.isfile(path) and _sha256(path) == RVC_UPSTREAM_ASSETS[filename]
        for filename, path in _rvc_upstream_asset_paths(voiceChangerParams).items()
    )


def rvcUpstreamAssetsPresent(voiceChangerParams: VoiceChangerParams) -> bool:
    return all(
        os.path.isfile(path)
        for path in _rvc_upstream_asset_paths(voiceChangerParams).values()
    )


def ensureRvcUpstreamAssets(voiceChangerParams: VoiceChangerParams) -> None:
    paths = _rvc_upstream_asset_paths(voiceChangerParams)
    download_params = [
        {
            "url": f"{RVC_UPSTREAM_ASSET_BASE}/{filename}",
            "saveTo": path,
            "position": position,
            "sha256": RVC_UPSTREAM_ASSETS[filename],
        }
        for position, (filename, path) in enumerate(paths.items())
        if not os.path.isfile(path)
        or _sha256(path) != RVC_UPSTREAM_ASSETS[filename]
    ]
    if download_params:
        try:
            with ThreadPoolExecutor(max_workers=len(download_params)) as pool:
                list(pool.map(download, download_params))
        except Exception as exc:
            raise WeightDownladException() from exc
    if not rvcUpstreamAssetsReady(voiceChangerParams):
        raise WeightDownladException()


def downloadWeight(voiceChangerParams: VoiceChangerParams):
    content_vec_500_onnx = voiceChangerParams.content_vec_500_onnx
    hubert_base = voiceChangerParams.hubert_base
    hubert_base_jp = voiceChangerParams.hubert_base_jp
    hubert_soft = voiceChangerParams.hubert_soft
    nsf_hifigan = voiceChangerParams.nsf_hifigan
    crepe_onnx_full = voiceChangerParams.crepe_onnx_full
    crepe_onnx_tiny = voiceChangerParams.crepe_onnx_tiny
    rmvpe = voiceChangerParams.rmvpe
    rmvpe_onnx = voiceChangerParams.rmvpe_onnx
    whisper_tiny = voiceChangerParams.whisper_tiny

    weight_files = [
        content_vec_500_onnx,
        hubert_base,
        hubert_base_jp,
        hubert_soft,
        nsf_hifigan,
        crepe_onnx_full,
        crepe_onnx_tiny,
        rmvpe,
        whisper_tiny,
    ]

    # file exists check (currently only for rvc)
    downloadParams = []
    if os.path.exists(hubert_base) is False:
        downloadParams.append(
            {
                "url": "https://huggingface.co/ddPn08/rvc-webui-models/resolve/main/embeddings/hubert_base.pt",
                "saveTo": hubert_base,
                "position": 0,
            }
        )
    if os.path.exists(hubert_base_jp) is False:
        downloadParams.append(
            {
                "url": "https://huggingface.co/rinna/japanese-hubert-base/resolve/main/fairseq/model.pt",
                "saveTo": hubert_base_jp,
                "position": 1,
            }
        )
    if os.path.exists(hubert_soft) is False:
        downloadParams.append(
            {
                "url": "https://huggingface.co/wok000/weights/resolve/main/ddsp-svc30/embedder/hubert-soft-0d54a1f4.pt",
                "saveTo": hubert_soft,
                "position": 2,
            }
        )
    if os.path.exists(nsf_hifigan) is False:
        downloadParams.append(
            {
                "url": "https://huggingface.co/wok000/weights/resolve/main/ddsp-svc30/nsf_hifigan_20221211/model.bin",
                "saveTo": nsf_hifigan,
                "position": 3,
            }
        )
    nsf_hifigan_config = os.path.join(os.path.dirname(nsf_hifigan), "config.json")

    if os.path.exists(nsf_hifigan_config) is False:
        downloadParams.append(
            {
                "url": "https://huggingface.co/wok000/weights/raw/main/ddsp-svc30/nsf_hifigan_20221211/config.json",
                "saveTo": nsf_hifigan_config,
                "position": 4,
            }
        )
    nsf_hifigan_onnx = os.path.join(os.path.dirname(nsf_hifigan), "nsf_hifigan.onnx")
    if os.path.exists(nsf_hifigan_onnx) is False:
        downloadParams.append(
            {
                "url": "https://huggingface.co/wok000/weights/resolve/main/ddsp-svc30/nsf_hifigan_onnx_20221211/nsf_hifigan.onnx",
                "saveTo": nsf_hifigan_onnx,
                "position": 4,
            }
        )

    if os.path.exists(crepe_onnx_full) is False:
        downloadParams.append(
            {
                "url": "https://huggingface.co/wok000/weights/resolve/main/crepe/onnx/full.onnx",
                "saveTo": crepe_onnx_full,
                "position": 5,
            }
        )
    if os.path.exists(crepe_onnx_tiny) is False:
        downloadParams.append(
            {
                "url": "https://huggingface.co/wok000/weights/resolve/main/crepe/onnx/tiny.onnx",
                "saveTo": crepe_onnx_tiny,
                "position": 6,
            }
        )

    if os.path.exists(content_vec_500_onnx) is False:
        downloadParams.append(
            {
                "url": "https://huggingface.co/wok000/weights_gpl/resolve/main/content-vec/contentvec-f.onnx",
                "saveTo": content_vec_500_onnx,
                "position": 7,
            }
        )
    if os.path.exists(rmvpe) is False:
        downloadParams.append(
            {
                "url": "https://huggingface.co/wok000/weights/resolve/main/rmvpe/rmvpe_20231006.pt",
                "saveTo": rmvpe,
                "position": 8,
            }
        )
    if os.path.exists(rmvpe_onnx) is False:
        downloadParams.append(
            {
                "url": "https://huggingface.co/wok000/weights_gpl/resolve/main/rmvpe/rmvpe_20231006.onnx",
                "saveTo": rmvpe_onnx,
                "position": 9,
            }
        )

    if os.path.exists(whisper_tiny) is False:
        downloadParams.append(
            {
                "url": "https://openaipublic.azureedge.net/main/whisper/models/65147644a518d12f04e32d6f3b26facc3f8dd46e5390956a9424a650c0ce22b9/tiny.pt",
                "saveTo": whisper_tiny,
                "position": 10,
            }
        )

    try:
        with ThreadPoolExecutor() as pool:
            list(pool.map(download, downloadParams))
    except Exception as exc:
        raise WeightDownladException() from exc

    if os.path.exists(hubert_base) is False or os.path.exists(hubert_base_jp) is False or os.path.exists(hubert_soft) is False or os.path.exists(nsf_hifigan) is False or os.path.exists(nsf_hifigan_config) is False:
        raise WeightDownladException()

    # ファイルサイズをログに書き込む。（デバッグ用）
    for weight in weight_files:
        if os.path.exists(weight):
            file_size = os.path.getsize(weight)
            logger.debug(f"weight file [{weight}]: {file_size}")
        else:
            logger.warning(f"weight file is missing. {weight}")
            raise WeightDownladException()
