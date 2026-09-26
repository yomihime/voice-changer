// Extracted declaration from ../main-ui.js:96947-97235.
// Navigation/reference excerpt; shared bundle dependencies are NOT imported.
// Edit ../main-ui.js for a runnable change. This is not original TS/TSX source.
const PortraitArea = () => {
    const { currentSlotInfo: S, updateServerSlotInfo: C } = useAppRoot(),
      { setOutputBufferSizeCallback: E } = useAppState(),
      [w, R] = reactExports.useState(!1),
      { t: _ } = useTranslation();
    reactExports.useEffect(() => {
      const ie = document.getElementById("outputBufferSize");
      E((ne) => {
        ie != null && (ie.textContent = ne.toString());
      });
    }, [E]);
    const x = reactExports.useCallback(
        (ie) => {
          if (S == null || S.voice_changer_type !== "Beatrice_v2") return null;
          const ne = S,
            ae = ne.model_info.voice[ie],
            ce = ne.toml_file.replace(/\\\\/g, "/").replace(/\\/g, "/");
          return (
            ce.substring(0, ce.lastIndexOf("/")) +
            "/" +
            ae.portrait.path.split(/[/\\]/).pop()
          );
        },
        [S],
      ),
      T = reactExports.useMemo(
        () =>
          S == null
            ? null
            : S.voice_changer_type === "RVC"
              ? S.icon_file != null
                ? "model_dir/" +
                  S.slot_index +
                  "/" +
                  S.icon_file.split(/[/\\]/).pop()
                : "./assets/icons/human.png"
              : S.voice_changer_type === "Beatrice_v2"
                ? x(S.dst_id)
                : (log$1(
                    "error",
                    logPrefix$4,
                    "currentSlotInfo.voice_changer_type is not supported",
                  ),
                  null),
        [S, x],
      ),
      A = reactExports.useMemo(() => {
        if (S == null || S.voice_changer_type === "RVC") return null;
        if (S.voice_changer_type === "Beatrice_v2") {
          const ie = S;
          return ie.model_info.voice[ie.dst_id];
        }
        return (
          log$1(
            "error",
            logPrefix$4,
            "currentSlotInfo.voice_changer_type is not supported",
          ),
          null
        );
      }, [S]),
      O = reactExports.useMemo(() => {
        if (S == null || S.voice_changer_type === "RVC") return null;
        if (S.voice_changer_type === "Beatrice_v2") {
          const ie = S,
            ae = Object.values(ie.model_info.voice).map((se, ce) => {
              const fe = x(ce);
              return jsxRuntimeExports.jsxs(
                MenuItem,
                {
                  value: ce,
                  sx: {
                    display: "flex",
                    alignItems: "center",
                    gap: "12px",
                    padding: "8px 12px",
                    "&:hover": { backgroundColor: "action.hover" },
                  },
                  children: [
                    jsxRuntimeExports.jsx("div", {
                      style: {
                        width: "40px",
                        height: "40px",
                        borderRadius: "4px",
                        overflow: "hidden",
                        flexShrink: 0,
                      },
                      children: fe
                        ? jsxRuntimeExports.jsx("img", {
                            src: fe,
                            alt: se.name,
                            style: {
                              width: "100%",
                              height: "100%",
                              objectFit: "cover",
                            },
                          })
                        : jsxRuntimeExports.jsx("div", {
                            style: {
                              width: "100%",
                              height: "100%",
                              backgroundColor: "action.hover",
                              display: "flex",
                              alignItems: "center",
                              justifyContent: "center",
                              fontSize: "20px",
                              color: "text.secondary",
                            },
                            children: se.name.charAt(0),
                          }),
                    }),
                    jsxRuntimeExports.jsxs("div", {
                      style: {
                        display: "flex",
                        alignItems: "center",
                        gap: "8px",
                        flex: 1,
                      },
                      children: [
                        jsxRuntimeExports.jsx("span", {
                          style: { fontWeight: 500 },
                          children: se.name,
                        }),
                        jsxRuntimeExports.jsxs("span", {
                          style: { color: "#666", fontSize: "0.85em" },
                          children: ["(", se.average_pitch, ")"],
                        }),
                      ],
                    }),
                  ],
                },
                ce,
              );
            });
          return jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, {
            children: [
              jsxRuntimeExports.jsx("div", {
                style: {
                  display: "flex",
                  alignItems: "center",
                  marginBottom: "10px",
                },
                children: jsxRuntimeExports.jsx("label", {
                  style: { display: "block", fontWeight: "bold", flex: 1 },
                  children: _("common.voice.character"),
                }),
              }),
              jsxRuntimeExports.jsx(FormControl, {
                fullWidth: !0,
                children: jsxRuntimeExports.jsx(Select, {
                  value: ie.dst_id,
                  onChange: async (se) => {
                    const ce = se.target.value,
                      fe = { ...ie, dst_id: ce };
                    await C(fe);
                  },
                  sx: {
                    backgroundColor: "background.paper",
                    "& .MuiOutlinedInput-notchedOutline": {
                      borderColor: "divider",
                    },
                    "&:hover .MuiOutlinedInput-notchedOutline": {
                      borderColor: "action.active",
                    },
                    "&.Mui-focused .MuiOutlinedInput-notchedOutline": {
                      borderColor: "primary.main",
                    },
                    borderRadius: "8px",
                    "& .MuiSelect-select": {
                      padding: "12px",
                      display: "flex",
                      alignItems: "center",
                      gap: "12px",
                    },
                  },
                  MenuProps: {
                    PaperProps: {
                      sx: {
                        borderRadius: "8px",
                        marginTop: "8px",
                        boxShadow: "0 4px 20px rgba(0,0,0,0.1)",
                      },
                    },
                    TransitionProps: { timeout: { enter: 10, exit: 5 } },
                  },
                  children: ae,
                }),
              }),
            ],
          });
        }
        return null;
      }, [S, x, C, _]),
      H = reactExports.useMemo(
        () =>
          S == null || S.voice_changer_type === "RVC"
            ? null
            : jsxRuntimeExports.jsx("div", {
                style: {
                  width: "320px",
                  padding: "10px",
                  backgroundColor: "#f5f5f5",
                  borderRadius: "4px",
                  fontSize: "14px",
                  color: "darkslategrey",
                  maxHeight: "100px",
                  overflowY: "auto",
                },
                children:
                  A != null ? A.description : _("common.voice.no_description"),
              }),
        [S, A, _],
      ),
      ee = reactExports.useMemo(
        () =>
          S == null || S.voice_changer_type === "RVC"
            ? null
            : jsxRuntimeExports.jsx("div", {
                style: {
                  marginTop: "8px",
                  display: "flex",
                  justifyContent: "flex-start",
                },
                children: jsxRuntimeExports.jsx(Tooltip, {
                  title: _("common.voice.edit_tooltip"),
                  children: jsxRuntimeExports.jsx(IconButton, {
                    size: "small",
                    onClick: () => R(!0),
                    children: jsxRuntimeExports.jsx(Edit, {
                      fontSize: "small",
                    }),
                  }),
                }),
              }),
        [S, _, R],
      );
    return reactExports.useMemo(
      () =>
        S == null
          ? jsxRuntimeExports.jsx(jsxRuntimeExports.Fragment, {})
          : jsxRuntimeExports.jsxs("div", {
              style: { display: "flex", flexDirection: "column", gap: "20px" },
              children: [
                O,
                jsxRuntimeExports.jsx("div", {
                  style: {
                    width: "320px",
                    height: "320px",
                    borderRadius: "8px",
                    overflow: "hidden",
                    border: "1px solid #eee",
                    marginRight: "20px",
                    flexShrink: 0,
                  },
                  children: T
                    ? jsxRuntimeExports.jsx("img", {
                        src: T,
                        style: {
                          width: "100%",
                          height: "100%",
                          objectFit: "scale-down",
                        },
                      })
                    : jsxRuntimeExports.jsx("div", {
                        style: {
                          width: "100%",
                          height: "100%",
                          backgroundColor: "action.hover",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          fontSize: "120px",
                          fontWeight: "bold",
                          color: "text.secondary",
                        },
                        children: A?.name?.charAt(0).toUpperCase(),
                      }),
                }),
                H,
                ee,
                jsxRuntimeExports.jsx(VoiceCharacterEditDialog, {
                  open: w,
                  onClose: () => R(!1),
                }),
              ],
            }),
      [S, w, T, O, H, ee, A?.name],
    );
  };
