// Extracted declaration from ../main-ui.js:96652-96722.
// Navigation/reference excerpt; shared bundle dependencies are NOT imported.
// Edit ../main-ui.js for a runnable change. This is not original TS/TSX source.
const HeaderArea = () => {
    const { currentSlotInfo: S } = useAppRoot(),
      { t: C } = useTranslation();
    return reactExports.useMemo(
      () =>
        jsxRuntimeExports.jsxs("div", {
          style: { padding: "10px", marginBottom: "20px", width: "100%" },
          children: [
            jsxRuntimeExports.jsxs("div", {
              style: {
                fontSize: "1.2em",
                fontWeight: "bold",
                marginBottom: "8px",
              },
              children: [
                S ? `${S.slot_index + 1}. ` : "",
                S?.name || C("common.model.not_selected"),
                S?.voice_changer_type != null
                  ? jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, {
                      children: [
                        jsxRuntimeExports.jsx(TagIcon, {
                          label: S.voice_changer_type,
                        }),
                        S.voice_changer_type === "RVC" &&
                          jsxRuntimeExports.jsx(TagIcon, {
                            label:
                              (S.is_onnx ? "onnx" : "torch") + " " + S.version,
                          }),
                        S.voice_changer_type === "RVC" &&
                          jsxRuntimeExports.jsx(TagIcon, {
                            label: S.is_f0 ? "f0" : "non-f0",
                          }),
                        S.voice_changer_type === "RVC" &&
                          jsxRuntimeExports.jsx(TagIcon, { label: S.embedder }),
                      ],
                    })
                  : null,
              ],
            }),
            S?.description &&
              jsxRuntimeExports.jsx("div", {
                style: {
                  width: "100%",
                  padding: "10px",
                  backgroundColor: "#f5f5f5",
                  borderRadius: "4px",
                  fontSize: "14px",
                  color: "darkslategrey",
                  maxHeight: "100px",
                  overflowY: "auto",
                },
                children: S.description,
              }),
            S?.voice_changer_type === "Beatrice_v2" &&
              jsxRuntimeExports.jsx("div", {
                children: jsxRuntimeExports.jsxs("div", {
                  children: [
                    jsxRuntimeExports.jsx("span", {
                      children: C("common.copyright.beatrice_lib_license"),
                    }),
                    jsxRuntimeExports.jsx("span", {
                      children: C("common.copyright.beatrice_lib_license2"),
                    }),
                  ],
                }),
              }),
          ],
        }),
      [S, C],
    );
  };
