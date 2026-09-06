# VCClient × Official RVC Upstream Integration

## 0. 任务背景

当前项目基于 w-okada/voice-changer（VCClient）。

项目现有的 RVC 实现已经与官方 RVC 项目长期分叉。VCClient 自己维护了一套：

* RVC Pipeline
* Embedder
* Pitch Extractor
* Inferencer
* Model loader
* FAISS index handling
* Device manager
* ONNX 相关实现

这导致官方 RVC 后续加入的新优化、模型支持、CUDA Graph、F0 改进、推理性能优化等无法自动获得，需要手工移植。

本次重构目标不是重写 VCClient，也不是把官方 RVC 仓库直接 merge 进 VCClient。

核心目标是：

> 保留 VCClient 作为实时变声应用框架，同时把 RVC 推理实现逐步替换成官方 RVC upstream。

VCClient 应继续负责：

* UI
* Model Slot
* 音频设备管理
* Server Device
* Client Device
* 局域网 Client / Server 推理
* 网络协议
* GPU 选择 UI
* 输入输出采样率管理
* 实时 chunk 调度
* crossfade / 输出拼接
* monitor
* 性能统计
* 配置持久化

Official RVC upstream 负责：

* `.pth` RVC 模型加载
* HuBERT / ContentVec feature extraction
* RMVPE / FCPE / PM 等 F0
* FAISS retrieval
* RVC synthesizer
* RVC v1/v2 模型兼容
* pitch conversion
* protect
* index rate
* CUDA Graph
* 官方后续增加的 RVC inference 优化

设计原则：

> VCClient 是 Application Host。
>
> Official RVC 是 Inference Backend。

两者之间必须存在一层明确、足够薄的 Adapter。

---

# 1. 上游项目

Application upstream：

`https://github.com/w-okada/voice-changer`

Inference upstream：

`https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI`

当前工作仓库以 VCClient 为主体。

官方 RVC 不应该成为另一个 Git branch，也不要尝试：

```text
git merge RVC-Project/main
```

这两个仓库不是同一个代码库的分支，禁止使用这种方式合并。

---

# 2. 第一阶段支持平台

首要目标：

```text
Windows 10 / Windows 11 x64
NVIDIA CUDA GPU
RVC PyTorch .pth model
FAISS .index
```

优先保证 NVIDIA CUDA。

CPU fallback 可以保留。

DirectML / AMD / Intel GPU 暂时不是新 backend 第一阶段的重点。

但是：

**不能因为新增 upstream backend 而破坏 VCClient 原有 legacy backend 的其他平台支持。**

旧 backend 在迁移完成前必须继续存在。

---

# 3. 非目标

第一阶段不要做以下工作：

* 不重写整个 UI
* 不替换 VCClient 的音频设备管理
* 不引入官方 RVC WebUI
* 不引入 Gradio
* 不把 Applio 引进项目
* 不用浏览器页面代替现有客户端
* 不删除 Client / Server 网络能力
* 不删除 Server Device
* 不删除 GPU 手动选择能力
* 不重写整个 VoiceChanger
* 不立即删除旧 RVC implementation
* 不立即删除 MMVC / DDSP / Beatrice / DiffusionSVC 等其他 backend
* 不做无关代码格式化
* 不进行全仓库大规模 rename
* 不因为方便而让 Official RVC 控制音频设备
* 不允许 Official RVC 自动覆盖用户手动选择的 GPU

这一阶段是：

> RVC inference backend replacement / migration

而不是：

> VCClient rewrite

---

# 4. 开始修改之前必须完成的分析

首先完整阅读当前仓库中与下面内容有关的代码。

重点包括但不限于：

```text
server/voice_changer/RVC/
server/voice_changer/RVC/RVC.py
server/voice_changer/RVC/RVCr2.py
server/voice_changer/RVC/RVCSettings.py
server/voice_changer/RVC/pipeline/
server/voice_changer/RVC/inferencer/
server/voice_changer/RVC/embedder/
server/voice_changer/RVC/pitchExtractor/
server/voice_changer/RVC/deviceManager/

server/voice_changer/VoiceChanger.py
server/voice_changer/VoiceChangerV2.py

server/voice_changer/Local/
server/voice_changer/Local/ServerDevice.py

server/voice_changer/utils/VoiceChangerModel.py

server/data/ModelSlot.py

client/
```

