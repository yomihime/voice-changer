import requests  # type: ignore
import os
import hashlib
from tqdm import tqdm

from mods.log_control import VoiceChangaerLogger

logger = VoiceChangaerLogger.get_instance().getLogger()


def download(params):
    url = params["url"]
    saveTo = params["saveTo"]
    position = params["position"]
    expected_sha256 = params.get("sha256")
    timeout = params.get("timeout", (10, 120))
    dirname = os.path.dirname(saveTo)
    if dirname != "":
        os.makedirs(dirname, exist_ok=True)
    temporary = f"{saveTo}.part"
    progress_bar = None

    try:
        with requests.get(
            url,
            stream=True,
            allow_redirects=True,
            timeout=timeout,
        ) as req:
            req.raise_for_status()
            content_length = req.headers.get("content-length")
            progress_bar = tqdm(
                total=int(content_length) if content_length is not None else None,
                leave=False,
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
                position=position,
            )

            digest = hashlib.sha256()
            with open(temporary, "wb") as f:
                for chunk in req.iter_content(chunk_size=1024):
                    if chunk:
                        progress_bar.update(len(chunk))
                        digest.update(chunk)
                        f.write(chunk)
        if expected_sha256 and digest.hexdigest() != expected_sha256:
            raise ValueError(f"SHA-256 mismatch for {url}")
        os.replace(temporary, saveTo)

    except Exception as e:
        logger.warning(e)
        if os.path.exists(temporary):
            os.remove(temporary)
        raise
    finally:
        if progress_bar is not None:
            progress_bar.close()


def download_no_tqdm(params):
    url = params["url"]
    saveTo = params["saveTo"]
    dirname = os.path.dirname(saveTo)
    if dirname != "":
        os.makedirs(dirname, exist_ok=True)
    try:
        req = requests.get(url, stream=True, allow_redirects=True)
        with open(saveTo, "wb") as f:
            countToDot = 0
            for chunk in req.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
                    countToDot += 1
                    if countToDot % 1024 == 0:
                        print(".", end="", flush=True)

        logger.info(f"[Voice Changer] download sample catalog. {saveTo}")
    except Exception as e:
        logger.warning(e)
