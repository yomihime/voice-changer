"""Qt-free control of the server launched by Voice Changer Server.

An endpoint is observable, not owned. Only processes created by this controller
may be stopped. No model, audio library, or server module is imported here.
"""

from __future__ import annotations

from dataclasses import dataclass
import http.client
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import threading


@dataclass(frozen=True)
class Settings:
    port: int = 18888
    bind_lan: bool = False
    skip_downloads: bool = False
    open_client: bool = True

    def __post_init__(self):
        if type(self.port) is not int or not 1 <= self.port <= 65535:
            raise ValueError("端口必须介于 1 和 65535 之间。")


def read_settings(root: Path) -> Settings:
    """Read both the old PowerShell UTF-8 BOM file and new Python preferences."""
    try:
        saved = json.loads((Path(root) / ".runtime/server-gui/settings.json").read_text(encoding="utf-8-sig"))
        if not isinstance(saved, dict):
            return Settings()
        defaults = Settings()
        port = saved.get("port", defaults.port)
        if type(port) is not int or not 1 <= port <= 65535:
            port = defaults.port
        values = {}
        for field, key in (("bind_lan", "bindLan"), ("skip_downloads", "skipDownloads"), ("open_client", "openClient")):
            value = saved.get(key, getattr(defaults, field))
            values[field] = value if type(value) is bool else getattr(defaults, field)
        return Settings(port=port, **values)
    except (OSError, ValueError):
        return Settings()


def save_settings(root: Path, settings: Settings) -> None:
    path = Path(root) / ".runtime/server-gui/settings.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
            json.dump({"port": settings.port, "bindLan": settings.bind_lan,
                       "skipDownloads": settings.skip_downloads,
                       "openClient": settings.open_client}, stream, indent=2)
            stream.write("\n")
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


@dataclass(frozen=True)
class EndpointState:
    kind: str
    port: int
    model_ready: bool = False
    error: str = ""

    @property
    def ready(self) -> bool:
        # Preserve the existing launcher's internal state names during migration.
        return self.kind in ("VCClientNoModel", "VCClientReady")

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.port}/"


def _is_server_info(info: object) -> bool:
    if not isinstance(info, dict) or info.get("status") != "OK":
        return False
    if not isinstance(info.get("python"), str) or not info["python"].strip():
        return False
    if not all(isinstance(info.get(key), list) for key in ("modelSlots", "sampleModels", "gpus")):
        return False
    params = info.get("voiceChangerParams")
    if not isinstance(params, dict) or not all(key in params for key in ("model_dir", "sample_mode", "allow_downloads")):
        return False
    try:
        int(info["serverAudioStated"])
    except (KeyError, ValueError, TypeError, OverflowError):
        return False
    return True


def _tcp_open(port: int, timeout: float) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=timeout):
            return True
    except OSError:
        return False


def probe_endpoint(port: int, timeout: float = 1.0) -> EndpointState:
    Settings(port=port)
    if timeout <= 0:
        raise ValueError("timeout must be positive")
    # http.client neither follows redirects nor consults proxy environment vars.
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=timeout)
    try:
        connection.request("GET", "/info", headers={"Accept": "application/json"})
        response = connection.getresponse()
        if response.status != 200:
            return EndpointState("ForeignHttp", port, error=f"/info returned HTTP {response.status}")
        body = response.read(2 * 1024 * 1024 + 1)
        if len(body) > 2 * 1024 * 1024:
            return EndpointState("InvalidHttp", port, error="/info response exceeds 2 MiB")
        try:
            info = json.loads(body)
        except (ValueError, UnicodeError):
            return EndpointState("InvalidHttp", port, error="/info is not valid JSON")
        if not _is_server_info(info):
            return EndpointState("ForeignHttp", port, error="/info is not a Voice Changer Server response")
        pipeline = info.get("pipelineInfo")
        ready = isinstance(pipeline, dict) and pipeline.get("ready") is True
        return EndpointState("VCClientReady" if ready else "VCClientNoModel", port, ready)
    except (OSError, http.client.HTTPException) as error:
        occupied = _tcp_open(port, min(timeout, 0.25))
        kind = ("HttpTimeout" if isinstance(error, TimeoutError) else "TcpOnly") if occupied else "Closed"
        return EndpointState(kind, port, error=str(error))
    finally:
        connection.close()


def _process_library():
    try:
        import psutil
    except ImportError as error:
        raise RuntimeError("缺少启动器依赖 psutil，请重新安装 Windows GUI 依赖。") from error
    return psutil


