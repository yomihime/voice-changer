// Extracted declaration from ../main-ui.js:102418-102504.
// Navigation/reference excerpt; shared bundle dependencies are NOT imported.
// Edit ../main-ui.js for a runnable change. This is not original TS/TSX source.
const useAudioConfig = (S) => {
    const { t: C } = useTranslation(),
      [E, w] = reactExports.useState(null),
      [R, _] = reactExports.useState([]),
      [x, T] = reactExports.useState([]),
      A = reactExports.useRef(!1);
    reactExports.useEffect(() => {
      const ee = async () => {
          if (A.current == !0) return;
          A.current = !0;
          const ae =
            new URL(window.location.href).searchParams.get("sample_rate") ||
            null;
          let se;
          (ae
            ? ae == "default"
              ? (log$1("info", logPrefix$2, "Sample rate: default"),
                (se = new AudioContext()))
              : (log$1("info", logPrefix$2, `Sample rate: ${ae}`),
                (se = new AudioContext({ sampleRate: Number(ae) })))
            : (log$1("info", logPrefix$2, "Sample rate: default(48000)"),
              (se = new AudioContext({ sampleRate: 48e3 }))),
            await O(),
            log$1("info", logPrefix$2, se),
            w(se),
            document.removeEventListener("touchstart", te),
            document.removeEventListener("mousedown", te));
        },
        te = () => {
          setTimeout(() => {
            ee();
          }, S.createAudioContextDelay);
        };
      (document.addEventListener("touchstart", te, !1),
        document.addEventListener("mousedown", te, !1));
    }, []);
    const O = async () => {
      try {
        (await navigator.mediaDevices.getUserMedia({ video: !1, audio: !0 }))
          .getTracks()
          .forEach((ae) => {
            ae.stop();
          });
      } catch (ne) {
        console.warn("Enumerate device error::", ne);
      }
      const ee = await navigator.mediaDevices.enumerateDevices(),
        te = ee.filter((ne) => ne.kind == "audioinput");
      (te.push({
        deviceId: "none",
        groupId: "none",
        kind: "audioinput",
        label: C("common.controls.device_none"),
        toJSON: () => {},
      }),
        te.push({
          deviceId: "file",
          groupId: "file",
          kind: "audioinput",
          label: C("common.controls.device_file"),
          toJSON: () => {},
        }),
        te.push({
          deviceId: "screen",
          groupId: "screen",
          kind: "audioinput",
          label: C("common.controls.device_system"),
          toJSON: () => {},
        }),
        _(te));
      const ie = ee.filter((ne) => ne.kind == "audiooutput");
      (ie.push({
        deviceId: "none",
        groupId: "none",
        kind: "audiooutput",
        label: C("common.controls.device_none"),
        toJSON: () => {},
      }),
        T(ie));
    };
    return {
      audioContext: E,
      audioInputs: R,
      audioOutputs: x,
      reloadDeviceInfo: O,
    };
  };
