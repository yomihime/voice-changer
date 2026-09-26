# 来源与修改

本目录作为本 fork 后续前端开发入口，基于 w-okada/voice-changer 的
`vcclient_win_cuda_2.1.4-alpha.zip` 中实际入口 `dist/main/web_front/index.html`。
压缩包 SHA-256：`58ced135e0768a9f382461fab13a8967520fde2d307d39c0ab4b830040f9c70f`。

`recovered/app.js` 是发布版 `assets/index-D8G8J-aW.js` 格式化后的 JavaScript，
包含 React、MUI 等上游运行库与应用代码。它不是原作者的 TypeScript/TSX 源码。
本 fork 添加平台适配模块、连接提示，并替换 invoke / listen 的平台入口。
`recovered/app.css` 来自 `index-GtP8_cVt.css`；ponyfill 和 public 资源来自同一发布包。
恢复资源集中在 `recovered/`，本 fork 的启动、平台适配和覆盖样式位于 `src/`。
ponyfill 对主 bundle 的相对引用已按恢复后的文件名修正为 `./app.js`。
只保留实际入口所需的一组 JS/CSS，没有将发布包内其他历史构建纳入正式前端。

保留上游版权注释、`licenses-js.json`、`licenses-py.json` 和
`assets/licenses/`。原发布包的样例音频属于 JVNV（CC BY-SA 4.0），不随本仓库分发；保留的署名与原始说明见
`assets/voices/JVNV/readme.md` 及 `readme_JVNV.md`。模型、个人录音、原生 EXE
和 Python 推理程序不属于此目录或桌面前端包。

二进制分析、资源校验清单与历史参考摘录见仓库
`reverse_engineering/v214_native_client/`。那里不再作为日常前端编辑入口。