def _stop_tree(owner, psutil) -> None:
    """Freeze each verified parent before enumerating its children.

    psutil guards suspend/kill against PID reuse with creation-time identities.
    Freezing before traversal prevents a live parent spawning after the snapshot.
    Any process that survives a failed stop is resumed before returning an error.
    """
    frozen = []
    seen = set()

    def freeze(process):
        try:
            identity = (process.pid, process.create_time())
            if identity in seen:
                return
            seen.add(identity)
            process.suspend()
            frozen.append(process)
            for child in process.children():
                freeze(child)
        except psutil.NoSuchProcess:
            return

    try:
        freeze(owner)
        for process in reversed(frozen):
            try:
                process.kill()
            except psutil.NoSuchProcess:
                pass
        _, alive = psutil.wait_procs(frozen, timeout=10)
        if alive:
            raise RuntimeError("服务进程未能完全停止，请检查日志并重试。")
    finally:
        original_error = sys.exception()
        resume_errors = []
        for process in frozen:
            try:
                process.resume()
            except psutil.NoSuchProcess:
                pass
            except Exception as error:
                # A failure for one survivor must not strand the remaining tree.
                resume_errors.append(f"PID {process.pid}: {error}")
        if resume_errors:
            detail = "部分服务进程无法恢复运行：" + "; ".join(resume_errors)
            if original_error is not None:
                original_error.add_note(detail)
            else:
                raise RuntimeError(detail)


class ServerController:
    def __init__(self, root: Path):
        self.root = Path(root).resolve()
        self.runtime_directory = self.root / ".runtime/server-gui"
        self._mutation_lock = threading.Lock()
        self._state_lock = threading.Lock()
        self._process = None
        self._owner = None

    @property
    def running(self) -> bool:
        with self._state_lock:
            process = self._process
        return process is not None and process.poll() is None

    @property
    def exit_code(self) -> int | None:
        with self._state_lock:
            process = self._process
        return process.poll() if process is not None else None

    def start(self, settings: Settings) -> EndpointState:
        with self._mutation_lock:
            if self.running:
                raise RuntimeError("当前控制台已经启动了服务，请先停止它。")
            state = probe_endpoint(settings.port)
            if state.ready:
                return state
            if state.kind != "Closed":
                raise RuntimeError(f"端口 {settings.port} 已被占用或没有响应，请更换端口。")
            psutil = _process_library()
            script = self.root / "scripts/windows.ps1"
            if not script.is_file():
                raise FileNotFoundError(script)
            save_settings(self.root, settings)
            powershell = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32/WindowsPowerShell/v1.0/powershell.exe"
            command = [str(powershell), "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script),
                       "-Action", "start", "--", "-p", str(settings.port), "--host",
                       "0.0.0.0" if settings.bind_lan else "127.0.0.1"]
            if settings.skip_downloads:
                command.append("--skip-downloads")
            environment = os.environ.copy()
            environment.update(PYTHONUTF8="1", PYTHONUNBUFFERED="1")
            with (self.runtime_directory / "server.stdout.log").open("wb") as stdout, \
                    (self.runtime_directory / "server.stderr.log").open("wb") as stderr:
                process = subprocess.Popen(command, cwd=self.root, env=environment, stdin=subprocess.DEVNULL,
                                           stdout=stdout, stderr=stderr,
                                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            try:
                owner = psutil.Process(process.pid)
                owner.create_time()  # Cache identity while the process is known to be ours.
            except psutil.NoSuchProcess:
                process.wait(timeout=1)
                raise RuntimeError(f"服务启动后立即退出，代码 {process.returncode}。") from None
            with self._state_lock:
                self._process, self._owner = process, owner
            return EndpointState("Starting", settings.port)

    def stop(self) -> bool:
        with self._mutation_lock:
            with self._state_lock:
                process, owner = self._process, self._owner
            if process is None or owner is None:
                return False
            if process.poll() is None:
                _stop_tree(owner, _process_library())
                process.wait(timeout=10)
            with self._state_lock:
                self._process = self._owner = None
            return True

    def open_client(self, port: int):
        state = probe_endpoint(port)
        if not state.ready:
            raise RuntimeError("Voice Changer Server 尚未就绪，无法打开客户端。")
        desktop = self.root / ".runtime/desktop/vcclient-desktop.exe"
        if not desktop.is_file():
            raise FileNotFoundError("桌面客户端尚未构建，请运行 python scripts/desktop.py build。")
        return subprocess.Popen([str(desktop), "--url", state.url], cwd=desktop.parent)

    def read_logs(self, max_lines: int = 240) -> str:
        if max_lines < 1:
            return ""
        sections = []
        for name in ("server.stdout.log", "server.stderr.log"):
            try:
                with (self.runtime_directory / name).open("rb") as stream:
                    stream.seek(0, os.SEEK_END)
                    size = stream.tell()
                    # Bound work even when a server has been running for days.
                    stream.seek(max(0, size - 128 * 1024))
                    lines = stream.read().decode("utf-8-sig", errors="replace").splitlines()
                if lines:
                    sections.append(f"[{name}]\n" + "\n".join(lines[-max_lines:]))
            except OSError:
                continue
        return "\n\n".join(sections)