需要搞清楚：

```text
Audio input
    ↓
VoiceChanger
    ↓
RVC model
    ↓
Pipeline
    ↓
Inference
    ↓
VoiceChanger
    ↓
crossfade / resampling
    ↓
Audio output
```

以及：

```text
Client Device
Server Device
LAN Client
LAN Server
```

分别在哪里进入这个流程。

同时分析 official RVC 当前 realtime implementation。

重点：

```text
configs/config.py

infer/rtrvc.py

infer/hubert.py

infer/module/

tools/cuda_graph.py

gui_v1.py
```

其中：

`gui_v1.py`

只作为：

* realtime buffer 参数计算参考
* upstream RVC 调用方式参考
* CUDA Graph 使用参考

不要复用其中的 GUI 或音频设备管理。

分析完成后在项目中生成：

```text
docs/rvc-upstream-integration.md
```

记录实际发现的调用关系。

如果实际代码结构与本任务说明有差异，以当前代码为准，但必须保持本任务定义的架构边界。

完成分析后，如果没有真正的 blocker，不需要等待人工确认，继续执行重构。

---

# 5. 目标架构

最终应形成类似：

```text
VCClient
│
├─ UI
├─ Model Slot
├─ Audio I/O
├─ Server Device
├─ Client Device
├─ Network Client / Server
├─ VoiceChanger
│
└─ RVC Model Host
      │
      ├─ LegacyRvcBackend
      │
      └─ UpstreamRvcBackend
              │
              ▼
        Official RVC
```

这里最重要的是：

```text
VoiceChanger
```

不应该知道 official RVC 内部：

```text
HuBERT
RMVPE
FCPE
FAISS
Synthesizer
CUDA Graph
```

具体如何工作。

这些必须被 Adapter 隔离。

---

# 6. 新建 RVC Backend 抽象

设计一个明确的 backend abstraction。

实际名称可以根据项目风格调整，例如：

```text
RvcBackend
RvcInferenceBackend
RvcEngine
```

建议目录：

```text
server/voice_changer/RVC/backend/
```

例如：

```text
backend/
├─ base.py
├─ legacy.py
├─ upstream.py
├─ config.py
├─ model_info.py
└─ exceptions.py
```

不要过度设计。

核心接口至少需要表达：

```python
class RvcBackend(Protocol):

    def load_model(...):
        ...

    def unload_model(...):
        ...

    def infer(...):
        ...

    def update_settings(...):
        ...

    def set_device(...):
        ...

    def get_model_info(...):
        ...

    def close(...):
        ...
```

具体签名请根据 VCClient 当前数据流设计。

目标不是设计“全世界通用 AI backend API”。

它只需要干净地隔离：

```text
VCClient
↔
RVC implementation
```

---

# 7. Legacy Backend

当前：

```text
server/voice_changer/RVC/
```

中现有的：

* Pipeline
* Inferencer
* PitchExtractor
* Embedder
* DeviceManager

第一阶段不要删除。

将它视为：

```text
Legacy RVC Backend
```

必要时通过一个很薄的 wrapper 使其符合新的 `RvcBackend` interface。

旧行为必须尽量保持不变。

目的：

1. 为新 backend 提供 A/B 基准
2. 新 backend 出错时可以 fallback
3. 降低一次性重构风险
4. 可以比较音质、延迟和 GPU 占用

---

# 8. Official RVC Upstream 的管理方式

不要复制几份零散文件到项目各处。

不要把 official RVC 代码手工改名后塞进：

```text
voice_changer/RVC/
```

优先考虑：

```text
third_party/rvc/
```

或者：

```text
vendor/rvc/
```

保存 official RVC upstream。

优先使用：

* git subtree
* vendored source + upstream commit metadata

不建议使用 submodule，除非现有项目已有成熟 submodule 工作流。

原因：

VCClient 是需要制作 Windows release package 的应用。

submodule 容易造成：

* clone 缺代码
* CI 忘记 recursive clone
* release package 缺依赖
* 用户本地 build 麻烦

---

# 9. Vendor 原则

尽可能保持：

```text
third_party/rvc/
```

为 upstream 原始代码。

禁止：

为了适应 VCClient，直接大量修改 upstream 文件。

理想状态：

```text
third_party/rvc/
    ↑
保持接近官方

server/voice_changer/RVC/backend/upstream.py
    ↑
负责适配
```

