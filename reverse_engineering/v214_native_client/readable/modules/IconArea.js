// Extracted declaration from ../main-ui.js:94723-94869.
// Navigation/reference excerpt; shared bundle dependencies are NOT imported.
// Edit ../main-ui.js for a runnable change. This is not original TS/TSX source.
const IconArea = ({ model: S }) => {
    const C = useTheme(),
      { t: E } = useTranslation(),
      { uploadIconFile: w, triggerToast: R } = useAppRoot(),
      _ = reactExports.useRef(null),
      x = reactExports.useCallback(
        (O) => {
          (O.stopPropagation(),
            S?.name &&
              _.current &&
              ((_.current.value = ""), _.current.click()));
        },
        [S?.name],
      ),
      T = reactExports.useCallback(
        async (O) => {
          const H = O.target.files?.[0];
          if (H && S?.slot_index !== void 0)
            try {
              (await w(S.slot_index, H, () => {}),
                R("success", E("common.model_editor.icon_upload_success")));
            } catch {
              R("error", E("common.model_editor.icon_upload_failed"));
            }
        },
        [S?.slot_index, w, R, E],
      );
    return reactExports.useMemo(() => {
      const O = S.icon_file
        ? "model_dir/" + S.slot_index + "/" + S.icon_file.split(/[/\\]/).pop()
        : "./assets/icons/human.png";
      return jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, {
        children: [
          jsxRuntimeExports.jsx("input", {
            type: "file",
            accept: "image/*",
            style: { display: "none" },
            ref: _,
            onChange: T,
          }),
          jsxRuntimeExports.jsx("div", {
            style: {
              width: "64px",
              height: "64px",
              flexShrink: 0,
              borderRadius: "8px",
              overflow: "hidden",
              backgroundColor:
                C.palette.mode === "light"
                  ? "#f0f2f5"
                  : C.palette.background.default,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              cursor: S?.name ? "pointer" : "default",
              position: "relative",
            },
            onClick: x,
            children:
              S.voice_changer_type != null
                ? jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, {
                    children: [
                      S.icon_file
                        ? jsxRuntimeExports.jsx("img", {
                            src: O,
                            alt: S.name,
                            style: {
                              width: "100%",
                              height: "100%",
                              objectFit: "cover",
                            },
                          })
                        : jsxRuntimeExports.jsx("div", {
                            style: {
                              fontSize: "24px",
                              fontWeight: "bold",
                              color: C.palette.text.secondary,
                            },
                            children: S.name.charAt(0).toUpperCase(),
                          }),
                      jsxRuntimeExports.jsx("div", {
                        style: {
                          position: "absolute",
                          top: 0,
                          left: 0,
                          right: 0,
                          bottom: 0,
                          backgroundColor: "rgba(0, 0, 0, 0.3)",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          opacity: 0,
                          transition: "opacity 0.2s",
                        },
                        onMouseEnter: (H) => {
                          H.target.style.opacity = "1";
                        },
                        onMouseLeave: (H) => {
                          H.target.style.opacity = "0";
                        },
                        children: jsxRuntimeExports.jsxs("svg", {
                          width: "24",
                          height: "24",
                          viewBox: "0 0 24 24",
                          fill: "none",
                          stroke: "currentColor",
                          strokeWidth: "2",
                          children: [
                            jsxRuntimeExports.jsx("path", {
                              d: "M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4",
                            }),
                            jsxRuntimeExports.jsx("polyline", {
                              points: "17 8 12 3 7 8",
                            }),
                            jsxRuntimeExports.jsx("line", {
                              x1: "12",
                              y1: "3",
                              x2: "12",
                              y2: "15",
                            }),
                          ],
                        }),
                      }),
                    ],
                  })
                : jsxRuntimeExports.jsx("div", {
                    style: {
                      fontSize: "24px",
                      color: C.palette.text.secondary,
                    },
                    children: "-",
                  }),
          }),
        ],
      });
    }, [
      S.name,
      S.icon_file,
      S.slot_index,
      S.voice_changer_type,
      C.palette.mode,
      C.palette.text.secondary,
      C.palette.background.default,
      T,
      x,
    ]);
  };
