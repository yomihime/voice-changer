# 新前端（2.1.4-alpha 基线）

后续前端开发从本目录开始。所有运行所需的界面源码、翻译与图标
均在仓库中，不依赖本机 E:\AI 下的 EXE、安装包或逆向生成目录。
这是可编辑的发布版 JavaScript 恢复基线，尚未恢复原始 TSX 工程，详见 [NOTICE](NOTICE.md)。

## 开发

需要仓库规定的 Node 24.20+（24.x），无需 npm install。

```powershell
npm --prefix client/frontend run dev -- --backend http://127.0.0.1:18000/
```

页面位于 http://127.0.0.1:21416/。修改后重新执行 build 并刷新页面。
纯界面开发可省略 backend；界面会提示未连接。停止终端即释放预览服务。

| 文件 | 用途 |
| --- | --- |
| `src/app.js` | 可执行的恢复代码；保留具名组件、状态 hooks、REST 客户端，可按名称搜索 |
| `src/app.css`、`src/overrides.css` | 原始样式与本 fork 样式 |
| `src/desktop-adapter.js` | 平台命令适配，避免浏览器 / Electron 调用不存在的 Tauri API |
| `src/connection-status.js` | 2.x API 连接提示 |
| `public/` | 翻译、图标、许可证 |
| `server.cjs` | 浏览器开发和 Electron 共用的静态服务及同源 HTTP/WebSocket 代理 |
| `build.cjs` | 零依赖构建与 JS 语法检查；`dist/` 是忽略的生成物 |

具名组件和客户端类的位置见 [代码导航](CODE_INDEX.md)。
今后应逐步把应用组件从恢复代码抽成独立模块；不要编辑逆向目录中的参考摘录，
它们没有完整依赖，也不会进入构建。

## Electron 启动和打包

复用 `client/desktop`。仓库根目录执行：

```powershell
.\build-frontend-windows.bat
.\start-frontend-windows.bat --backend http://127.0.0.1:18000/
```

双击桌面 EXE 或无参数启动默认使用新前端，后端地址为 `127.0.0.1:18000`。
前端服务由 Electron 管理，窗口退出后关闭；占用端口 21416 时会明确报错。
后端需要单独启动，关闭前端不会结束外部推理服务。
原有 `start-client-windows.bat` 仍通过 `--url` 打开旧后端自带界面。

输出是 `.runtime/desktop/` 和 `dist/vcclient-desktop-win-x64.zip`。
分发时保留完整目录，不能只复制 EXE；包含前端、固定版本 Electron 及许可证，
不包含 Python 后端和模型。同名 ZIP 已存在时不会覆盖，可传
`--output dist/自定义名字.zip`。打包只需 Python 标准库，首次需下载校验过的 Electron。
此入口采用 Electron 官方支持的 [resources/app 目录打包方式](https://www.electronjs.org/docs/latest/tutorial/application-distribution)。

```powershell
node --test client/frontend/tests/*.test.cjs client/desktop/tests/*.test.cjs
python -m unittest discover -s scripts/tests -p test_desktop.py
python scripts/desktop.py verify
```

## 当前边界

- 必须连接兼容 2.1.4 的 `/api/...` 后端；仓库目前 `/info`、`/update_settings`
  后端尚未适配，不能仅替换页面就认为整套迁移完成。
- 麦克风沿用 Electron 的授权与隔离策略；浏览器模式依赖浏览器自身权限。
- 全局快捷键与 Tauri 浮窗尚未移植，设置默认关闭，不会伪装成注册成功。
- 清除界面缓存会清除 Web Storage / Cache Storage 并重载界面，不会停止独立后端。
- 本次收尾不自动启动服务、采集麦克风或加载个人模型。

官方示例音频不是变声必需项，默认样例列表为空。个人模型、截图、推理输出与麦克风测试资料不纳入版本管理。