如果 upstream 必须修改：

优先：

```text
patches/
```

或者非常小、明确、有注释的 downstream patch。

每个 patch 都需要说明：

```text
为什么需要
对应 upstream 哪个问题
未来是否可以删除
```

---

# 10. Upstream 版本必须固定

不要运行时：

```text
git pull latest
```

不要永远追踪 floating main。

记录当前使用的：

```text
repository
commit hash
date
```

例如：

```text
third_party/rvc/UPSTREAM.md
```

包含：

```text
Repository:
RVC-Project/Retrieval-based-Voice-Conversion-WebUI

Commit:
<commit hash>

Imported:
<date>

Local patches:
...
```

目标是：

> 构建可重复。

---

# 11. Upstream Backend 的核心实现

优先研究并复用 official RVC：

```text
infer/rtrvc.py
```

不要优先复用：

```text
gui_v1.py
```

`gui_v1.py` 是 Application / GUI 层。

`infer/rtrvc.py` 才更接近我们需要的 inference implementation。

Official RVC 当前 realtime class 已经接受类似：

```python
RVC(
    key,
    formant,
    pth_path,
    index_path,
    index_rate,
    config,
    last_rvc,
)
```

并提供实时 inference。

Adapter 应负责将 VCClient 参数映射到这里。

---

# 12. 不使用 Official RVC 的音频系统

这是强约束。

Official RVC 不应该：

* 枚举麦克风
* 打开 PortAudio stream
* 管理输出设备
* 管理 monitor
* 管理虚拟声卡
* 控制 Server Device
* 控制 Client Device

音频系统仍然属于 VCClient：

```text
VCClient audio input
       ↓
VCClient buffering
       ↓
UpstreamRvcBackend.infer()
       ↓
VCClient output processing
       ↓
VCClient audio output
```

Official RVC 只看见：

```text
audio tensor / numpy data
parameters
```

并返回：

```text
converted audio
```

---

# 13. 不使用 Official RVC 的自动 GPU 选择

这一点非常重要。

Official RVC 当前 `configs/config.py` 有自己的 GPU 检测和默认设备选择逻辑。

VCClient 已经允许用户在 UI 中选择 GPU。

VCClient 的 GPU 选择必须拥有最高优先级。

例如：

```text
GPU 0 RTX 5090
GPU 1 RTX 5060
GPU 2 RTX 4060
```

用户选择：

```text
GPU 1
```

则 upstream inference 必须运行：

```python
torch.device("cuda:1")
```

不能因为 official RVC 认为 GPU 0 更快而改成：

```text
cuda:0
```

---

# 14. 不要强依赖 Official Config singleton

优先研究：

是否可以不直接依赖：

```python
official_rvc.configs.config.Config()
```

而由 Adapter 构造一个：

```python
RvcRuntimeConfig
```

只实现 official realtime inference 真正需要的字段，例如：

```python
device
dtype
is_half
cuda_graph
```

示意：

```python
@dataclass
class RvcRuntimeConfig:
    device: torch.device
    dtype: torch.dtype
    is_half: bool
    cuda_graph: bool
```

然后：

```text
VCClient selected GPU
        ↓
RvcRuntimeConfig
        ↓
official infer/rtrvc.py
```

如果 upstream API 实际还需要其他字段，再根据当前源码补充。

不要提前复制整个 Official Config。

避免 VCClient 被：

* argparse
* global state
* singleton
* environment variables
* automatic GPU selection

污染。

---

# 15. GPU / dtype 策略

需要实现：

```text
GPU index
    ↓
torch.cuda device
    ↓
capability / compatibility check
    ↓
fp16 or fp32
```

用户显式选择 GPU 后：

优先尊重用户设备选择。

但是 dtype 可以依据设备能力判断。

例如：

```text
RTX 50 / 40 / 30
→ fp16

不支持可靠 fp16 的设备
→ fp32
```

具体规则优先参考 official RVC 当前实现。

不要复制一套过时规则。

如果 CUDA device 不可用，应输出明确错误。

不要偷偷 fallback 到另一块 GPU。

可以允许：

```text
selected cuda:1 unavailable
→ error
```

而不是：

```text
selected cuda:1 unavailable
→ secretly use cuda:0
```

因为对于多 GPU 用户，这种行为很难排查。

---

# 16. CUDA Graph

