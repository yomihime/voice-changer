class RvcBackendError(RuntimeError):
    """Base error exposed by the VCClient-to-RVC backend boundary."""


class RvcBackendConfigError(RvcBackendError):
    pass


class RvcModelLoadError(RvcBackendError):
    pass


class RvcIndexLoadError(RvcBackendError):
    pass


class RvcDeviceError(RvcBackendError):
    pass


class RvcInferenceError(RvcBackendError):
    pass


class RvcCudaGraphError(RvcBackendError):
    pass
