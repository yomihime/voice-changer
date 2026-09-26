// Extracted declaration from ../main-ui.js:95208-95602.
// Navigation/reference excerpt; shared bundle dependencies are NOT imported.
// Edit ../main-ui.js for a runnable change. This is not original TS/TSX source.
const ModelUploadDialog = (S) => {
    const { onClose: C } = S,
      { t: E } = useTranslation(),
      w = useTheme(),
      [R, _] = React.useState("RVC"),
      [x, T] = React.useState(null),
      [A, O] = React.useState(null),
      [H, ee] = React.useState(null),
      te = React.useRef(null),
      ie = React.useRef(null),
      ne = React.useRef(null),
      ae = useAppRoot(),
      [se, ce] = React.useState(!1),
      [fe, pe] = React.useState(0),
      [le, de] = reactExports.useState(!1),
      he = reactExports.useCallback(async () => {
        if (!S.slotIndex && S.slotIndex !== 0) return;
        const be = [];
        if (R === VoiceChangerType.RVC) {
          if (!x) {
            alert(E("common.model_upload.select_model_file_error"));
            return;
          }
          (be.push({ kind: "rvcModel", file: x }),
            A && be.push({ kind: "rvcIndex", file: A }));
        } else if (R === VoiceChangerType.Beatrice_v2) {
          if (!H) {
            alert(E("common.model_upload.select_zip_error"));
            return;
          }
          be.push({ kind: "beatriceV2Zip", file: H });
        } else {
          alert(E("common.model_upload.unsupported_voice_changer_type"));
          return;
        }
        (ce(!0), pe(0));
        try {
          await ae.uploadModelFile(S.slotIndex, R, be, null, (ve, xe) => {
            (pe(ve), xe && (pe(100), ce(!1), de(!0)));
          });
        } catch (ve) {
          ce(!1);
          let xe = E("common.model_upload.upload_error");
          if (
            (console.log(xe, ve),
            typeof ve == "object" &&
              ve !== null &&
              "reason" in ve &&
              "detail" in ve &&
              "action" in ve)
          ) {
            const Ce = ve;
            ae.triggerToast(
              "error",
              jsxRuntimeExports.jsxs("div", {
                style: {
                  display: "flex",
                  flexDirection: "column",
                  gap: "10px",
                },
                children: [
                  jsxRuntimeExports.jsx("div", {
                    style: { fontWeight: "bold", fontSize: "1rem" },
                    children: xe,
                  }),
                  jsxRuntimeExports.jsx("div", {
                    style: { fontSize: "0.9rem" },
                    children: Ce.reason ?? "",
                  }),
                  jsxRuntimeExports.jsxs("div", {
                    style: { fontSize: "0.9rem" },
                    children: [" ", Ce.detail ?? "", " "],
                  }),
                  jsxRuntimeExports.jsx("div", {
                    style: { fontSize: "0.9rem" },
                    children: Ce.action ?? "",
                  }),
                ],
              }),
            );
            return;
          } else
            (typeof ve == "object" &&
              ve &&
              "message" in ve &&
              typeof ve.message == "string" &&
              (xe += ve.message),
              ae.triggerToast("error", xe));
        }
      }, [S.slotIndex, R, x, A, H, ae, E]),
      me = reactExports.useCallback(() => {
        (de(!1), C());
      }, [C]),
      ye = reactExports.useMemo(
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
            },
            onClick: C,
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
              onClick: (be) => be.stopPropagation(),
              children: [
                jsxRuntimeExports.jsxs("div", {
                  style: {
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    marginBottom: "20px",
                  },
                  children: [
                    jsxRuntimeExports.jsx("h2", {
                      style: { margin: 0 },
                      children: E("common.model_upload.title"),
                    }),
                    jsxRuntimeExports.jsx(IconButton, {
                      onClick: C,
                      size: "large",
                      sx: { color: w.palette.text.secondary },
                      children: jsxRuntimeExports.jsx(CloseIcon, {}),
                    }),
                  ],
                }),
                jsxRuntimeExports.jsx("div", {
                  style: {
                    marginBottom: "20px",
                    color: w.palette.text.primary,
                  },
                  children: E("common.model_upload.slot_info", {
                    slotNumber: (S.slotIndex ?? 0) + 1,
                  }),
                }),
                jsxRuntimeExports.jsxs(FormControl, {
                  fullWidth: !0,
                  sx: { marginBottom: "20px" },
                  children: [
                    jsxRuntimeExports.jsx(InputLabel, {
                      id: "voice-changer-type-label",
                      children: E("common.model_upload.voice_changer_type"),
                    }),
                    jsxRuntimeExports.jsx(Select, {
                      labelId: "voice-changer-type-label",
                      value: R,
                      label: E("common.model_upload.voice_changer_type"),
                      onChange: (be) => {
                        be.target.value === VoiceChangerType.RVC
                          ? _(be.target.value)
                          : be.target.value === VoiceChangerType.Beatrice_v2 &&
                            alert(
                              E(
                                "common.model_upload.beatrice_v2_not_supported_yet",
                              ),
                            );
                      },
                      children: jsxRuntimeExports.jsx(MenuItem, {
                        value: VoiceChangerType.RVC,
                        children: "RVC",
                      }),
                    }),
                  ],
                }),
                R === VoiceChangerType.RVC &&
                  jsxRuntimeExports.jsxs("div", {
                    style: { marginBottom: "20px" },
                    children: [
                      jsxRuntimeExports.jsxs("div", {
                        style: {
                          marginBottom: "10px",
                          display: "flex",
                          alignItems: "center",
                        },
                        children: [
                          jsxRuntimeExports.jsx(Button, {
                            variant: "outlined",
                            component: "span",
                            onClick: () => te.current?.click(),
                            sx: {
                              marginRight: "10px",
                              width: 200,
                              textOverflow: "ellipsis",
                              overflow: "hidden",
                              whiteSpace: "nowrap",
                            },
                            children: jsxRuntimeExports.jsx("span", {
                              style: {
                                display: "inline-block",
                                maxWidth: "100%",
                                overflow: "hidden",
                                textOverflow: "ellipsis",
                                whiteSpace: "nowrap",
                                verticalAlign: "middle",
                              },
                              children: E(
                                "common.model_upload.select_model_file",
                              ),
                            }),
                          }),
                          jsxRuntimeExports.jsx("input", {
                            ref: te,
                            type: "file",
                            accept: ".pth,.onnx",
                            style: { display: "none" },
                            onChange: (be) => T(be.target.files?.[0] || null),
                          }),
                          x &&
                            jsxRuntimeExports.jsx("span", {
                              style: {
                                flex: 1,
                                minWidth: 0,
                                overflow: "hidden",
                                textOverflow: "ellipsis",
                                whiteSpace: "nowrap",
                                display: "inline-block",
                                verticalAlign: "middle",
                              },
                              children: x.name,
                            }),
                        ],
                      }),
                      jsxRuntimeExports.jsxs("div", {
                        style: { display: "flex", alignItems: "center" },
                        children: [
                          jsxRuntimeExports.jsx(Button, {
                            variant: "outlined",
                            component: "span",
                            onClick: () => ie.current?.click(),
                            sx: {
                              marginRight: "10px",
                              width: 200,
                              textOverflow: "ellipsis",
                              overflow: "hidden",
                              whiteSpace: "nowrap",
                            },
                            children: jsxRuntimeExports.jsx("span", {
                              style: {
                                display: "inline-block",
                                maxWidth: "100%",
                                overflow: "hidden",
                                textOverflow: "ellipsis",
                                whiteSpace: "nowrap",
                                verticalAlign: "middle",
                              },
                              children: E(
                                "common.model_upload.select_index_file",
                              ),
                            }),
                          }),
                          jsxRuntimeExports.jsx("input", {
                            ref: ie,
                            type: "file",
                            accept: ".index,.bin",
                            style: { display: "none" },
                            onChange: (be) => O(be.target.files?.[0] || null),
                          }),
                          A &&
                            jsxRuntimeExports.jsx("span", {
                              style: {
                                flex: 1,
                                minWidth: 0,
                                overflow: "hidden",
                                textOverflow: "ellipsis",
                                whiteSpace: "nowrap",
                                display: "inline-block",
                                verticalAlign: "middle",
                              },
                              children: A.name,
                            }),
                        ],
                      }),
                    ],
                  }),
                R === VoiceChangerType.Beatrice_v2 &&
                  jsxRuntimeExports.jsxs("div", {
                    style: {
                      marginBottom: "20px",
                      display: "flex",
                      alignItems: "center",
                    },
                    children: [
                      jsxRuntimeExports.jsx(Button, {
                        variant: "outlined",
                        component: "span",
                        onClick: () => ne.current?.click(),
                        sx: {
                          marginRight: "10px",
                          width: 200,
                          textOverflow: "ellipsis",
                          overflow: "hidden",
                          whiteSpace: "nowrap",
                        },
                        children: jsxRuntimeExports.jsx("span", {
                          style: {
                            display: "inline-block",
                            maxWidth: "100%",
                            overflow: "hidden",
                            textOverflow: "ellipsis",
                            whiteSpace: "nowrap",
                            verticalAlign: "middle",
                          },
                          children: E("common.model_upload.select_zip"),
                        }),
                      }),
                      jsxRuntimeExports.jsx("input", {
                        ref: ne,
                        type: "file",
                        accept: ".zip",
                        style: { display: "none" },
                        onChange: (be) => ee(be.target.files?.[0] || null),
                      }),
                      H &&
                        jsxRuntimeExports.jsx("span", {
                          style: {
                            flex: 1,
                            minWidth: 0,
                            overflow: "hidden",
                            textOverflow: "ellipsis",
                            whiteSpace: "nowrap",
                            display: "inline-block",
                            verticalAlign: "middle",
                          },
                          children: H.name,
                        }),
                    ],
                  }),
                se &&
                  jsxRuntimeExports.jsxs("div", {
                    style: { marginBottom: 20 },
                    children: [
                      jsxRuntimeExports.jsx(LinearProgress, {
                        variant: "determinate",
                        value: fe,
                      }),
                      jsxRuntimeExports.jsxs("div", {
                        style: {
                          textAlign: "right",
                          fontSize: "0.9rem",
                          marginTop: 4,
                        },
                        children: [fe, "%"],
                      }),
                    ],
                  }),
                jsxRuntimeExports.jsx("div", {
                  style: {
                    display: "flex",
                    justifyContent: "flex-end",
                    marginTop: "30px",
                  },
                  children: jsxRuntimeExports.jsx(Button, {
                    variant: "contained",
                    color: "primary",
                    onClick: he,
                    children: E("common.model_upload.upload_button"),
                  }),
                }),
              ],
            }),
          }),
        [C, E, w, R, x, A, H, he, S.slotIndex, se, fe],
      );
    return jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, {
      children: [
        ye,
        jsxRuntimeExports.jsx(ConfirmationDialog, {
          isOpen: le,
          title: E("common.model_upload.upload_complete_title"),
          message: E("common.model_upload.upload_complete_message"),
          confirmButtonText: "OK",
          cancelButtonText: "OK",
          onConfirm: me,
          onCancel: me,
          showCancelButton: !1,
        }),
      ],
    });
  };