Official RVC upstream 已经支持 CUDA Graph。

新 backend 应尽量复用官方实现。

需要：

* 检测当前选择 GPU 是否支持
* 允许启用
* 不支持时自动安全回退到 eager inference
* CUDA Graph 失败不能导致整个 VCClient 崩溃
* 在日志中明确输出当前状态

例如：

```text
RVC Backend: Official
Device: cuda:1
Precision: fp16
CUDA Graph: enabled
```

或者：

```text
CUDA Graph: unavailable, using eager mode
```

不要静默。

---

# 17. Model loading

必须继续支持 VCClient 当前 RVC model slot。

包括：

```text
.pth
.index
```

以及当前 model slot 中已有信息：

```text
modelFile
indexFile
defaultTune
defaultIndexRatio
defaultProtect
samplingRate
f0
version
speakers
```

Adapter 负责从：

```text
RVCModelSlot
```

构建 official RVC model。

不要要求用户重新导入现有模型。

现有模型目录必须尽可能保持兼容。

---

# 18. RVC v1 / v2

必须至少保持 official RVC 支持的：

```text
RVC v1
RVC v2
```

模型。

不要根据 VCClient model slot 的 metadata 盲目判断。

尽量让 official loader 从 checkpoint 本身判断：

```text
version
f0
speaker count
sample rate
```

VCClient metadata 可以作为缓存/展示信息。

模型本身应该是最终真相来源。

---

# 19. Speaker ID

VCClient 当前支持：

```text
dstId
speakers
```

Official backend 必须支持 speaker ID。

单 speaker model：

```text
default 0
```

multi-speaker model：

使用 VCClient 当前选择的：

```text
dstId
```

如果 speaker ID 超出范围：

返回明确错误。

不要 silently clamp 到 0。

---

# 20. Index

继续支持：

```text
.index
```

以及：

```text
indexRatio
```

映射到 official RVC：

```text
index_rate
```

需要处理：

```text
index missing
index invalid
index_rate = 0
```

当：

```text
index_rate = 0
```

时应该允许没有 index。

当：

```text
index_rate > 0
```

且 index 不可用时：

优先给出明显 warning / error。

不要因为 index 出错导致整个 server 无提示退出。

---

# 21. 参数映射

至少需要明确映射：

```text
VCClient             Official RVC

tran             → pitch/key
indexRatio       → index_rate
protect          → protect
dstId            → speaker id
gpu              → device
f0Detector       → f0 method
```

其他参数逐项分析。

建立一个单独的映射层。

不要让 UI 字段名渗透进 upstream。

例如：

```python
def build_inference_options(settings: RVCSettings) -> RvcInferenceOptions:
    ...
```

---

# 22. F0 Detector

需要检查 VCClient 当前支持：

```text
dio
harvest
crepe
rmvpe
rmvpe_onnx
...
```

与 official realtime RVC 当前支持的实际交集。

不要假设名称完全一致。

建立映射，例如概念上：

```text
VCClient rmvpe / rmvpe_onnx
→ official rmvpe
```

但具体映射必须根据代码实际行为决定。

如果某个 legacy F0 backend official 不再支持：

第一阶段不要假装支持。

可以：

```text
Legacy Backend
→ 全部旧 detector

Official Backend
→ official 当前支持 detector
```

UI 根据 backend 决定可选项。

---

# 23. Formant

Official RVC realtime 目前有 formant 参数。

如果 VCClient 当前 UI 没有：

第一阶段可以使用：

```text
0
```

不要为了这个参数立即修改 UI。

后续再单独增加。

---

# 24. 实时 Buffer

这是整个迁移最需要谨慎的地方。

VCClient 已经有自己的实时：

* audio buffer
* extraConvertSize
* chunk
* crossfade
* overlap
* resampling

Official realtime RVC 自己也有：

* input history
* pitch cache
* feature context
* skip_head
* return_length
* block frame

不能简单地：

```text
VCClient chunk
→ official infer()
```

然后假设一定正确。

需要先理解 official：

```python
infer(
    input_wav,
    block_frame_16k,
    skip_head,
    return_length,
    f0method,
)
```

每个参数的意义。

然后建立：

```text
VCClient streaming context
        ↓
RvcRealtimeRequest
        ↓
Official rtrvc
```

特别检查：

