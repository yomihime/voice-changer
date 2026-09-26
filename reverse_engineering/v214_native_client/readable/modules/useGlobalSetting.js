// Extracted declaration from ../main-ui.js:98988-99126.
// Navigation/reference excerpt; shared bundle dependencies are NOT imported.
// Edit ../main-ui.js for a runnable change. This is not original TS/TSX source.
const useGlobalSetting = () => {
    const [S, C] = reactExports.useState(!1),
      [E, w] = reactExports.useState("light"),
      [R, _] = reactExports.useState("default"),
      [x, T] = reactExports.useState("default"),
      [A, O] = reactExports.useState("default"),
      [H, ee] = reactExports.useState("default"),
      [te, ie] = reactExports.useState(null),
      [ne, ae] = reactExports.useState(null),
      [se, ce] = reactExports.useState(InputAudioType.MICROPHONE),
      [fe, pe] = reactExports.useState(1),
      [le, de] = reactExports.useState(1),
      [he, me] = reactExports.useState(0),
      [ye, be] = reactExports.useState("ja"),
      [ve, xe] = reactExports.useState(!1),
      [Ce, _e] = reactExports.useState(null),
      [Be, Ve] = reactExports.useState(!1),
      [ke, Le] = reactExports.useState(!1),
      [qe, ze] = reactExports.useState(!1),
      [Ae, Ne] = reactExports.useState(!1),
      [We, Ie] = reactExports.useState(!1),
      [$e, Me] = reactExports.useState(!0),
      [Ge, er] = reactExports.useState(2),
      [Ht, rr] = reactExports.useState("rest"),
      [Jt, Kt] = reactExports.useState(!1),
      [dr, or] = reactExports.useState(!0);
    return (
      reactExports.useEffect(() => {
        (async () => {
          try {
            const pr = await loadSettings();
            pr &&
              (w(pr.displayColorMode),
              pe(pr.nodeInputGain),
              de(pr.nodeOutputGain),
              me(pr.nodeMonitorGain),
              _(pr.selectedInputAudioDeviceId),
              O(pr.outputAudio),
              ee(pr.monitorAudio),
              ce(pr.inputAudioType),
              be(pr.selectedLanguage),
              ze(pr.enableEchoCancellation ?? !1),
              Ne(pr.enableNoiseSuppression ?? !1),
              Ie(pr.enableNoiseSuppression2 ?? !1),
              Me(pr.realtimeOutputStatusEnabled ?? !1),
              er(pr.realtimeOutputStatusSendIntervalSec ?? 10),
              rr(pr.protocol ?? "rest"),
              Kt(pr.recordForAnalysis ?? !1),
              or(pr.showSampleAudioButton ?? !0));
          } catch (pr) {
            console.error("Failed to load settings:", pr);
          } finally {
            C(!0);
          }
        })();
      }, []),
      reactExports.useEffect(() => {
        if (!S) return;
        (async () => {
          try {
            await saveSettings({
              displayColorMode: E,
              nodeInputGain: fe,
              nodeOutputGain: le,
              nodeMonitorGain: he,
              selectedInputAudioDeviceId: R,
              outputAudio: A,
              monitorAudio: H,
              inputAudioType: se,
              selectedLanguage: ye,
              enableEchoCancellation: qe,
              enableNoiseSuppression: Ae,
              enableNoiseSuppression2: We,
              realtimeOutputStatusEnabled: $e,
              realtimeOutputStatusSendIntervalSec: Ge,
              protocol: Ht,
              recordForAnalysis: Jt,
              showSampleAudioButton: dr,
            });
          } catch (pr) {
            console.error("Failed to save settings:", pr);
          }
        })();
      }, [S, E, fe, le, he, R, A, H, se, ye, qe, Ae, We, $e, Ge, Ht, Jt, dr]),
      reactExports.useEffect(() => {
        T(se === "microphone" ? R : "none");
      }, [se, R]),
      {
        displayColorMode: E,
        setDisplayColorMode: w,
        selectedLanguage: ye,
        setSelectedLanguage: be,
        selectedInputAudioDeviceId: R,
        setSelectedInputAudioDeviceId: _,
        inputAudio: x,
        setInputAudio: T,
        inputAudioType: se,
        setInputAudioType: ce,
        outputAudio: A,
        setOutputAudio: O,
        monitorAudio: H,
        setMonitorAudio: ee,
        outputAudioElementId: te,
        setOutputAudioElementId: ie,
        monitorAudioElementId: ne,
        setMonitorAudioElementId: ae,
        nodeInputGain: fe,
        setNodeInputGain: pe,
        nodeOutputGain: le,
        setNodeOutputGain: de,
        nodeMonitorGain: he,
        setNodeMonitorGain: me,
        enableEchoCancellation: qe,
        setEnableEchoCancellation: ze,
        enableNoiseSuppression: Ae,
        setEnableNoiseSuppression: Ne,
        enableNoiseSuppression2: We,
        setEnableNoiseSuppression2: Ie,
        isOutputRecording: ve,
        setIsOutputRecording: xe,
        outputRecord: Ce,
        setOutputRecord: _e,
        isStarted: Be,
        setIsStarted: Ve,
        protocol: Ht,
        setProtocol: rr,
        isPassthrough: ke,
        setIsPassthrough: Le,
        realtimeOutputStatusEnabled: $e,
        setRealtimeOutputStatusEnabled: Me,
        recordForAnalysis: Jt,
        setRecordForAnalysis: Kt,
        showSampleAudioButton: dr,
        setShowSampleAudioButton: or,
        realtimeOutputStatusSendIntervalSec: Ge,
        setRealtimeOutputStatusSendIntervalSec: er,
      }
    );
  };
