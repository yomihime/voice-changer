// Extracted declaration from ../main-ui.js:104852-105157.
// Navigation/reference excerpt; shared bundle dependencies are NOT imported.
// Edit ../main-ui.js for a runnable change. This is not original TS/TSX source.
const useVoiceChangerClient = (S) => {
    const { t: C } = useTranslation(),
      E = S.triggerToast,
      { currentSlotInfo: w, reloadLocalVoiceChangerInterfaceInfo: R } =
        useAppRoot(),
      _ = reactExports.useMemo(() => new VoiceChangerClient(), []),
      [x, T] = reactExports.useState(!1),
      [A, O] = reactExports.useState([]),
      [H, ee] = reactExports.useState(!1),
      te = reactExports.useRef(null);
    (reactExports.useEffect(() => {
      S.ctx != null &&
        (log$1("info", logPrefix, "initializing client..... only one called.."),
        _.initialize(S.ctx, !1),
        _.setVoiceChangerExceptionListener({
          onException: (he, me) => {
            (log$1("error", logPrefix, `onException: ${he} ${me}`),
              he == "LOCAL_VOICE_CHANGER_INTERFACE_RUN_ERROR" &&
                (E(
                  "error",
                  C("common.error_messages.server_device_init_failed"),
                ),
                R()));
          },
        }));
    }, [S.ctx, _, R, E, C]),
      reactExports.useEffect(() => {
        if (!_) return;
        (async () => {
          (await _.isInitialized(), T(!0));
        })();
      }, [_]),
      reactExports.useEffect(() => {
        if (!x) return;
        (log$1(
          "info",
          logPrefix,
          "inputAudioType",
          S.globaSetting.inputAudioType,
        ),
          log$1("info", logPrefix, "inputAudio", S.globaSetting.inputAudio));
        const me = _.getClientSetting().voiceChangerClientSetting;
        (((S.globaSetting.inputAudioType === "microphone" &&
          typeof S.globaSetting.inputAudio == "string") ||
          (S.globaSetting.inputAudioType === "file" &&
            S.globaSetting.inputAudio instanceof MediaStream) ||
          (S.globaSetting.inputAudioType === "capture" &&
            S.globaSetting.inputAudio instanceof MediaStream) ||
          (S.globaSetting.inputAudioType === "sample" &&
            S.globaSetting.inputAudio instanceof MediaStream)) &&
          (me.audioInput = S.globaSetting.inputAudio),
          (me.inputGain = S.globaSetting.nodeInputGain),
          (me.outputGain = S.globaSetting.nodeOutputGain),
          (me.monitorGain = S.globaSetting.nodeMonitorGain),
          (me.echoCancel = S.globaSetting.enableEchoCancellation),
          (me.noiseSuppression = S.globaSetting.enableNoiseSuppression),
          (me.noiseSuppression2 = S.globaSetting.enableNoiseSuppression2),
          console.log("clientSetting", me),
          _.updateClientSetting({ ...me }));
      }, [
        _,
        x,
        S.globaSetting.inputAudioType,
        S.globaSetting.inputAudio,
        S.globaSetting.nodeInputGain,
        S.globaSetting.nodeOutputGain,
        S.globaSetting.nodeMonitorGain,
        S.globaSetting.enableEchoCancellation,
        S.globaSetting.enableNoiseSuppression,
        S.globaSetting.enableNoiseSuppression2,
      ]),
      reactExports.useEffect(() => {
        (async () => {
          if (!x) return;
          if (S.globaSetting.outputAudioElementId == null) {
            console.warn(
              "[voiceChangerClient] audioOutputElementId not set for audio output.",
            );
            return;
          }
          const me = document.getElementById(
            S.globaSetting.outputAudioElementId,
          );
          if (!me) {
            console.warn(
              "[voiceChangerClient] audioOutputElementId not set for audio output.",
            );
            return;
          }
          if (S.globaSetting.outputAudio == "none") {
            (console.warn(
              "[voiceChangerClient] audioOutputDevice not set for audio output.",
            ),
              (me.volume = 0),
              (me.muted = !0));
            return;
          }
          if (
            !(await navigator.mediaDevices.enumerateDevices())
              .filter((xe) => xe.kind == "audiooutput")
              .some((xe) => xe.deviceId == S.globaSetting.outputAudio)
          ) {
            (console.warn(
              `[voiceChangerClient] audioOutputDevice ${S.globaSetting.outputAudio} not found.`,
            ),
              E(
                "error",
                C("common.error_messages.audio_output_device_not_found", {
                  device: S.globaSetting.outputAudio,
                }),
              ),
              (me.volume = 0),
              (me.muted = !0));
            return;
          }
          ((me.srcObject = null), (me.srcObject = _.stream));
          try {
            await me.setSinkId(S.globaSetting.outputAudio);
          } catch (xe) {
            (console.log("setSinkId is not supported?", xe),
              E(
                "error",
                C("common.error_messages.set_sink_id_not_supported", {
                  error: xe,
                }),
              ));
          }
          ((me.volume = 1), me.paused && me.play());
        })();
      }, [
        _,
        x,
        S.globaSetting.outputAudioElementId,
        S.globaSetting.outputAudio,
        E,
        C,
      ]),
      reactExports.useEffect(() => {
        (async () => {
          if (!x) return;
          if (S.globaSetting.monitorAudioElementId == null) {
            console.warn(
              "[voiceChangerClient] audioMonitorElementId not set for audio monitor.",
            );
            return;
          }
          const me = document.getElementById(
            S.globaSetting.monitorAudioElementId,
          );
          if (!me) {
            console.warn(
              "[voiceChangerClient] audioMonitorElementId not set for audio monitor.",
            );
            return;
          }
          if (S.globaSetting.monitorAudio == "none") {
            (console.warn(
              "[voiceChangerClient] audioMonitorDevice not set for audio monitor.",
            ),
              (me.volume = 0),
              (me.muted = !0));
            return;
          }
          if (
            !(await navigator.mediaDevices.enumerateDevices())
              .filter((xe) => xe.kind == "audiooutput")
              .some((xe) => xe.deviceId == S.globaSetting.monitorAudio)
          ) {
            (console.warn(
              `[voiceChangerClient] audioMonitorDevice ${S.globaSetting.monitorAudio} not found.`,
            ),
              E(
                "error",
                C("common.error_messages.audio_monitor_device_not_found", {
                  device: S.globaSetting.monitorAudio,
                }),
              ),
              (me.volume = 0),
              (me.muted = !0));
            return;
          }
          ((me.srcObject = null), (me.srcObject = _.monitorStream));
          try {
            await me.setSinkId(S.globaSetting.monitorAudio);
          } catch (xe) {
            (console.log("setSinkId is not supported?", xe),
              E(
                "error",
                C("common.error_messages.set_sink_id_not_supported", {
                  error: xe,
                }),
              ));
          }
          ((me.volume = 1), me.paused && me.play());
        })();
      }, [
        _,
        x,
        S.globaSetting.monitorAudioElementId,
        S.globaSetting.monitorAudio,
        E,
        C,
      ]),
      reactExports.useEffect(() => {
        (async () => {
          if (x)
            if (S.globaSetting.isOutputRecording == !0)
              _.startOutputRecording();
            else {
              const me = await _.stopOutputRecording();
              if (me.length > 0) {
                const ye = generateTimestamp();
                downloadAsWav(me, `output_client_${ye}.wav`);
              }
            }
        })();
      }, [_, x, S.globaSetting.isOutputRecording]),
      reactExports.useEffect(() => {
        (async () => {
          x && (S.globaSetting.isStarted == !0 ? _.start() : _.stop());
        })();
      }, [_, x, S.globaSetting.isStarted]),
      reactExports.useEffect(() => {
        (async () => {
          if (!x || !w?.voice_changer_type) return;
          const ye = _.getClientSetting().workletNodeSetting;
          let be = "bulk";
          (w.voice_changer_type == VoiceChangerType.RVC,
            (be = "bulk"),
            (ye.protocol = S.globaSetting.protocol),
            (ye.sendingMode = be),
            await _.updateNodeSetting({ ...ye }),
            await _.resetBuffer());
        })();
      }, [_, x, S.globaSetting.protocol, w?.voice_changer_type]),
      reactExports.useEffect(() => {
        if (!_ || !x) return;
        const me = _.getClientSetting().workletSetting;
        ((me.realtimeOutputStatusEnabled =
          S.globaSetting.realtimeOutputStatusEnabled),
          (me.realtimeOutputStatusSendIntervalSec =
            S.globaSetting.realtimeOutputStatusSendIntervalSec),
          (me.isPassthroughEnabled = S.globaSetting.isPassthrough),
          (me.sendingChunkSec = w?.chunk_sec ?? 0.2),
          _.updateWorkletSetting(me));
      }, [
        _,
        x,
        S.globaSetting.isPassthrough,
        S.globaSetting.realtimeOutputStatusEnabled,
        S.globaSetting.realtimeOutputStatusSendIntervalSec,
        w?.chunk_sec,
      ]),
      reactExports.useEffect(() => {
        x && _.resetBuffer();
      }, [_, x, w?.chunk_sec]),
      reactExports.useEffect(() => {
        if (!x || !H) return;
        const he = setInterval(async () => {
          try {
            const me = await _.getOutputBufferSize(),
              ye = Date.now();
            O((be) => [...be, { timestamp: ye, size: me }].slice(-100));
          } catch (me) {
            console.error("Failed to get output buffer size:", me);
          }
        }, 100);
        return () => clearInterval(he);
      }, [x, H, _]));
    const ie = () => (A.length > 0 ? A[A.length - 1].size : null),
      ne = () => {
        O([]);
      },
      ae = (he) => {
        (ee(he), he || O([]));
      },
      se = () => _.getPendingRequestCount(),
      ce = () => {
        _.abortAllRequests();
      },
      fe = (he) => {
        te.current = he;
      },
      pe = () => {
        _.resetBuffer();
      },
      le = reactExports.useCallback(
        (he) => {
          _.setVoiceChangerStatusListener(he);
        },
        [_],
      );
    return {
      isClientInitialized: x,
      outputBufferSizeHistory: A,
      outputBufferSizeMonitoringEnabled: H,
      getLatestOutputBufferSize: ie,
      clearOutputBufferSizeHistory: ne,
      setOutputBufferSizeMonitoringEnabled: ae,
      getPendingRequestCount: se,
      abortAllRequests: ce,
      setOutputBufferSizeCallback: fe,
      resetOutputBuffer: pe,
      setVoiceChangerStatusListener: le,
    };
  };
