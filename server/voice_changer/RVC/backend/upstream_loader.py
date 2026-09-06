import importlib
import importlib.util
import sys
from pathlib import Path
from types import ModuleType

PACKAGE_NAME = "vcclient_official_rvc"


def _vendor_root() -> Path:
    candidates = []
    if hasattr(sys, "_MEIPASS"):
        candidates.append(Path(sys._MEIPASS) / "third_party" / "rvc")
    candidates.append(Path(__file__).resolve().parents[4] / "third_party" / "rvc")
    for candidate in candidates:
        if (candidate / "infer" / "rtrvc.py").is_file():
            return candidate
    raise FileNotFoundError(
        "Vendored official RVC runtime was not found in third_party/rvc"
    )


def load_upstream_module(module: str) -> ModuleType:
    if PACKAGE_NAME not in sys.modules:
        root = _vendor_root()
        spec = importlib.util.spec_from_file_location(
            PACKAGE_NAME,
            root / "__init__.py",
            submodule_search_locations=[str(root)],
        )
        if spec is None or spec.loader is None:
            raise ImportError(f"Unable to load vendored RVC package from {root}")
        package = importlib.util.module_from_spec(spec)
        sys.modules[PACKAGE_NAME] = package
        spec.loader.exec_module(package)
    return importlib.import_module(f"{PACKAGE_NAME}.{module}")
