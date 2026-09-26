// Extracted declaration from ../main-ui.js:93720-94031.
// Navigation/reference excerpt; shared bundle dependencies are NOT imported.
// Edit ../main-ui.js for a runnable change. This is not original TS/TSX source.
class VoiceChangerClient {
  voiceChangerStatusListener = null;
  voiceChangerExceptionListener = null;
  ctx;
  vfEnable = !1;
  vf = null;
  currentDevice = null;
  currentMediaStream = null;
  currentMediaStreamAudioSourceNode = null;
  currentMediaStreamAudioDestinationNode;
  currentMediaStreamAudioDestinationMonitorNode;
  inputGainNode;
  outputGainNode;
  monitorGainNode;
  inputAnalyser;
  outputAnalyser;
  inputRms = 0;
  outputRms = 0;
  vcInNode;
  promiseForInitialize;
  _isVoiceChanging = !1;
  setting = {
    inputGain: 1,
    outputGain: 1,
    monitorGain: 1,
    audioInput: "none",
    echoCancel: !1,
    noiseSuppression: !1,
    noiseSuppression2: !1,
    sampleRate: 48e3,
  };
  nodeSetting = { protocol: "rest", sendingMode: "bulk" };
  workletSetting = {
    realtimeOutputStatusEnabled: !1,
    isPassthroughEnabled: !1,
    realtimeOutputStatusSendIntervalSec: 10,
    sendingChunkSec: 0.2,
  };
  sslCertified = [];
  sem = new BlockingQueue();
  constructor() {}
  initialize(C, E) {
    (log("info", LOG_PREFIX, "initializing..."),
      (this.ctx = C),
      (this.vfEnable = E),
      this.sem.enqueue(0),
      (this.inputGainNode = this.ctx.createGain()),
      (this.outputGainNode = this.ctx.createGain()),
      (this.monitorGainNode = this.ctx.createGain()),
      (this.inputAnalyser = this.ctx.createAnalyser()),
      (this.outputAnalyser = this.ctx.createAnalyser()),
      (this.inputGainNode.gain.value = this.setting.inputGain),
      (this.outputGainNode.gain.value = this.setting.outputGain),
      (this.monitorGainNode.gain.value = this.setting.monitorGain),
      (this.currentMediaStreamAudioDestinationNode =
        this.ctx.createMediaStreamDestination()),
      (this.currentMediaStreamAudioDestinationMonitorNode =
        this.ctx.createMediaStreamDestination()));
    const w = { outputChannelCount: [1] };
    this.promiseForInitialize = new Promise(async (R) => {
      const _ = URL.createObjectURL(
        new Blob([workerjs], { type: "text/javascript" }),
      );
      await this.ctx.audioWorklet.addModule(_);
      try {
        ((this.vcInNode = new VoiceChangerWorkletNode(this.ctx, w)),
          this.vcInNode.connect(this.outputGainNode),
          this.outputGainNode.connect(
            this.currentMediaStreamAudioDestinationNode,
          ),
          this.outputGainNode.connect(this.outputAnalyser),
          this.vcInNode.connect(this.monitorGainNode),
          this.monitorGainNode.connect(
            this.currentMediaStreamAudioDestinationMonitorNode,
          ));
      } catch {
        try {
          this.ctx.audioWorklet.addModule(_).then(() => {
            ((this.vcInNode = new VoiceChangerWorkletNode(this.ctx, w)),
              this.vcInNode.connect(this.outputGainNode),
              this.outputGainNode.connect(
                this.currentMediaStreamAudioDestinationNode,
              ),
              this.vcInNode.connect(this.monitorGainNode),
              this.monitorGainNode.connect(
                this.currentMediaStreamAudioDestinationMonitorNode,
              ));
          });
        } catch (x) {
          log("error", LOG_PREFIX, x);
        }
      }
      if (
        (this.vcInNode.updateSetting(this.nodeSetting),
        this.vcInNode.updateWorkletSetting(this.workletSetting),
        this.vfEnable)
      ) {
        this.vf = await buildExports.VoiceFocusDeviceTransformer.create({
          variant: "c20",
        });
        const x = createDummyMediaStream(this.ctx);
        this.currentDevice = (await this.vf.createTransformDevice(x)) || null;
      }
      (this.setVoiceChangerWorkletNodeListener(), R());
    });
  }
  _lock = async () => await this.sem.dequeue();
  _unlock = (C) => {
    this.sem.enqueue(C + 1);
  };
  isInitialized = async () => {
    for (;;) {
      if (this.promiseForInitialize)
        return (await this.promiseForInitialize, !0);
      await new Promise((C) => setTimeout(C, 100));
    }
  };
  getRms = (C, E = 0) => {
    const w = new Float32Array(C.fftSize);
    C.getFloatTimeDomainData(w);
    let R = 0;
    for (let x = 0; x < w.length; x++) R += w[x] * w[x];
    const _ = Math.sqrt(R / w.length);
    return Math.max(_, E * 0.95);
  };
  setVoiceChangerWorkletNodeListener = () => {
    const C = {
        onRealtimeOutputStatus: (w) => {
          w.inputRms == null || w.outputRms == null
            ? ((this.inputRms = this.getRms(this.inputAnalyser, this.inputRms)),
              (this.outputRms = this.getRms(
                this.outputAnalyser,
                this.outputRms,
              )),
              this.voiceChangerStatusListener?.onRealtimeOutputStatus({
                ...w,
                inputRms: this.inputRms,
                outputRms: this.outputRms,
              }))
            : w.inputRms != null &&
              w.outputRms != null &&
              this.voiceChangerStatusListener?.onRealtimeOutputStatus({
                ...w,
                inputRms: w.inputRms,
                outputRms: w.outputRms,
              });
        },
        onRealtimeProcessStatus: (w) => {
          this.voiceChangerStatusListener?.onRealtimeProcessStatus(w);
        },
        onData: (w, R) => {
          this.voiceChangerStatusListener?.onData(w, R);
        },
      },
      E = {
        onException: (w, R) => {
          this.voiceChangerExceptionListener?.onException(w, R);
        },
      };
    (this.vcInNode.setStatusListener(C), this.vcInNode.setExceptionListener(E));
  };
  setVoiceChangerStatusListener = (C) => {
    this.voiceChangerStatusListener = C;
  };
  setVoiceChangerExceptionListener = (C) => {
    this.voiceChangerExceptionListener = C;
  };
  setup = async () => {
    if (
      (log(
        "info",
        LOG_PREFIX,
        `Input Setup=> audio: ${this.setting.audioInput}`,
      ),
      log(
        "info",
        LOG_PREFIX,
        `Input Setup=> echo: ${this.setting.echoCancel}, noise1: ${this.setting.noiseSuppression}, noise2: ${this.setting.noiseSuppression2}`,
      ),
      this.currentMediaStream &&
        (this.currentMediaStream.getTracks().forEach((C) => {
          C.stop();
        }),
        (this.currentMediaStream = null)),
      typeof this.setting.audioInput == "string")
    )
      try {
        this.setting.audioInput == "none"
          ? (log("info", LOG_PREFIX, "Input Setup=> dummy stream."),
            (this.currentMediaStream = createDummyMediaStream(this.ctx)))
          : (this.currentMediaStream =
              await navigator.mediaDevices.getUserMedia({
                audio: {
                  deviceId: this.setting.audioInput,
                  channelCount: 1,
                  sampleRate: this.setting.sampleRate,
                  sampleSize: 16,
                  autoGainControl: !1,
                  echoCancellation: this.setting.echoCancel,
                  noiseSuppression: this.setting.noiseSuppression,
                },
              }));
      } catch (C) {
        throw (log("error", LOG_PREFIX, C), this.vcInNode.stop(), C);
      }
    else this.currentMediaStream = this.setting.audioInput;
    if (
      ((this.currentMediaStreamAudioSourceNode =
        this.ctx.createMediaStreamSource(this.currentMediaStream)),
      (this.inputGainNode.gain.value = this.setting.inputGain),
      this.currentMediaStreamAudioSourceNode.connect(this.inputGainNode),
      this.currentDevice && this.setting.noiseSuppression2)
    ) {
      this.currentDevice.chooseNewInnerDevice(this.currentMediaStream);
      const C = await this.currentDevice.createAudioNode(this.ctx);
      (this.inputGainNode.connect(C.start),
        C.end.connect(this.vcInNode),
        C.end.connect(this.inputAnalyser));
    } else
      (this.inputGainNode.connect(this.vcInNode),
        this.inputGainNode.connect(this.inputAnalyser));
    console.log("Input Setup=> success");
  };
  get stream() {
    return this.currentMediaStreamAudioDestinationNode.stream;
  }
  get monitorStream() {
    return this.currentMediaStreamAudioDestinationMonitorNode.stream;
  }
  start = async () => {
    (await this.vcInNode.start(), (this._isVoiceChanging = !0));
  };
  stop = async () => {
    (await this.vcInNode.stop(), (this._isVoiceChanging = !1));
  };
  get isVoiceChanging() {
    return this._isVoiceChanging;
  }
  setServerUrl = (C, E = !1) => {
    const w = validateUrl(C),
      R = `${location.protocol}//${location.host}`;
    throw (
      w != R &&
        w.length != 0 &&
        location.protocol == "https:" &&
        this.sslCertified.includes(w) == !1 &&
        E &&
        (window.confirm(
          "MMVC Server is different from this page's origin. Open tab to open ssl connection. OK? (You can close the opened tab after ssl connection succeed.)",
        )
          ? (window.open(w, "_blank"), this.sslCertified.push(w))
          : alert("Your voice conversion may fail...")),
      new Error("setServerUrl not implemented")
    );
  };
  getClientSetting = () => ({
    voiceChangerClientSetting: { ...this.setting },
    workletNodeSetting: { ...this.nodeSetting },
    workletSetting: { ...this.workletSetting },
  });
  updateClientSetting = async (C) => {
    const E = await this._lock();
    let w = !1;
    (console.log("updateClientSetting", C),
      (this.setting.audioInput != C.audioInput ||
        this.setting.echoCancel != C.echoCancel ||
        this.setting.noiseSuppression != C.noiseSuppression ||
        this.setting.noiseSuppression2 != C.noiseSuppression2 ||
        this.setting.sampleRate != C.sampleRate) &&
        (console.log("updateClientSetting update required"), (w = !0)),
      this.setting.inputGain != C.inputGain && this._setInputGain(C.inputGain),
      this.setting.outputGain != C.outputGain &&
        this._setOutputGain(C.outputGain),
      this.setting.monitorGain != C.monitorGain &&
        this._setMonitorGain(C.monitorGain),
      (this.setting = C),
      w && (await this.setup()),
      await this._unlock(E));
  };
  updateNodeSetting = async (C) => {
    const E = await this._lock();
    (this.vcInNode.updateSetting(C),
      (this.nodeSetting = C),
      await this._unlock(E));
  };
  updateWorkletSetting = async (C) => {
    const E = await this._lock();
    (this.vcInNode.updateWorkletSetting(C),
      (this.workletSetting = C),
      await this._unlock(E));
  };
  _setInputGain = (C) => {
    this.inputGainNode && C != null && (this.inputGainNode.gain.value = C);
  };
  _setOutputGain = (C) => {
    this.outputGainNode && C != null && (this.outputGainNode.gain.value = C);
  };
  _setMonitorGain = (C) => {
    this.monitorGainNode && C != null && (this.monitorGainNode.gain.value = C);
  };
  resetBuffer = () => this.vcInNode.resetBuffer();
  startInputRecording = () => {
    this.vcInNode.startInputRecording();
  };
  stopInputRecording = () => this.vcInNode.stopInputRecording();
  startOutputRecording = () => this.vcInNode.startOutputRecording();
  stopOutputRecording = () => this.vcInNode.stopOutputRecording();
  getOutputBufferSize = async () => await this.vcInNode.getOutputBufferSize();
  abortAllRequests = () => this.vcInNode.abortAllRequests();
  isRequestPending = () => this.vcInNode.isRequestPending();
  getPendingRequestCount = () => this.vcInNode.getPendingRequestCount();
}
