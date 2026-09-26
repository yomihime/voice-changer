// Extracted declaration from ../main-ui.js:100885-100911.
// Navigation/reference excerpt; shared bundle dependencies are NOT imported.
// Edit ../main-ui.js for a runnable change. This is not original TS/TSX source.
const Controls = () => {
    const { currentSlotInfo: S } = useAppRoot();
    return reactExports.useMemo(
      () =>
        S == null
          ? null
          : jsxRuntimeExports.jsx("div", {
              style: { flex: 1, width: "calc(100% - 340px)" },
              children: jsxRuntimeExports.jsxs("div", {
                style: {
                  display: "flex",
                  flexDirection: "column",
                  gap: "0px",
                  justifyContent: "center",
                  width: "100%",
                },
                children: [
                  jsxRuntimeExports.jsx(MainControls, {}),
                  jsxRuntimeExports.jsx(InputControls, {}),
                  jsxRuntimeExports.jsx(VolumeControls, {}),
                  jsxRuntimeExports.jsx(VoiceControls, {}),
                ],
              }),
            }),
      [S],
    );
  };
