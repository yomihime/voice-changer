"""Voice Changer Server's PyQt6 / qfluentwidgets entry point."""
from pathlib import Path
import sys
import traceback


if __name__ == "__main__":
    try:
        from server_gui.app import main
        sys.exit(main())
    except Exception:
        directory = Path(__file__).resolve().parents[1] / ".runtime/server-gui"
        directory.mkdir(parents=True, exist_ok=True)
        report = traceback.format_exc()
        (directory / "gui-error.log").write_text(report, encoding="utf-8")
        if sys.stderr:
            print(report, file=sys.stderr)
        if sys.platform == "win32" and not any(arg in sys.argv for arg in ("--preview", "--self-test")):
            import ctypes
            ctypes.windll.user32.MessageBoxW(None, f"无法打开服务控制台。详情：\n{directory / 'gui-error.log'}",
                                            "Voice Changer Server", 0x10)
        sys.exit(1)