* 历史上下文长度
* 当前 block 长度
* 输出长度
* pitch cache
* feature context
* 首包 warmup
* model sample rate
* 16 kHz feature input
* output resampling

必须避免：

```text
重复 padding
重复 history
重复 resample
重复 crossfade
```

否则会增加延迟和音质问题。

---

# 25. Crossfade / SOLA

默认原则：

> 只保留一套最终输出拼接策略。

如果 VCClient 当前 outer VoiceChanger 已经负责 crossfade，则不要再完整套一遍 official GUI 的 SOLA/crossfade。

Official：

```text
RVC inference core
```

负责模型推理。

VCClient：

```text
stream stitching
```

负责最终实时音频拼接。

但是如果经过测试证明 official realtime inference 对某部分状态管理有强依赖，需要区分：

```text
model context
```

与：

```text
audio output crossfade
```

不要为了“代码看起来统一”强行删除必要 realtime context。

---

# 26. Resampling

仔细梳理当前数据路径。

避免：

```text
48k
↓
16k
↓
48k
↓
16k
↓
48k
```

这种重复 resample。

最终应明确：

```text
Device SR
↓
VCClient processing SR
↓
16k feature path
↓
RVC model SR
↓
VCClient output SR
```

记录每一步：

* 谁负责
* 为什么需要
* dtype
* tensor location
* CPU/GPU

如果 upstream 已有 GPU resampling 优化，应研究是否可以安全复用。

但第一阶段优先正确性，再优化。

---

# 27. Tensor copy

实时链路中注意：

```text
numpy → torch
CPU → GPU
GPU → CPU
```

次数。

不要在每个小步骤反复：

```python
.cpu().numpy()
torch.from_numpy(...)
.to(device)
```

但是：

第一阶段不要为了减少一次 copy 而进行危险的全局重构。

完成正确 backend 后，增加 profiling，再优化。

---

# 28. Model warmup

新 backend 应支持 warmup。

模型加载后：

```text
load model
load hubert
load pitch model
initialize index
prepare CUDA
optional CUDA Graph
warmup
ready
```

只有 ready 后再开始正常 realtime inference。

避免：

第一句话产生：

```text
数百毫秒 ~ 数秒卡顿
```

日志需要区分：

```text
Loading model
Loading HuBERT
Loading index
Warming up
Ready
```

---

# 29. 模型共享

Official realtime RVC 支持复用部分模型状态。

研究：

```text
last_rvc
```

机制。

如果切换角色模型时：

```text
HuBERT
RMVPE
```

可以安全复用，就复用。

目标：

```text
Model A
→ Model B
```

不要每次都重新加载所有 shared model。

但是必须确认：

* device 一致
* dtype 一致
* embedder compatible

如果 GPU 改变：

```text
cuda:0
→ cuda:1
```

则必须正确重建相关状态。

---

# 30. GPU 切换

VCClient 当前支持运行时修改：

```text
gpu
```

新 backend 必须正确处理。

期望流程：

```text
User selects GPU
↓
stop inference safely
↓
release old backend GPU objects
↓
torch cleanup if appropriate
↓
create backend on new device
↓
load/warmup
↓
resume
```

不能留下：

```text
model on cuda:0
pitch model on cuda:1
```

这种混合状态。

日志应该明确：

```text
RVC backend moved:
cuda:0 → cuda:1
```

---

# 31. 不允许 GPU 全局污染

如果可能，不要：

```python
torch.cuda.set_device(...)
```

作为核心切换机制。

优先：

```python
torch.device("cuda:N")
tensor.to(device)
model.to(device)
```

因为未来：

```text
多个 backend
多个模型
多个 GPU
```

可能同时存在。

如果 upstream 某处必须依赖 current CUDA device，要明确隔离并记录。

---

# 32. Backend Selector

第一阶段增加：

```text
Legacy
Official
```

两个 backend。

可以先通过：

* config
* environment
* debug setting
* server setting

选择。

如果修改 UI 成本很低，可以在 RVC 设置页增加：

```text
Inference Backend

Legacy
Official
```

默认第一阶段建议：

```text
Legacy
```

等 Official backend 经验证稳定后再改默认。

如果 UI 修改明显增加任务复杂度：

第一阶段可以先使用 server config：

```text
rvcBackend = legacy | official
```

但必须容易切换做 A/B test。

---

# 33. Backend 不要存入 model slot

Backend 类型是：

