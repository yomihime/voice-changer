// Extracted declaration from ../main-ui.js:101327-101362.
// Navigation/reference excerpt; shared bundle dependencies are NOT imported.
// Edit ../main-ui.js for a runnable change. This is not original TS/TSX source.
const ControlArea = () => {
    const { currentSlotInfo: S } = useAppRoot();
    return reactExports.useMemo(
      () =>
        S == null
          ? jsxRuntimeExports.jsx(jsxRuntimeExports.Fragment, {})
          : jsxRuntimeExports.jsxs("div", {
              style: {
                display: "flex",
                flexDirection: "column",
                marginBottom: "30px",
                border: "1px solid #eee",
                borderRadius: "8px",
                padding: "20px",
                boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
                width: "100%",
              },
              children: [
                jsxRuntimeExports.jsx(HeaderArea, {}),
                jsxRuntimeExports.jsxs("div", {
                  style: { display: "flex", gap: "10px", width: "100%" },
                  children: [
                    jsxRuntimeExports.jsxs("div", {
                      children: [
                        jsxRuntimeExports.jsx(PortraitArea, {}),
                        jsxRuntimeExports.jsx(PerformanceArea, {}),
                      ],
                    }),
                    jsxRuntimeExports.jsx(Controls, {}),
                  ],
                }),
              ],
            }),
      [S],
    );
  };
