# VCClient 2.1.4-alpha 客户端恢复工作区

已恢复可修改的完整前端构建产物，以及原生 EXE 内嵌的连接页、通知页。**未找到对应的原始 TS/TSX、Rust 源码；本目录不是上游完整源码仓库。** 这里的代码、脚本和开发副本与项目现有客户端独立。



## 已确认的来源

分析日期：2026-09-26。

- 用户提供的 EXE：`E:\AI\voice-changer-native-client-win.exe`，12,882,432 字节。
- 在同目录发现官方完整包：`E:\AI\vcclient_win_cuda_2.1.4-alpha.zip`。
- ZIP 的 SHA-256 与[官方 Hugging Face 仓库](https://huggingface.co/wok000/vcclient000/tree/main)的 LFS SHA-256 **完全一致**：`58ced135e0768a9f382461fab13a8967520fde2d307d39c0ab4b830040f9c70f`。
- ZIP 内 `_internal/native_client/voice-changer-native-client.exe` 与用户附件 **逐哈希一致**：`cbd63c440fd1f48356023d141950e62740b10ccac5fbf8f76817b73cca9c2cef`。
- 主界面 `assets/gui_settings/version.txt` 为 `2.1.4-alpha`，edition 为 `cuda`。

证据见 [release-report.json](evidence/release-report.json)、[binary-report.json](evidence/binary-report.json)、[hf-root.json](evidence/hf-root.json)。提取过程没有运行原生 EXE、服务端 EXE，也没有读取或复制已安装程序中的用户设置、模型或运行日志。

## 先从哪里看

| 目标 | 文件/目录 | 性质 |
| --- | --- | --- |
| 改界面逻辑 | [readable/main-ui.js](readable/main-ui.js) | 当前实际加载的完整 JS，已格式化，可编辑 |
| 快速找到组件 | [readable/CODE_INDEX.md](readable/CODE_INDEX.md) | 38 个关键声明、接口和原生调用的行号索引 |
| 单独阅读组件 | [readable/modules](readable/modules) | 从完整 JS 按 AST 摘出的声明；依赖仍在大 bundle 内，不能单独运行 |
| 改整体样式 | [readable/main-ui.css](readable/main-ui.css) | 当前实际加载的 CSS，已格式化 |
| 追加样式实验 | [editable/overrides.css](editable/overrides.css) | 开发副本最后加载的样式，不修改原始提取文件 |
| 改文字、语言、图标 | [web_front/assets](web_front/assets) | 13 种语言、配置、图标和示例音频 |
| 原生连接页/通知页 | [readable/native-client.js](readable/native-client.js) | 从 EXE 解压出的 JS 格式化版本 |
| 重写原生壳时的接口 | [contracts/native-client.d.ts](contracts/native-client.d.ts) | 根据调用点重建的接口说明；不是原始类型定义 |
| 接口兼容性和原生分析 | [ANALYSIS.md](ANALYSIS.md) | 调用链、Rust 边界和迁移建议 |
| 原始提取物 | `extracted/`、`web_front/` | 分别为 EXE 内嵌资产、官方 ZIP 的前端目录 |
| 可运行开发副本 | `dev_front/` | 由构建脚本生成，用于预览和进一步开发 |

`web_front/` 共 93 个文件、73,492,237 字节，包含官方示例音频。`extracted/` 共 3 个文件。较大的可再生目录已在本目录 `.gitignore` 中排除；它们仍在本地磁盘可用。**若要提交长期修改，请把修改整理为独立源码或补丁，不要依赖被忽略的 `readable/main-ui.js` 保存到 Git。** 当前实验可以直接编辑它并构建。

## 二次开发与预览

在仓库根目录 `E:\AI\Dev\voice-changer` 执行。现在已经完成提取和格式化，直接从编辑开始即可。

```powershell
# 编辑 readable/main-ui.js、readable/main-ui.css 或 editable/overrides.css 后：
node reverse_engineering/v214_native_client/scripts/build_dev.mjs

# 只预览界面，不连接服务端：
node reverse_engineering/v214_native_client/scripts/serve.mjs
```

打开 <http://127.0.0.1:21414>。预览已验证可以渲染版本标题、模型列表、设置入口和原版布局。没有服务端时模型列表为空，音频/模型功能不可用；这不是完整变声功能测试。构建后刷新页面即可，未提供 HMR。

如果已有 **2.1.4-alpha** 服务端运行在 `18000`，停止上一个预览进程，再执行：

```powershell
node reverse_engineering/v214_native_client/scripts/serve.mjs --backend http://127.0.0.1:18000
```

该模式通过同源路径转发 REST、Socket.IO 和模型图标请求，界面上的操作会作用于指定服务端。脚本不会自行启动或安装服务端。普通浏览器不具备 Tauri 全局快捷键、原生通知、清理 WebView2 数据等能力；这些要由兼容的原生壳提供。

其他预览模式：

```powershell
# 发布包原始前端（不使用 readable 中的改动）
node reverse_engineering/v214_native_client/scripts/serve.mjs --mode original --port 21415

# EXE 原生连接页；浏览器缺少 IPC，连接时可手动输入服务地址
node reverse_engineering/v214_native_client/scripts/serve.mjs --mode native --port 21416
# 通知页路径：http://127.0.0.1:21416/?mode=notification
```

## 从原文件重新生成

需要 Node.js、Python 3.11+。提取脚本本身只用标准库；格式化和索引用本项目现有 `client/demo/node_modules` 中的 Prettier 和 TypeScript，没有额外安装工具。

以下命令会重新生成提取物、完整可读 JS/CSS、模块摘录及开发副本；**请先另存对这些生成文件的编辑**。`editable/overrides.css` 不会被这些脚本重置。

```powershell
node reverse_engineering/v214_native_client/scripts/extract.mjs "E:\AI\voice-changer-native-client-win.exe"
python reverse_engineering/v214_native_client/scripts/extract_release.py "E:\AI\vcclient_win_cuda_2.1.4-alpha.zip" --verify-archive
node reverse_engineering/v214_native_client/scripts/prepare_readable.mjs
node reverse_engineering/v214_native_client/scripts/index_code.mjs
node reverse_engineering/v214_native_client/scripts/verify.mjs
node reverse_engineering/v214_native_client/scripts/build_dev.mjs
```

`verify.mjs` 校验 96 个原始提取文件的 SHA-256、JSON 可解析性、27 份 JS 的模块语法和当前主入口动态依赖是否存在。它不会执行这些 JS，也不会启动麦克风。修改 `web_front/` 后原始哈希校验失败是预期结果。

## 当前完成度

- 已完成：官方版本匹配、EXE 静态解包、主界面恢复、格式化、38 个声明摘录、接口索引、开发副本构建、浏览器静态预览。
- 尚未恢复：原始 TS/TSX 文件结构、注释、source map、Rust 源码及 Cargo 构建工程。
- 尚未验证：浏览器直接采集麦克风、耳机/虚拟声卡输出、游戏内语音发送、上传流程、Socket.IO 音频流转发、原生全局快捷键和通知。
- 尚未集成：当前 fork 的服务端接口适配。现有 `client/demo`、`client/desktop` 和服务端代码没有被本次分析修改。

依赖许可清单保留在 `web_front/licenses-js.json`、`web_front/licenses-py.json`，原始 notices 也随资产保留。上游公开仓库的许可证不能单凭同名仓库就视为覆盖所有未公开源码的 2.x 构建产物；此处没有重新声明这些提取文件的许可证。
# 后续开发入口

可维护的运行基线现已整理到 [`client/frontend`](../../client/frontend/README.md)，
Electron 启动和打包复用 `client/desktop`。本目录保留取证、提取工具和测试记录；
`readable/modules` 仍是参考摘录，不是构建源码。测试服务已在收尾时关闭。