```text
runtime / application setting
```

不是模型属性。

不要把：

```text
official
legacy
```

写进每个 `.pth` model slot。

同一个模型应该可以：

```text
Model A
   ├ Legacy backend
   └ Official backend
```

直接切换。

---

# 34. LAN Client / Server

必须完整保留。

这是 VCClient 相比普通 RVC GUI 的核心价值之一。

期望：

```text
PC A
Microphone
VCClient Client

     LAN

PC B
VCClient Server
RTX GPU
Official RVC Backend

     LAN

PC A
Audio output
```

Backend replacement 不能改变这个应用层设计。

客户端不需要安装完整 official RVC。

推理服务器负责：

```text
RVC runtime
model
CUDA
```

如果当前协议只传 PCM / control data，则继续保持。

不要为了 Official backend 把模型推理搬到 Client。

---

# 35. Server Device

以下能力必须保留：

```text
Input device
Output device
Monitor device
Gain
Sample rate
Exclusive mode
```

Official RVC backend 不应该感知这些 device id。

Backend API 输入应该已经是：

```text
audio data
```

而不是：

```text
audio device
```

---

# 36. 异常处理

建立明确 backend exception。

例如：

```text
RvcBackendError
RvcModelLoadError
RvcIndexLoadError
RvcDeviceError
RvcInferenceError
RvcCudaGraphError
```

不要让：

```text
torch exception
faiss exception
file exception
```

一路裸传到 UI。

日志可以保留 traceback。

UI / API 返回人类可理解的信息。

---

# 37. Backend fallback

第一阶段建议：

如果用户主动选择：

```text
Official
```

但模型加载失败：

不要无提示自动改成 Legacy。

因为这会掩盖 bug。

应该：

```text
Official backend failed:
<reason>
```

然后由用户选择 Legacy。

仅在配置明确允许：

```text
fallbackToLegacy = true
```

时才自动 fallback。

---

# 38. Logging

增加清晰日志。

启动模型至少输出：

```text
RVC Backend: Official
Upstream commit: XXXXXXX
Model: xxx.pth
Index: xxx.index
Model version: v2
Model sample rate: 48000
Speaker: 0
Device: cuda:1
GPU: NVIDIA ...
Precision: fp16
F0: rmvpe
Index rate: 0.75
CUDA Graph: enabled
```

不要每个 audio block 打日志。

实时 callback 中禁止高频 logging。

---

# 39. Performance metrics

VCClient 已经有 performance 数据。

尽量保留。

如果可行增加阶段统计：

```text
feature
index
pitch
synth
total inference
```

但不要为了这个侵入 upstream 大量代码。

最低限度：

```text
backend infer total
```

需要可测。

---

# 40. 测试

至少增加以下测试。

## Backend unit test

使用 mock backend 验证：

```text
VoiceChanger
↔
RvcBackend
```

边界。

## Config mapping test

验证：

```text
tran
indexRatio
protect
gpu
dstId
f0Detector
```

映射。

## Device selection test

至少测试：

```text
gpu=0 → cuda:0
gpu=1 → cuda:1
cpu → cpu
```

不要要求 CI 真有多个 GPU，可以 mock torch CUDA discovery。

## Model metadata test

至少覆盖：

```text
RVC v1
RVC v2
f0
non-f0
single speaker
```

如果仓库中没有适合提交的模型 fixture，不要提交大型模型。

使用：

* small mocked checkpoint
* metadata fixture

或者把完整模型测试作为 integration test。

---

# 41. Integration test

如果开发机器存在 NVIDIA GPU 和测试模型：

运行真实测试。

至少记录：

```text
Legacy backend
Official backend
```

同一段输入音频。

记录：

```text
Output length
Model SR
Inference time
GPU memory
No exception
```

如果无法自动判断音质，可以输出测试 WAV 放在：

```text
test_output/
```

但不要提交大文件。

---

# 42. Realtime 验收

最终必须人工可验证：

```text
Microphone
↓
VCClient
↓
Official backend
↓
Virtual audio device / speaker
```

连续说话至少：

```text
10 minutes
```

不应出现：

* buffer 越积越多
* 延迟持续增长
* CUDA memory 持续增长
* 周期性爆音
* model context 崩坏
* pitch cache 越界
* GPU device mismatch

---

# 43. A/B 性能比较

为同一环境记录：

