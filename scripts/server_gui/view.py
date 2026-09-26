"""Fluent presentation layer; process and network work lives in runtime.py."""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget
from qfluentwidgets import (
    BodyLabel, CaptionLabel, CardWidget, ComboBox, FluentIcon, FluentWindow,
    IconWidget, PrimaryPushButton, PushButton, ScrollArea, SpinBox,
    StrongBodyLabel, SubtitleLabel, SwitchButton, TextEdit, TitleLabel,
)


def caption(text, parent=None):
    label = CaptionLabel(text, parent)
    label.setWordWrap(True)
    return label


def card(parent=None):
    widget = CardWidget(parent)
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(24, 22, 24, 22)
    layout.setSpacing(14)
    return widget, layout


class ServerWindowView(FluentWindow):
    """Widgets and layout only, so preview never needs a running server."""

    def __init__(self):
        super().__init__()
        self.setMicaEffectEnabled(False)
        self.setWindowTitle("Voice Changer Server")
        self.setWindowIcon(FluentIcon.MICROPHONE.icon())
        self.resize(1100, 840)
        self.setMinimumSize(900, 720)
        self.navigationInterface.setExpandWidth(190)
        self.dashboard = self._dashboard()
        self.settings_page = self._settings()
        self.addSubInterface(self.dashboard, FluentIcon.HOME, "服务概览")
        self.addSubInterface(self.settings_page, FluentIcon.SETTING, "启动设置")
        self.switchTo(self.dashboard)

    def _page(self, name, title, description):
        scroll = ScrollArea(self)
        scroll.setObjectName(name)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content = QWidget()
        scroll.setWidget(content)
        scroll.enableTransparentBackground()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(18)
        heading = QVBoxLayout()
        heading.setSpacing(6)
        heading.addWidget(TitleLabel(title))
        heading.addWidget(caption(description))
        layout.addLayout(heading)
        return scroll, layout

    def _dashboard(self):
        page, layout = self._page(
            "serverDashboard", "Voice Changer Server",
            "管理本地变声服务。在客户端中选择模型与音频设备。",
        )
        status_card, status_layout = card()
        top = QHBoxLayout()
        icon = IconWidget(FluentIcon.MICROPHONE)
        icon.setFixedSize(34, 34)
        top.addWidget(icon)
        titles = QVBoxLayout()
        titles.setSpacing(5)
        titles.addWidget(caption("服务状态"))
        self.status_title = SubtitleLabel("尚未启动")
        titles.addWidget(self.status_title)
        top.addLayout(titles)
        top.addStretch()
        self.status_badge = StrongBodyLabel("●  待机")
        top.addWidget(self.status_badge)
        status_layout.addLayout(top)
        self.status_detail = BodyLabel("启动服务后，这里将显示连接状态。")
        self.status_detail.setWordWrap(True)
        status_layout.addWidget(self.status_detail)
        actions = QHBoxLayout()
        actions.setSpacing(10)
        self.start_button = PrimaryPushButton(FluentIcon.PLAY, "启动服务")
        self.stop_button = PushButton(FluentIcon.PAUSE, "停止服务")
        self.client_button = PushButton(FluentIcon.LINK, "打开客户端")
        for button in (self.start_button, self.stop_button, self.client_button):
            button.setMinimumHeight(38)
            actions.addWidget(button)
        actions.addStretch()
        status_layout.addLayout(actions)
        layout.addWidget(status_card)

        facts = QHBoxLayout()
        facts.setSpacing(14)
        self.address_value = self._fact(facts, "本机地址", "127.0.0.1:18888", FluentIcon.LINK)
        self.owner_value = self._fact(facts, "服务进程", "未启动", FluentIcon.APPLICATION)
        self.model_value = self._fact(facts, "模型状态", "等待服务", FluentIcon.MUSIC)
        layout.addLayout(facts)

        log_card, log_layout = card()
        log_header = QHBoxLayout()
        log_header.addWidget(StrongBodyLabel("运行日志"))
        log_header.addStretch()
        self.log_note = caption("自动更新 · 最近 240 行")
        log_header.addWidget(self.log_note)
        self.copy_url_button = PushButton(FluentIcon.COPY, "复制地址")
        self.log_folder_button = PushButton(FluentIcon.FOLDER, "日志目录")
        log_header.addWidget(self.copy_url_button)
        log_header.addWidget(self.log_folder_button)
        log_layout.addLayout(log_header)
        self.logs = TextEdit()
        self.logs.setReadOnly(True)
        self.logs.setMinimumHeight(190)
        self.logs.document().setMaximumBlockCount(240)
        self.logs.setPlaceholderText("服务启动后的输出将显示在这里。")
        log_font = QFont("Microsoft YaHei UI", 9)
        self.logs.setFont(log_font)
        log_layout.addWidget(self.logs, 1)
        layout.addWidget(log_card, 1)
        self.tray_hint = caption("关闭或最小化窗口后保留在系统托盘；通过托盘菜单可退出控制台。")
        layout.addWidget(self.tray_hint)
        return page

    def _fact(self, layout, title, value, icon):
        widget, content = card()
        content.setContentsMargins(18, 17, 18, 17)
        content.setSpacing(9)
        row = QHBoxLayout()
        symbol = IconWidget(icon)
        symbol.setFixedSize(16, 16)
        row.addWidget(symbol)
        row.addWidget(caption(title))
        row.addStretch()
        content.addLayout(row)
        label = StrongBodyLabel(value)
        label.setWordWrap(True)
        content.addWidget(label)
        layout.addWidget(widget, 1)
        return label

    def _settings(self):
        page, layout = self._page("serverSettings", "启动设置", "设置在下次启动服务时生效，并自动保存到本机。")
        connection, content = card()
        content.addWidget(SubtitleLabel("连接与启动"))
        self.port_spin = SpinBox()
        self.port_spin.setRange(1, 65535)
        self.port_spin.setValue(18888)
        self.port_spin.setFixedWidth(140)
        self._setting(content, "服务端口", "客户端通过此端口连接本机服务。", self.port_spin)
        self.lan_switch = SwitchButton()
        self._setting(content, "允许局域网连接", "开启后监听所有网卡；仅在可信网络使用。", self.lan_switch)
        self.download_switch = SwitchButton()
        self._setting(content, "跳过启动下载", "使用已准备好的本地依赖与模型资源。", self.download_switch)
        self.client_switch = SwitchButton()
        self._setting(content, "就绪后打开客户端", "本次启动的服务就绪后，自动打开一次客户端。", self.client_switch)
        layout.addWidget(connection)
        appearance, content = card()
        content.addWidget(SubtitleLabel("外观"))
        self.theme_combo = ComboBox()
        self.theme_combo.addItems(["跟随系统", "浅色", "深色"])
        self.theme_combo.setFixedWidth(140)
        self._setting(content, "界面主题", "选择适合当前环境的显示方式。", self.theme_combo)
        layout.addWidget(appearance)
        layout.addWidget(caption("控制台只会停止由它启动的服务。已在其他窗口运行的服务会显示为外部进程。"))
        layout.addStretch()
        return page

    def _setting(self, layout, title, description, control):
        if isinstance(control, SwitchButton):
            control.setOnText("开启")
            control.setOffText("关闭")
        row = QHBoxLayout()
        row.setContentsMargins(0, 10, 0, 10)
        text = QVBoxLayout()
        text.setSpacing(4)
        text.addWidget(StrongBodyLabel(title))
        text.addWidget(caption(description))
        row.addLayout(text, 1)
        row.addSpacing(24)
        row.addWidget(control)
        layout.addLayout(row)
