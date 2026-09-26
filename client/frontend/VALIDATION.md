# 收尾验证（2026-09-27）

- Node 24.20.0：前端构建及 JavaScript 语法检查通过。
- Node tests：10 项通过，覆盖桌面参数/权限、平台适配、静态资源、HTTP multipart
  上传代理、来源隔离、离线响应、WebSocket 转发与连接清理。
- Python tests：`test_desktop.py` 5 项、`test_manage.py` 11 项通过。
- 已打包 Electron 44.2.0：真实新前端隐藏窗口渲染成功；无后端时提示正确；
  不依赖 Tauri，渲染进程无 Node 权限；未采集麦克风。
- 原桌面入口集成回归通过：媒体拒绝、外链限制、文件上传、刷新持久化、
  单实例激活及窗口等待退出。没有播放或录制音频。
- 早期含示例音频的便携 ZIP 校验通过；代码提交精简后需重新打包，旧包统计不再代表当前源码。
- 收尾确认：18000、18888、21414、21415、21416 均无监听；测试 Electron 已退出。

本机生成证据位于忽略的 `.runtime/frontend-smoke/`、`.runtime/desktop-smoke/`；
源码测试位于本目录 `tests/`、`client/desktop/tests/`、`scripts/tests/`。
个人模型测试资料仅保留在本地，不属于源码提交。

新前端对现有旧版后端的协议适配、Electron 全局快捷键和浮窗仍待实现。