```text
Model
Index
Input device
Output device
GPU
Pitch
Chunk
Sample rate
```

然后对比：

```text
Legacy
Official eager
Official CUDA Graph
```

记录至少：

```text
Mean inference time
P50
P95
GPU VRAM
Approx realtime latency
```

目标不是要求 Official 一定更快。

目标是：

> 有数据证明迁移是否值得。

---

# 44. 回归测试

必须验证原 VCClient：

```text
Legacy RVC
```

仍能工作。

同时至少 smoke test：

```text
Server starts
UI loads
model list loads
GPU list loads
Server Device can enumerate devices
LAN mode starts
```

不要因为 upstream package 改了：

```text
numpy
torch
torchaudio
faiss
```

版本导致整个旧 application 崩溃。

---

# 45. 依赖冲突处理

Official RVC 与 VCClient 很可能依赖不同版本：

```text
torch
torchaudio
numpy
faiss
librosa
sounddevice
```

不要直接：

```text
pip install official requirements.txt
```

覆盖 VCClient requirements。

先建立 dependency compatibility matrix：

```text
VCClient requires
Official RVC requires
Resolved version
Reason
```

优先寻找共同兼容版本。

如果无法共存，再评估：

```text
separate inference worker process
```

但不要第一反应就拆进程。

---

# 46. 如果依赖无法安全合并

备用架构允许：

```text
VCClient Server
    │
    │ local IPC
    ▼
Official RVC Worker Process
```

但只有在：

```text
Python dependency conflict
CUDA runtime conflict
global singleton conflict
```

确实无法合理解决时才使用。

如果需要 worker：

不要走 HTTP localhost 音频传输。

优先考虑：

```text
shared memory
named pipe
local socket
```

并把实时音频 transport 与 control 分开。

但是：

**第一阶段优先尝试 in-process Adapter。**

---

# 47. 打包

最终 Windows release 不应该要求用户另外：

```text
git clone official RVC
pip install ...
```

目标最终仍然是：

```text
下载 VCClient
运行
```

因此 vendored upstream 与其 runtime dependency 必须被 release build 正确包含。

测试：

```text
clean Windows machine
no system Python
```

能够启动 release package。

如果当前 VCClient 本身依赖 bundled Python，则沿用其机制。

---

# 48. License

保留：

```text
w-okada/voice-changer
MIT
```

同时加入 official RVC：

```text
RVC-Project/Retrieval-based-Voice-Conversion-WebUI
MIT
```

维护：

```text
THIRD_PARTY_NOTICES
```

或者项目已有对应机制则复用。

不要删除 upstream copyright。

检查 official RVC 引用的第三方组件许可证。

---

# 49. Documentation

至少增加：

```text
docs/rvc-upstream-integration.md
docs/rvc-upstream-update.md
```

第一份解释架构：

```text
VCClient
↓
Adapter
↓
Official RVC
```

第二份说明未来如何升级 official upstream。

例如：

```text
1. fetch upstream
2. inspect changelog
3. update vendored commit
4. run backend tests
5. run model tests
6. run realtime test
7. update UPSTREAM.md
```

以后更新 RVC 不应该重新研究整个工程。

---

# 50. Git / Commit 策略

不要做一个巨大 commit。

建议拆成：

```text
1. docs: document current RVC architecture

2. refactor: introduce RVC backend abstraction

3. refactor: wrap legacy RVC backend

4. vendor: import official RVC upstream

5. feat: implement official RVC backend

6. feat: map VCClient device selection to upstream RVC

7. feat: add official backend runtime selection

8. test: add backend and config tests

9. docs: document upstream update workflow
```

每一步尽量：

```text
buildable
testable
```

---

# 51. 第一轮任务边界

这次不要一口气删除 legacy RVC。

第一轮完成状态应该是：

```text
                     ┌─ Legacy RVC
VCClient → Adapter ──┤
                     └─ Official RVC
```

并且：

```text
同一个 .pth + .index
```

可以选择：

```text
Legacy
Official
```

两套 backend 启动。

这就是第一阶段成功。

---

# 52. 第二阶段再考虑的事情

第一阶段完成后暂时不要自动继续做这些。

后续可以单独处理：

