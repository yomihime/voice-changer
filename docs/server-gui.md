# Voice Changer Server

服务端控制台使用 **PyQt6 + PyQt6-Fluent-Widgets 社区版**（Python 模块名 `qfluentwidgets`）。
它负责管理 Python 变声服务；“打开客户端”会在默认浏览器中打开源项目的兼容页面。
新客户端使用独立的 Tauri 2 打包，目前面向 2.x API，尚未适配此处的旧服务端协议。

## 启动与依赖

双击仓库根目录 `server-gui-windows.bat`。保留的 `scripts/server-gui.ps1` 只负责选择解释器、
检查依赖和转发参数；界面已经完全移至 Python / Qt，没有并行维护的 WinForms 界面。

源码环境缺少 UI 依赖时，入口会安装 `server/requirements/windows-gui.lock` 中校验哈希的固定版本。
这个过程不安装 CUDA 依赖或加载模型；点击“启动服务”才进入已有服务安装与启动流程。
完整安装同时同步 CUDA 与 GUI 两份锁文件；portable 分发包含 GUI 源码、Qt plugins、DLL 和依赖许可证。

```powershell
.venv\Scripts\python.exe scripts/manage.py gui-install
.venv\Scripts\python.exe scripts/server_gui.py
```

## 操作

- 服务概览：服务状态、本机地址、进程归属、模型状态和最近 240 行日志。
- 启动设置：端口、仅本机 / 局域网、跳过权重下载、就绪后打开客户端，以及主题选择。
- 启动/停止：网络和进程操作在后台执行。只有控制台自己创建并核验身份的进程树可以停止。
- 外部服务：可查看状态与打开客户端，不会取得停止权限。
- 托盘：关闭窗口后保留控制台；通过托盘退出。退出正在管理的服务时会请求确认。
- 设置兼容旧 `.runtime/server-gui/settings.json`；日志位于同目录。

## 开发边界与测试

| 文件 | 职责 |
| --- | --- |
| `scripts/server_gui.py` | 可执行入口与启动错误报告 |
| `scripts/server_gui/view.py` | Fluent 组件、布局和展示 |
| `scripts/server_gui/app.py` | Qt 事件、异步操作、托盘与退出 |
| `scripts/server_gui/runtime.py` | 无 Qt 的设置、端点探测、进程身份与日志读取 |

```powershell
.venv\Scripts\python.exe scripts/server_gui.py --self-test
.venv\Scripts\python.exe scripts/server_gui.py --preview .runtime/server-gui-fluent-preview.png
.venv\Scripts\python.exe -m unittest discover -s scripts/tests
```

`--preview` 和 `--self-test` 不创建控制器、托盘或定时器，不探测网络、不加载真实模型、不读写个人设置。
预览中的在线状态是展示样例。真实服务和音频设备需另行测试。

## 依赖来源与许可证

- [PyQt6-Fluent-Widgets 1.11.3](https://pypi.org/project/PyQt6-Fluent-Widgets/1.11.3/)：仅使用社区版。
  [官方项目](https://github.com/zhiyiYo/PyQt-Fluent-Widgets#license)标明 GPLv3，并对商业使用提供单独授权说明；不是 MIT/BSD 依赖。
- [PyQt6](https://www.riverbankcomputing.com/commercial/license-faq)：GPLv3 / 商业授权。
- Qt、Frameless Window、darkdetect、psutil、pywin32 等许可证随安装的依赖保留；
  分发时不能仅以仓库根目录的 MIT LICENSE 代替这些依赖各自的许可。

本次未引入 Pro 组件，也不改变仓库其他源码原有的许可声明。
