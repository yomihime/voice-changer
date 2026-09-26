// Extracted declaration from ../main-ui.js:96147-96222.
// Navigation/reference excerpt; shared bundle dependencies are NOT imported.
// Edit ../main-ui.js for a runnable change. This is not original TS/TSX source.
const ModelEditDialog = ({ onClose: S }) => {
    const { t: C } = useTranslation(),
      { serverSlotInfos: E } = useAppRoot(),
      w = useTheme(),
      R = reactExports.useMemo(
        () => E.filter((x) => x.voice_changer_type !== null).length,
        [E],
      );
    return reactExports.useMemo(
      () =>
        jsxRuntimeExports.jsx("div", {
          style: {
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(0, 0, 0, 0.5)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1e3,
            width: "100%",
          },
          onClick: S,
          children: jsxRuntimeExports.jsxs("div", {
            style: {
              backgroundColor: w.palette.background.paper,
              borderRadius: "8px",
              padding: "20px",
              width: "90%",
              maxWidth: "800px",
              maxHeight: "80vh",
              overflow: "auto",
              color: w.palette.text.primary,
            },
            onClick: (x) => x.stopPropagation(),
            children: [
              jsxRuntimeExports.jsxs("div", {
                style: {
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  marginBottom: "20px",
                  width: "100%",
                },
                children: [
                  jsxRuntimeExports.jsx("h2", {
                    style: { margin: 0 },
                    children: C("common.model_editor.title"),
                  }),
                  jsxRuntimeExports.jsx(IconButton, {
                    onClick: S,
                    size: "large",
                    sx: { color: w.palette.text.secondary },
                    children: jsxRuntimeExports.jsx(CloseIcon, {}),
                  }),
                ],
              }),
              jsxRuntimeExports.jsx("div", {
                style: { marginBottom: "20px", width: "100%" },
                children: jsxRuntimeExports.jsx("p", {
                  style: { color: w.palette.text.primary },
                  children: C("common.model_editor.slots_in_use", {
                    used: R,
                    total: MAX_SLOT_INDEX,
                  }),
                }),
              }),
              jsxRuntimeExports.jsx(ModelList, {}),
            ],
          }),
        }),
      [S, C, w, R],
    );
  };
