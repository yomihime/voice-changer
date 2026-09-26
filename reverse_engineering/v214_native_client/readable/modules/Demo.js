// Extracted declaration from ../main-ui.js:102350-102394.
// Navigation/reference excerpt; shared bundle dependencies are NOT imported.
// Edit ../main-ui.js for a runnable change. This is not original TS/TSX source.
function Demo() {
  const { edition: S, version: C } = useAppRoot(),
    { setOutputAudioElementId: E, setMonitorAudioElementId: w } = useAppState();
  return (
    reactExports.useEffect(() => {
      (E(AUDIO_ELEMENT_FOR_PLAY_RESULT), w(AUDIO_ELEMENT_FOR_PLAY_MONITOR));
    }, []),
    jsxRuntimeExports.jsxs("div", {
      style: {
        maxWidth: "1200px",
        margin: "0 auto",
        padding: "20px",
        width: "100%",
      },
      children: [
        jsxRuntimeExports.jsxs("h2", {
          children: [
            "Realtime Voice Changer Client",
            " ",
            jsxRuntimeExports.jsxs("span", {
              style: { fontSize: "1rem", color: "gray" },
              children: ["ver ", C, " ", S],
            }),
          ],
        }),
        jsxRuntimeExports.jsx(LinkArea, {}),
        jsxRuntimeExports.jsx(ModelSelector, {}),
        jsxRuntimeExports.jsx(ControlArea, {}),
        jsxRuntimeExports.jsx(AdvancedArea, {}),
        jsxRuntimeExports.jsxs("div", {
          children: [
            jsxRuntimeExports.jsx("audio", {
              hidden: !0,
              id: AUDIO_ELEMENT_FOR_PLAY_RESULT,
            }),
            jsxRuntimeExports.jsx("audio", {
              hidden: !0,
              id: AUDIO_ELEMENT_FOR_PLAY_MONITOR,
            }),
          ],
        }),
      ],
    })
  );
}
