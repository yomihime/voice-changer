# 来源检索与逆向分析

## 源码检索结论

在本次检查范围内没有找到能直接构建附件的原生客户端源码。

| 已检查来源 | 结果 |
| --- | --- |
| [upstream/master](https://github.com/w-okada/voice-changer/tree/f1caf8e7c39fd0d6866202be27bf142790191a51) | 749 个树项；未发现匹配的 Tauri/Cargo 原生项目 |
| [upstream/dev](https://github.com/w-okada/voice-changer/tree/be1dbf2feaa968588dfc6e2f4992fd149675d9c7) | 1062 个树项；未发现匹配的 Tauri/Cargo 原生项目 |
| [upstream/v.2](https://github.com/w-okada/voice-changer/tree/bec5bd04d1ba081dd3c60b274de3f9132d443d17) | 38 个树项，主要是文档、许可证、教程、notebook；没有客户端源代码 |
| GitHub branches/tags API | 存在 v.2 分支，但未列出 2.1.4-alpha 标签 |
| w-okada 公开仓库第一页（100 项） | 未找到明确对应的 vcclient-native-client 仓库；没有据此断言其他所有仓库都不存在源码 |
| [Issue #1521](https://github.com/w-okada/voice-changer/issues/1521) | 用户同样询问 2.x 源码；当前评论没有提供源码链接。这是辅助线索，不是维护者闭源声明 |
| [Hugging Face 发布目录](https://huggingface.co/wok000/vcclient000/tree/main) | 有 2.1.4-alpha 的 Windows CUDA、DML、Mac 发行包 |

API 结果保存在 `evidence/`，其中树结果 `truncated=false`。结论是“尚未找到公开源码”，不是“证明所有 2.x 源码永久不公开”。

## 实际结构

```text
voice-changer-native-client-win.exe
  Rust / Tauri 2.5.1 / WebView2
    ├─ 内嵌连接页：get_server_url → window.location.href = URL
    ├─ 原生全局快捷键、通知窗口、浏览器打开、站点数据清理
    └─ 加载服务端提供的主界面
          web_front/index.html
            ├─ assets/index-D8G8J-aW.js
            ├─ assets/index-GtP8_cVt.css
            ├─ assets/i18n/{13 languages}/translation.json
            └─ REST /api/... + Socket.IO + AudioWorklet
                  2.1.4-alpha server
```

附件 EXE 是一个轻量原生宿主，不是整个模型推理服务。主界面样式、控件和业务流程主要存在于发行包的 `web_front` 中，因此想修改你喜欢的 2.1.4-alpha 界面，优先从该前端开始最直接。

## EXE 静态证据

- PE32+、AMD64，ImageBase `0x140000000`，入口 `0x140833f20`，6 个节。
- PE 时间戳为 `2025-06-24T03:09:12Z`；它是链接元数据，不等于用户文件修改时间或发布版本日期。
- PDB 名称：`vcclient_native_client.pdb`，未找到随包 PDB。
- 编译路径包含 `tauri-2.5.1`、`tauri-runtime-wry-2.6.0`、`tauri-plugin-global-shortcut-2.2.1`、`tauri-plugin-notification-2.2.2`、`tauri-plugin-opener-2.2.7`。
- 应用标识字符串：`com.vcclient-native-client.app`；二进制保留 `0.1.0` 模板版本，不能靠它判断发行包版本。
- 应用源文件路径残留：`src/lib.rs`、`src/config/shortcut_config.rs`、`src/shortcut/mod.rs`、`src/notification/mod.rs`。这只是路径线索，不是恢复出的 Rust 文件。

[Tauri 2.5.1 的打包代码](https://github.com/tauri-apps/tauri/blob/tauri-v2.5.1/crates/tauri-codegen/src/embedded_assets.rs)说明资源以 PHF 表和 Brotli 内容嵌入。提取器扫描 `.rdata` 中的 Rust 字符串/字节切片四元组，将 PE 虚拟地址映射到文件偏移，逐条解压验证。没有把随机 ZIP/PYZ 字节误判为打包器。

| 内嵌文件 | 表偏移 | Brotli 数据偏移 | 压缩/解压字节数 |
| --- | --- | --- | --- |
| `/index.html` | `0x8b48b8` | `0x870b8f` | 197 / 410 |
| `/favicon.ico` | `0x8b48d8` | `0x870c60` | 159307 / 230481 |
| `/assets/index-DXT-JtqG.js` | `0x8b48f8` | `0x897ac4` | 118253 / 394687 |

原始内嵌 HTML 引用不存在的 `/vite.svg`，这一点保留原样，没有“修补”证据文件。可读版包含 React 和国际化等依赖代码，约 23,000 行，并不全是应用逻辑。

## 主界面恢复与开发切入点

发行包 HTML **实际引用** `index-D8G8J-aW.js`，其原始大小为 2,207,447 字节。ZIP 还包含其他 11 份 `index-*.js`；本次全部保留，但没有任意选择其中体积最大或文件名排序最后的 bundle 作为入口。

当前入口的动态依赖是 `browser-ponyfill-8xTspxQN.js`。CSS、13 种语言、图标、官方示例音频、GUI 参数及许可清单一并恢复。所有前端资产均无 `.map` 文件，没有可用于恢复原始文件树的 source map。

从随包许可清单可识别 React/React DOM 19.1.0、MUI 7.1.2、Emotion React 11.14.0、Vite 7.0.0、TypeScript 5.8.3；这些是随包记录，不是本次新创建的可复现 package.json。

构建产物仍保留大量有意义的名称，最有价值的切入点包括：

- `Demo`、`ModelSelector`、`ModelList`、`PortraitArea`：整体布局、模型列表、人物区域。
- `InputControls`、`VolumeControls`、`VoiceControls`、`MainControls`：设备、音量、模型参数、运行控制。
- `AdvancedSettingDialog`、`ShortcutSettingDialog`：高级设置和快捷键设置。
- `VCRestClient`、`RestClient`、`FileUploaderClient`：HTTP 协议适配层。
- `VoiceChangerClient`、`useVoiceChangerClient`：浏览器端音频处理与客户端状态。
- `useHotKeySetting`：原生事件如何变成切换模型、开关转换、增益调整和通知。

具体行号见 `readable/CODE_INDEX.md`。`readable/modules` 文件是可追溯的声明摘录，保留原局部变量名和共享引用。没有声称这些摘录是能独立编译的组件项目，也没有自动把所有短变量名猜测成业务名。

## 原生桥接接口

| 命令/事件 | 已观察用途 | 证据 |
| --- | --- | --- |
| `get_server_url` | 连接页获取启动 URL；有值则跳转 | native-client.js 的 `xC` |
| `get_shortcut_settings` | 获取快捷键配置 | `useHotKeySetting` |
| `update_shortcut_settings` | 写入 `{configDto}` | `useHotKeySetting` |
| `register_shortcuts` | 更新配置后重新注册快捷键 | `useHotKeySetting` |
| `shortcut-action` | `{action, volumeType, delta}` 原生事件 | `useHotKeySetting` |
| `show_notification_window_with_message` | 发送 `{params}` 状态信息 | `useHotKeySetting` |
| `hide_notification_window` | 点击或倒计时后隐藏通知 | native-client.js 的 `C0` |
| `open_browser_url` | 将地址交给系统浏览器 | `AdvancedArea` |
| `set_clear_site_data_and_stop_app` | 清理站点数据并退出的请求 | `AdvancedArea` + EXE 字符串 |

通知窗口入口是 `index.html?mode=notification`；网页暴露 `window.startCountdown()` 和 `window.updateNotificationContent(...)`。通知默认显示 5 秒。快捷键事件驱动前端执行 `ShowStatus`、`NextSlot`、`PreviousSlot`、`ToggleVoiceConversion`、`TogglePassthrough`、`VolumeChange`。原生侧还存在窗口切换相关字符串，不能据此认定其全部实现细节已恢复。

类型参考见 `contracts/native-client.d.ts`。若以后重建 Rust 壳，可从这些实际调用点恢复兼容接口，再逐项验证配置存储位置、快捷键默认值、窗口生命周期、远程页面 IPC 权限等。当前没有生成未经验证的 Cargo 工程。

## 与当前 fork 的接口差异

当前仓库 `server/restapi/MMVC_Rest_Fileuploader.py` 注册 `/info` 和 `POST /update_settings` 等接口；恢复的 `VCRestClient` 则使用如下 API：

| 行为 | 2.1.4-alpha 接口 |
| --- | --- |
| 获取/更新全局配置 | `GET/PUT /api/configuration-manager/configuration` |
| 输入/输出设备 | `GET /api/audio-device-manager/input_devices`、`output_devices` |
| 获取模型槽 | `GET /api/slot-manager/slots` |
| 更新/删除模型槽 | `PUT/DELETE /api/slot-manager/slots/{index}` |
| 分块上传 | `POST /api/uploader/upload_file_chunk` |
| 启停服务端音频 | `POST /api/local-voice-changer-interface/operation/start`、`stop` |
| 获取转换状态 | `GET /api/voice-changer-manager/information` |
| 客户端音频转换 | `/api/voice-changer/convert_chunk`、`convert_chunk_bulk` 和 Socket.IO 相关代码 |

因此，直接覆盖当前 `client/demo` 编译产物不能保证功能工作。后续适合分两步：先在此独立目录基于原版服务端修改界面；再把 UI 拆回维护性更好的组件，并以 `VCRestClient`、音频协议和全局状态为边界接入当前 fork。这里没有修改用户已经进行中的界面改动。

## 验证边界

- 官方 ZIP 哈希与附件 EXE 哈希均匹配。
- 96 个原始提取文件 SHA-256 校验通过，ZIP 解压同时校验 CRC。
- 27 份原始/格式化 JS 通过 Node 模块语法检查。
- 主入口依赖文件存在，开发副本构建通过。
- 独立 HTTP 服务返回首页/版本文件 200、无后端 API 503、缺失文件 404、静态写请求 405。
- 浏览器真实渲染出 `Realtime Voice Changer Client ver 2.1.4-alpha cuda`、模型列表和设置入口；截图为 `evidence/preview-without-backend.png`。
- 本次只验证静态显示，没有将预览连接到用户正在运行的服务端，没有测试实时变声或原生桥接行为。