```text
删除 legacy RVC pipeline
删除 legacy inferencer
删除 legacy pitch extractor
删除 legacy embedder
精简 dependency
增加 FCPE UI
增加 formant UI
更完整 CUDA Graph UI
模型快速切换
多 GPU 并行
ONNX backend 整理
UI modernization
audio engine modernization
ASIO
```

这些不属于当前 migration 的必要条件。

---

# 53. 第一阶段验收标准

必须全部满足。

### 基础功能

```text
VCClient 正常启动
现有 UI 正常
Server Device 正常
Client / Server 正常
GPU 列表正常
```

### Legacy

```text
Legacy RVC 可加载
Legacy RVC 可实时变声
```

### Official

```text
Official RVC backend 可加载 .pth
Official RVC backend 可加载 .index
RVC v2 正常
pitch 正常
index ratio 正常
protect 正常
speaker id 正常
```

### GPU

用户选择：

```text
GPU N
```

实际模型必须运行：

```text
cuda:N
```

日志可以证明。

### Realtime

```text
Microphone → RVC → Output
```

实时工作。

### LAN

Client / Server 模式仍然工作。

服务器选择 GPU 并执行 inference。

### Stability

至少连续运行：

```text
10 min
```

没有明显：

```text
VRAM leak
buffer growth
latency growth
exception loop
```

---

# 54. 代码质量要求

不要为了赶进度写：

```text
if backend == official
```

散落整个仓库。

Backend-specific behavior 应尽量限制在：

```text
RVC backend package
```

上层只认识 interface。

避免：

```text
global variables
sys.path hacks
os.chdir
environment mutation
```

如果 official upstream 必须依赖其中某些行为：

将其隔离在 upstream bootstrap 中。

不要污染整个 VCClient process。

---

# 55. 最重要的架构原则

遇到设计选择时按照下面优先级判断。

第一：

**保留 VCClient 独特价值。**

包括：

```text
LAN inference
GPU selection
audio routing
Server Device
Client Device
monitor
model management
```

第二：

**尽可能使用 Official RVC inference implementation。**

不要重新复制官方算法。

第三：

**隔离 upstream。**

以后升级 official RVC 时只应该主要修改：

```text
vendor version
adapter
```

而不是整个 VCClient。

第四：

**迁移优先于重写。**

能小步替换就不要大规模重构。

第五：

**先保证正确，再优化 latency。**

---

# 56. 最终期望

我们最终希望这个项目形成：

```text
┌──────────────────────────────┐
│           VCClient           │
│                              │
│ UI / Audio / Network / LAN   │
│ Device / Monitor / Settings  │
└──────────────┬───────────────┘
               │
               │ stable backend API
               ▼
┌──────────────────────────────┐
│      RVC Backend Adapter     │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│      Official RVC Core       │
│                              │
│ Hubert / F0 / FAISS / VITS   │
│ CUDA Graph / future updates  │
└──────────────────────────────┘
```

以后：

```text
Official RVC 发布新版本
↓
更新 vendored upstream
↓
修正少量 Adapter API
↓
测试
↓
获得最新 inference 优化
```

而不是：

```text
Official RVC 发布新版本
↓
人工阅读 diff
↓
复制几十个算法修改
↓
手工改 VCClient Pipeline
↓
产生新的长期 fork
```

---

# 57. 执行方式

现在开始执行。

首先：

1. 分析当前 VCClient RVC 调用链。
2. 分析 official RVC 当前 realtime inference API。
3. 写 `docs/rvc-upstream-integration.md`。
4. 建立 backend abstraction。
5. 把当前实现包装为 Legacy backend，保证行为不变。
6. Vendor 固定版本的 Official RVC upstream。
7. 实现 Official backend。
8. 接入 VCClient 手动 GPU 选择。
9. 实现 Legacy / Official backend 切换。
10. 添加测试。
11. 本地运行能够执行的测试与 lint/build。
12. 总结实际修改、未解决问题和下一阶段建议。

除非遇到确实无法自行决定、会导致数据破坏或架构方向完全不同的 blocker，否则不要在分析后停住等待确认。

如果某项要求因为当前仓库实际结构无法完全按描述实现：

优先保持：

```text
VCClient Application
       ↕
thin adapter
       ↕
Official RVC
```

这一核心架构，而不是机械遵守文件名。

完成后请给出：

```text
Changed files
Architecture changes
Upstream commit used
Tests executed
Test results
Known limitations
Performance comparison（如果环境允许）
Recommended next steps
```
