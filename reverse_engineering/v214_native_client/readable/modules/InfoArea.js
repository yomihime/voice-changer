// Extracted declaration from ../main-ui.js:94888-95202.
// Navigation/reference excerpt; shared bundle dependencies are NOT imported.
// Edit ../main-ui.js for a runnable change. This is not original TS/TSX source.
const InfoArea = ({ model: S }) => {
    const { serverSlotInfos: C, updateServerSlotInfo: E } = useAppRoot(),
      w = useTheme(),
      { t: R } = useTranslation(),
      [_, x] = reactExports.useState(""),
      [T, A] = reactExports.useState(""),
      [O, H] = reactExports.useState(!1),
      [ee, te] = reactExports.useState(!1),
      ie = reactExports.useCallback(
        async (fe, pe) => {
          const le = C.find((de) => de.slot_index === fe);
          if (le)
            try {
              (await E({ ...le, name: pe }), H(!1));
            } catch (de) {
              console.error(R("common.model_editor.name_update_failed"), de);
            }
        },
        [C, E, R],
      ),
      ne = reactExports.useCallback(
        async (fe, pe) => {
          const le = C.find((de) => de.slot_index === fe);
          if (le)
            try {
              (await E({ ...le, description: pe }), te(!1));
            } catch (de) {
              console.error(
                R("common.model_editor.description_update_failed"),
                de,
              );
            }
        },
        [C, E, R],
      ),
      ae = reactExports.useMemo(
        () =>
          O
            ? jsxRuntimeExports.jsx("div", {
                children: jsxRuntimeExports.jsxs("div", {
                  style: { display: "flex", gap: "8px", alignItems: "center" },
                  children: [
                    jsxRuntimeExports.jsx("input", {
                      type: "text",
                      value: _,
                      onChange: (fe) => x(fe.target.value),
                      onKeyDown: async (fe) => {
                        fe.key === "Enter"
                          ? await ie(S.slot_index, _)
                          : fe.key === "Escape" && H(!1);
                      },
                      style: {
                        padding: "4px 8px",
                        borderRadius: "4px",
                        border: `1px solid ${w.palette.divider}`,
                        backgroundColor: w.palette.background.default,
                        color: w.palette.text.primary,
                      },
                      autoFocus: !0,
                    }),
                    jsxRuntimeExports.jsx(IconButton, {
                      onClick: async () => {
                        await ie(S.slot_index, _);
                      },
                      color: "default",
                      sx: {
                        height: "32px",
                        minWidth: "64px",
                        px: 2,
                        border: "2px solid",
                        borderColor: "grey.300",
                        borderRadius: "8px",
                        "&:hover": { borderColor: "primary.main" },
                      },
                      children: jsxRuntimeExports.jsx(Stack, {
                        direction: "row",
                        spacing: 1,
                        alignItems: "center",
                        children: jsxRuntimeExports.jsx("span", {
                          style: { fontSize: "14px", whiteSpace: "nowrap" },
                          children: R("common.model_editor.save"),
                        }),
                      }),
                    }),
                    jsxRuntimeExports.jsx(IconButton, {
                      onClick: () => H(!1),
                      color: "default",
                      sx: {
                        height: "32px",
                        minWidth: "64px",
                        px: 2,
                        border: "2px solid",
                        borderColor: "grey.300",
                        borderRadius: "8px",
                        "&:hover": { borderColor: "primary.main" },
                      },
                      children: jsxRuntimeExports.jsx(Stack, {
                        direction: "row",
                        spacing: 1,
                        alignItems: "center",
                        children: jsxRuntimeExports.jsx("span", {
                          style: { fontSize: "14px", whiteSpace: "nowrap" },
                          children: R("common.model_editor.cancel"),
                        }),
                      }),
                    }),
                  ],
                }),
              })
            : jsxRuntimeExports.jsx("div", {
                onClick: () => {
                  ee || (H(!0), x(S.name || ""));
                },
                style: {
                  cursor: ee ? "default" : "pointer",
                  color: w.palette.text.primary,
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap",
                },
                children: S.name,
              }),
        [
          O,
          ee,
          S.name,
          S.slot_index,
          _,
          x,
          R,
          w.palette.background.default,
          w.palette.divider,
          w.palette.text.primary,
          ie,
        ],
      ),
      se = reactExports.useMemo(
        () =>
          jsxRuntimeExports.jsx("div", {
            children: ee
              ? jsxRuntimeExports.jsxs("div", {
                  style: {
                    display: "flex",
                    gap: "8px",
                    alignItems: "center",
                    marginTop: "8px",
                  },
                  children: [
                    jsxRuntimeExports.jsx("input", {
                      type: "text",
                      value: T,
                      onChange: (fe) => A(fe.target.value),
                      onKeyDown: async (fe) => {
                        fe.key === "Enter"
                          ? await ne(S.slot_index, T)
                          : fe.key === "Escape" && te(!1);
                      },
                      style: {
                        padding: "4px 8px",
                        borderRadius: "4px",
                        border: `1px solid ${w.palette.divider}`,
                        backgroundColor: w.palette.background.default,
                        color: w.palette.text.primary,
                        width: "100%",
                      },
                      autoFocus: !0,
                    }),
                    jsxRuntimeExports.jsx(IconButton, {
                      onClick: async () => {
                        await ne(S.slot_index, T);
                      },
                      color: "default",
                      sx: {
                        height: "32px",
                        minWidth: "64px",
                        px: 2,
                        border: "2px solid",
                        borderColor: "grey.300",
                        borderRadius: "8px",
                        "&:hover": { borderColor: "primary.main" },
                      },
                      children: jsxRuntimeExports.jsx(Stack, {
                        direction: "row",
                        spacing: 1,
                        alignItems: "center",
                        children: jsxRuntimeExports.jsx("span", {
                          style: { fontSize: "14px", whiteSpace: "nowrap" },
                          children: R("common.model_editor.save"),
                        }),
                      }),
                    }),
                    jsxRuntimeExports.jsx(IconButton, {
                      onClick: () => te(!1),
                      color: "default",
                      sx: {
                        height: "32px",
                        minWidth: "64px",
                        px: 2,
                        border: "2px solid",
                        borderColor: "grey.300",
                        borderRadius: "8px",
                        "&:hover": { borderColor: "primary.main" },
                      },
                      children: jsxRuntimeExports.jsx(Stack, {
                        direction: "row",
                        spacing: 1,
                        alignItems: "center",
                        children: jsxRuntimeExports.jsx("span", {
                          style: { fontSize: "14px", whiteSpace: "nowrap" },
                          children: R("common.model_editor.cancel"),
                        }),
                      }),
                    }),
                  ],
                })
              : jsxRuntimeExports.jsx("div", {
                  onClick: () => {
                    O || (te(!0), A(S.description || ""));
                  },
                  style: {
                    fontSize: "14px",
                    color: w.palette.text.secondary,
                    marginTop: "4px",
                    cursor: O ? "default" : "pointer",
                  },
                  children:
                    S.description && S.description.length > 0
                      ? S.description
                      : R("common.model_editor.no_description"),
                }),
          }),
        [
          ee,
          O,
          S.description,
          S.slot_index,
          T,
          A,
          R,
          w.palette.background.default,
          w.palette.divider,
          w.palette.text.primary,
          w.palette.text.secondary,
          ne,
        ],
      );
    return reactExports.useMemo(
      () =>
        jsxRuntimeExports.jsxs("div", {
          style: { width: "60%" },
          children: [
            jsxRuntimeExports.jsxs("div", {
              style: {
                display: "flex",
                fontWeight: "bold",
                marginBottom: "4px",
                color: w.palette.text.primary,
                gap: "1rem",
              },
              children: [
                jsxRuntimeExports.jsx("span", {
                  children: R("common.model_editor.slot", {
                    number: S.slot_index + 1,
                  }),
                }),
                jsxRuntimeExports.jsx("span", {
                  style: {
                    display: "flex",
                    alignItems: "center",
                    gap: "0.3rem",
                  },
                  children:
                    S.voice_changer_type != null
                      ? jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, {
                          children: [
                            jsxRuntimeExports.jsx(TagIcon, {
                              label: S.voice_changer_type,
                            }),
                            S.voice_changer_type === "RVC" &&
                              jsxRuntimeExports.jsx(TagIcon, {
                                label:
                                  (S.is_onnx ? "onnx" : "torch") +
                                  " " +
                                  S.version,
                              }),
                            S.voice_changer_type === "RVC" &&
                              jsxRuntimeExports.jsx(TagIcon, {
                                label: S.is_f0 ? "f0" : "non-f0",
                              }),
                            S.voice_changer_type === "RVC" &&
                              jsxRuntimeExports.jsx(TagIcon, {
                                label: S.embedder,
                              }),
                          ],
                        })
                      : null,
                }),
              ],
            }),
            jsxRuntimeExports.jsx("div", {
              children:
                S.voice_changer_type != null
                  ? jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, {
                      children: [ae, se],
                    })
                  : jsxRuntimeExports.jsx("div", {
                      style: { color: w.palette.text.secondary },
                      children: R("common.model_editor.empty_slot"),
                    }),
            }),
          ],
        }),
      [S, R, w, ae, se],
    );
  };
