"""Qt event loop, asynchronous control actions and tray lifecycle."""

import argparse
import os
from pathlib import Path
import sys

from PyQt6.QtCore import QEvent, QObject, QRunnable, QThreadPool, QTimer, Qt, QUrl, pyqtSignal
from PyQt6.QtGui import QAction, QCloseEvent, QDesktopServices, QFont, QFontDatabase
from PyQt6.QtWidgets import QApplication, QMenu, QSystemTrayIcon
from qfluentwidgets import InfoBar, InfoBarPosition, MessageBox, Theme, setTheme, setThemeColor

from .runtime import Settings, ServerController, probe_endpoint, read_settings, save_settings
from .view import ServerWindowView


class _Signals(QObject):
    result = pyqtSignal(object)
    error = pyqtSignal(str)
    finished = pyqtSignal()


class _Task(QRunnable):
    def __init__(self, action):
        super().__init__()
        self.action = action
        self.signals = _Signals()

    def run(self):
        try:
            self.signals.result.emit(self.action())
        except Exception as exc:
            self.signals.error.emit("\n".join([str(exc), *getattr(exc, "__notes__", [])]))
        finally:
            self.signals.finished.emit()


class ServerWindow(ServerWindowView):
    def __init__(self, root, *, preview=False):
        super().__init__()
        self.root = Path(root)
        self.preview = preview
        self.controller = None if preview else ServerController(self.root)
        self.settings = Settings() if preview else read_settings(self.root)
        self._workers = set()
        self._operation = None
        self._probing = False
        self._quitting = False
        self._allow_close = False
        self._auto_open = False
        self._ready = False
        self._state_epoch = 0
        self._last_logs = None
        self.tray = None
        self.tray_actions = {}
        self.refresh_timer = None
        self.port_spin.setValue(self.settings.port)
        self.address_value.setText(f"127.0.0.1:{self.settings.port}")
        self.lan_switch.setChecked(self.settings.bind_lan)
        self.download_switch.setChecked(self.settings.skip_downloads)
        self.client_switch.setChecked(self.settings.open_client)
        self.theme_combo.currentIndexChanged.connect(
            lambda index: setTheme((Theme.AUTO, Theme.LIGHT, Theme.DARK)[index])
        )
        if preview:
            self.status_title.setText("服务已就绪")
            self.status_badge.setText("●  在线")
            self.status_badge.setTextColor("#138468", "#65d6b6")
            self.status_detail.setText("本机服务连接正常。打开客户端，选择模型与音频设备后即可开始变声。")
            self.owner_value.setText("由控制台管理")
            self.model_value.setText("等待选择模型")
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(False)
            self.client_button.setEnabled(False)
            self.copy_url_button.setEnabled(False)
            self.log_folder_button.setEnabled(False)
            self.logs.setPlainText(
                "[预览] Voice Changer Server\n"
                "[预览] 服务地址  http://127.0.0.1:18888\n"
                "[预览] 服务状态  已就绪\n"
                "[预览] 等待在客户端中选择模型与音频设备。\n\n"
                "此画面为界面预览，未启动服务、网络探测或音频设备。"
            )
            return
        self.start_button.clicked.connect(self.start_server)
        self.stop_button.clicked.connect(self.stop_server)
        self.client_button.clicked.connect(self.open_client)
        self.copy_url_button.clicked.connect(self.copy_url)
        self.log_folder_button.clicked.connect(self.open_log_folder)
        self.port_spin.valueChanged.connect(self._settings_changed)
        for switch in (self.lan_switch, self.download_switch, self.client_switch):
            switch.checkedChanged.connect(self._settings_changed)
        self._create_tray()
        self._update_controls()
        self.refresh_timer = QTimer(self)
        self.refresh_timer.setInterval(1800)
        self.refresh_timer.timeout.connect(self.refresh)
        self.refresh_timer.start()
        QTimer.singleShot(0, self.refresh)

    def _settings_changed(self, *_):
        self._state_epoch += 1
        self.settings = Settings(
            port=self.port_spin.value(), bind_lan=self.lan_switch.isChecked(),
            skip_downloads=self.download_switch.isChecked(),
            open_client=self.client_switch.isChecked(),
        )
        self.address_value.setText(f"127.0.0.1:{self.settings.port}")
        try:
            save_settings(self.root, self.settings)
        except Exception as exc:
            self._notify("无法保存设置", str(exc))
        self._ready = False
        self._update_controls()
        self.refresh()

    def _submit(self, action, callback, *, operation=None):
        if operation:
            self._operation = operation
            self._update_controls()
        task = _Task(action)
        self._workers.add(task)

        def result(value):
            if operation:
                self._operation = None
            if not self._quitting:
                callback(value)
                self._update_controls()

        def failed(message):
            if operation:
                self._operation = None
                self._auto_open = False
            if self._quitting:
                self._quitting = False
                if self.refresh_timer:
                    self.refresh_timer.start()
                self._show_window()
            if not self._quitting:
                self.status_title.setText("操作未完成")
                self.status_detail.setText(message)
                self._notify("操作未完成", message)
                self._update_controls()

        def finished():
            self._workers.discard(task)
            if self._quitting and not self._workers:
                self._finish_quit()

        task.signals.result.connect(result)
        task.signals.error.connect(failed)
        task.signals.finished.connect(finished)
        QThreadPool.globalInstance().start(task)
        return task

    def refresh(self):
        if self.preview or self._quitting or self._probing or self._operation:
            return
        self._probing = True
        port = self.settings.port
        epoch = self._state_epoch

        def read():
            return probe_endpoint(port, timeout=1.0), self.controller.read_logs(max_lines=240)

        def apply(result):
            if epoch != self._state_epoch or self._operation:
                return
            state, logs = result
            self._show_state(state)
            if logs != self._last_logs:
                bar = self.logs.verticalScrollBar()
                at_bottom = bar.value() >= bar.maximum() - 4
                previous = bar.value()
                self.logs.setPlainText(logs)
                bar.setValue(bar.maximum() if at_bottom else previous)
                self._last_logs = logs

        task = self._submit(read, apply)
        # Only one probe is allowed in flight, including when a port is edited.
        task.signals.finished.connect(self._probe_finished)

    def _probe_finished(self):
        self._probing = False

    def _show_state(self, state):
        self._ready = state.ready
        owned = self.controller.running
        self.address_value.setText(f"127.0.0.1:{state.port}")
        self.owner_value.setText("由控制台管理" if owned else "外部进程" if state.ready else "未启动")
        self.model_value.setText("模型已加载" if state.model_ready else "等待选择模型" if state.ready else "等待服务")
        if state.ready:
            self.status_title.setText("服务已就绪")
            self.status_badge.setText("●  在线")
            self.status_badge.setTextColor("#138468", "#65d6b6")
            self.status_detail.setText(
                "连接正常。在客户端中选择模型与音频设备后即可开始变声。" if owned else
                "检测到已运行的变声服务。可以打开客户端；此控制台不会停止外部进程。"
            )
        elif owned:
            self.status_title.setText("正在启动服务")
            self.status_badge.setText("●  启动中")
            self.status_badge.setTextColor("#9c690c", "#efc070")
            self.status_detail.setText("正在等待服务就绪，首次启动可能需要准备依赖资源。")
        elif state.kind == "Closed":
            exit_code = self.controller.exit_code
            failed = isinstance(exit_code, int) and exit_code != 0
            self.status_title.setText(f"服务已退出 · 代码 {exit_code}" if failed else "尚未启动")
            self.status_badge.setText("●  已退出" if failed else "●  待机")
            self.status_badge.setTextColor("#ba4427" if failed else "#5c6675", "#f0997f" if failed else "#bdc5cf")
            self.status_detail.setText("服务异常退出，请查看下方日志后重新启动。" if failed else
                                       "启动本地服务，然后打开客户端开始使用。")
        else:
            self.status_title.setText("连接需要检查")
            self.status_badge.setText("●  无法连接")
            self.status_badge.setTextColor("#ba4427", "#f0997f")
            self.status_detail.setText(state.error or "此端口没有返回可识别的变声服务信息，请检查日志或更换端口。")
        self._update_controls()
        if self._auto_open and state.ready:
            self._auto_open = False
            self.open_client()

    def _update_controls(self):
        owned = bool(self.controller and self.controller.running)
        idle = self._operation is None and not self._quitting
        self.start_button.setEnabled(idle and not owned and not self._ready)
        self.stop_button.setEnabled(idle and owned)
        self.client_button.setEnabled(idle and self._ready)
        for name, button in (("start", self.start_button), ("stop", self.stop_button), ("client", self.client_button)):
            if name in self.tray_actions:
                self.tray_actions[name].setEnabled(button.isEnabled())
        self.start_button.setText("正在启动…" if self._operation == "start" else "启动服务")
        self.stop_button.setText("正在停止…" if self._operation == "stop" else "停止服务")
        for control in (self.port_spin, self.lan_switch, self.download_switch, self.client_switch):
            control.setEnabled(idle and not owned)

    def start_server(self):
        if self._operation or self._quitting or self.controller.running:
            return
        self._state_epoch += 1
        settings = self.settings
        self._auto_open = settings.open_client
        self.status_title.setText("正在启动服务")
        self.status_detail.setText("正在准备运行环境，请稍候。")
        self._submit(lambda: self.controller.start(settings), self._show_state, operation="start")

    def stop_server(self):
        if self._operation or self._quitting or not self.controller.running:
            return
        self._state_epoch += 1
        self._auto_open = False
        self._submit(self.controller.stop, lambda _: self.refresh(), operation="stop")

    def open_client(self):
        if self._operation or self._quitting or not self._ready:
            return
        port = self.settings.port
        self._submit(lambda: self.controller.open_client(port), lambda _: None, operation="client")

    def _notify(self, title, message):
        InfoBar.error(title=title, content=message, orient=Qt.Orientation.Horizontal, isClosable=True,
                      position=InfoBarPosition.TOP, duration=7000, parent=self)

    def copy_url(self):
        QApplication.clipboard().setText(f"http://127.0.0.1:{self.settings.port}/")
        InfoBar.success(title="地址已复制", content=f"http://127.0.0.1:{self.settings.port}/",
                        position=InfoBarPosition.TOP, duration=2000, parent=self)

    def open_log_folder(self):
        folder = self.root / ".runtime" / "server-gui"
        try:
            folder.mkdir(parents=True, exist_ok=True)
            if not QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder))):
                self._notify("无法打开日志目录", str(folder))
        except OSError as exc:
            self._notify("无法打开日志目录", str(exc))

    def _create_tray(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_hint.setText("当前环境没有系统托盘。关闭窗口时将退出控制台。")
            return
        self.tray = QSystemTrayIcon(self.windowIcon(), self)
        self.tray.setToolTip("Voice Changer Server")
        menu = QMenu(self)
        show_action = QAction("显示 Voice Changer Server", menu)
        show_action.triggered.connect(self._show_window)
        menu.addAction(show_action)
        menu.addSeparator()
        for name, text, handler in (("start", "启动服务", self.start_server),
                                    ("stop", "停止服务", self.stop_server),
                                    ("client", "打开客户端", self.open_client)):
            action = QAction(text, menu)
            action.triggered.connect(handler)
            menu.addAction(action)
            self.tray_actions[name] = action
        menu.addSeparator()
        exit_action = QAction("退出控制台", menu)
        exit_action.triggered.connect(self.request_exit)
        menu.addAction(exit_action)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(
            lambda reason: self._show_window() if reason in (
                QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick
            ) else None
        )
        self.tray.show()

    def _show_window(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def request_exit(self):
        if self._quitting:
            return
        if self._operation:
            self._show_window()
            self._notify("请稍候", "当前操作尚未完成，请完成后再退出控制台。")
            return
        if self.controller and self.controller.running:
            self._show_window()
            dialog = MessageBox("退出 Voice Changer Server", "退出时将停止由此控制台启动的服务。确定退出？", self)
            dialog.yesButton.setText("停止服务并退出")
            dialog.cancelButton.setText("取消")
            if not dialog.exec():
                return
        self._quitting = True
        if self.refresh_timer:
            self.refresh_timer.stop()
        self._update_controls()
        if self.controller and self.controller.running:
            # Keep the Qt event loop alive until process cleanup and pending probes finish.
            self._submit(self.controller.stop, lambda _: None)
        elif not self._workers:
            self._finish_quit()

    def _finish_quit(self):
        self._allow_close = True
        if self.tray:
            self.tray.hide()
        self.close()
        QApplication.instance().quit()

    def closeEvent(self, event: QCloseEvent):
        if self._allow_close or self.preview:
            event.accept()
        elif self.tray and self.tray.isVisible():
            self.hide()
            event.ignore()
        else:
            event.ignore()
            self.request_exit()

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QEvent.Type.WindowStateChange and self.isMinimized() and getattr(self, "tray", None):
            QTimer.singleShot(0, self.hide)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Voice Changer Server control panel")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--preview", type=Path, metavar="PNG", help="Render an offline preview without server or settings access")
    parser.add_argument("--self-test", action="store_true", help="Build and check the widgets without server or settings access")
    args = parser.parse_args(argv)
    offline = bool(args.preview or args.self_test)
    if offline:
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
    app = QApplication.instance() or QApplication(sys.argv[:1])
    if offline and sys.platform == "win32":
        # Windows' offscreen Qt plugin does not discover system fonts by itself.
        fonts = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
        for name in ("segoeui.ttf", "segoeuib.ttf", "msyh.ttc", "msyhbd.ttc"):
            QFontDatabase.addApplicationFont(str(fonts / name))
    app.setFont(QFont("Microsoft YaHei UI", 10))
    app.setApplicationName("Voice Changer Server")
    app.setOrganizationName("Voice Changer")
    setTheme(Theme.LIGHT if offline else Theme.AUTO)
    setThemeColor("#3478d4")
    window = ServerWindow(args.root, preview=offline)
    window.show()
    if offline:
        app.processEvents()
        assert window.windowTitle() == "Voice Changer Server"
        assert window.controller is None and window.tray is None and window.refresh_timer is None
        assert window.logs.document().maximumBlockCount() == 240
        window.resize(window.minimumSize())
        app.processEvents()
        assert window.start_button.isVisible() and window.logs.isVisible()
        window.resize(1100, 840)
        app.processEvents()
        if args.preview:
            args.preview.parent.mkdir(parents=True, exist_ok=True)
            if not window.grab().save(str(args.preview)):
                raise RuntimeError(f"Could not save preview to {args.preview}")
            print(f"Preview saved: {args.preview}")
        print("Voice Changer Server UI self-test passed (offline).")
        window.close()
        return 0
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
