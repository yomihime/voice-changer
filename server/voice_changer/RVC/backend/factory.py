from voice_changer.RVC.backend.base import RvcBackend, RvcBackendConfig
from voice_changer.RVC.backend.exceptions import RvcBackendConfigError


def create_rvc_backend(kind: str, config: RvcBackendConfig) -> RvcBackend:
    if kind == "legacy":
        from voice_changer.RVC.backend.legacy import LegacyRvcBackend

        return LegacyRvcBackend(config)
    if kind == "official":
        from voice_changer.RVC.backend.upstream import UpstreamRvcBackend

        return UpstreamRvcBackend(config)
    raise RvcBackendConfigError(f"Unknown RVC backend: {kind!r}")
