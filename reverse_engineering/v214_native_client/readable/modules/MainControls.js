// Extracted declaration from ../main-ui.js:98372-98748.
// Navigation/reference excerpt; shared bundle dependencies are NOT imported.
// Edit ../main-ui.js for a runnable change. This is not original TS/TSX source.
const MainControls = () => {
    const {
        isStarted: S,
        setIsStarted: C,
        isOutputRecording: E,
        setIsOutputRecording: w,
        isPassthrough: R,
        setIsPassthrough: _,
        recordForAnalysis: x,
      } = useAppState(),
      { t: T } = useTranslation(),
      [A, O] = reactExports.useState(!1),
      {
        serverConfiguration: H,
        serverGpuInfo: ee,
        startServerDevice: te,
        stopServerDevice: ie,
        localVoiceChangerInterfaceInfo: ne,
        updateServerConfiguration: ae,
        triggerToast: se,
      } = useAppRoot(),
      ce = H.voice_changer_input_mode === VoiceChangerInputMode.server,
      fe = !!ne?.local_voice_changer_interface_active,
      pe = ce ? fe : S,
      le = ce ? !fe : !S,
      de = ce ? H.pass_through : R,
      he = ce ? H.recording_started : E,
      me = reactExports.useCallback(async () => {
        if (ce) {
          if (
            H.audio_input_device_index === -1 ||
            H.audio_output_device_index === -1
          ) {
            se("error", T("common.controls.device_not_selected_error"));
            return;
          }
          await te();
        } else C(!0);
      }, [
        ce,
        H.audio_input_device_index,
        H.audio_output_device_index,
        se,
        T,
        te,
        C,
      ]),
      ye = reactExports.useCallback(async () => {
        ce ? await ie() : C(!1);
      }, [ce, ie, C]);
    return reactExports.useMemo(
      () =>
        jsxRuntimeExports.jsxs("div", {
          children: [
            jsxRuntimeExports.jsxs("div", {
              style: { display: "flex", alignItems: "center", gap: 8 },
              children: [
                jsxRuntimeExports.jsx("label", {
                  style: { display: "block", fontWeight: "bold", flex: 1 },
                  children: T("common.controls.title"),
                }),
                jsxRuntimeExports.jsxs("div", {
                  style: {
                    display: "flex",
                    gap: 8,
                    justifyContent: "flex-end",
                  },
                  children: [
                    (() => {
                      const ve = ee.find(
                        (xe) => xe.device_id_int === H.gpu_device_id_int,
                      );
                      return jsxRuntimeExports.jsx(Chip, {
                        label: `${ve?.name || "cpu"}`,
                        color: "success",
                        size: "small",
                        sx: {
                          fontWeight: "bold",
                          cursor: "default",
                          "&:hover": {
                            backgroundColor: "success.main",
                            color: "white",
                            cursor: "default",
                          },
                        },
                        clickable: !0,
                        onClick: () => O(!0),
                      });
                    })(),
                    jsxRuntimeExports.jsx(Chip, {
                      label:
                        H.voice_changer_input_mode ===
                        VoiceChangerInputMode.server
                          ? T("common.controls.server_mode")
                          : T("common.controls.client_mode"),
                      color:
                        H.voice_changer_input_mode ===
                        VoiceChangerInputMode.server
                          ? "secondary"
                          : "primary",
                      size: "small",
                      sx: {
                        fontWeight: "bold",
                        cursor: "default",
                        "&:hover": {
                          backgroundColor:
                            H.voice_changer_input_mode ===
                            VoiceChangerInputMode.server
                              ? "secondary.main"
                              : "primary.main",
                          color: "white",
                          cursor: "default",
                        },
                      },
                      clickable: !0,
                      onClick: () => O(!0),
                    }),
                  ],
                }),
              ],
            }),
            jsxRuntimeExports.jsxs(Stack, {
              direction: "row",
              spacing: 2,
              justifyContent: "flex-start",
              sx: { my: 2 },
              style: { width: "100%" },
              children: [
                jsxRuntimeExports.jsx(Box, {
                  sx: { minWidth: 0, display: "flex" },
                  children: jsxRuntimeExports.jsx(Tooltip, {
                    title: T("common.controls.start"),
                    children: jsxRuntimeExports.jsx(IconButton, {
                      onClick: me,
                      color: pe ? "primary" : "default",
                      size: "large",
                      sx: {
                        height: "60px",
                        minWidth: "70px",
                        px: 1,
                        border: "2px solid",
                        borderColor: pe ? "primary.main" : "grey.300",
                        borderRadius: "8px",
                        "&:hover": { borderColor: "primary.main" },
                      },
                      children: jsxRuntimeExports.jsxs(Stack, {
                        alignItems: "center",
                        children: [
                          jsxRuntimeExports.jsx(PlayArrow, {
                            sx: { fontSize: "1.5rem" },
                          }),
                          jsxRuntimeExports.jsx("span", {
                            style: {
                              fontSize: "11px",
                              marginTop: "2px",
                              whiteSpace: "nowrap",
                            },
                            children: T("common.controls.start"),
                          }),
                        ],
                      }),
                    }),
                  }),
                }),
                jsxRuntimeExports.jsx(Box, {
                  sx: { minWidth: 0, display: "flex" },
                  children: jsxRuntimeExports.jsx(Tooltip, {
                    title: T("common.controls.stop"),
                    children: jsxRuntimeExports.jsx(IconButton, {
                      onClick: async () => {
                        await ye();
                      },
                      color: le ? "primary" : "default",
                      size: "large",
                      sx: {
                        height: "60px",
                        minWidth: "70px",
                        px: 1,
                        border: "2px solid",
                        borderColor: le ? "primary.main" : "grey.300",
                        borderRadius: "8px",
                        "&:hover": { borderColor: "primary.main" },
                      },
                      children: jsxRuntimeExports.jsxs(Stack, {
                        alignItems: "center",
                        children: [
                          jsxRuntimeExports.jsx(Stop, {
                            sx: { fontSize: "1.5rem" },
                          }),
                          jsxRuntimeExports.jsx("span", {
                            style: {
                              fontSize: "11px",
                              marginTop: "2px",
                              whiteSpace: "nowrap",
                            },
                            children: T("common.controls.stop"),
                          }),
                        ],
                      }),
                    }),
                  }),
                }),
                jsxRuntimeExports.jsx(Box, {
                  sx: { minWidth: 0, display: "flex" },
                  children: jsxRuntimeExports.jsx(Tooltip, {
                    title: T(
                      he
                        ? "common.controls.stop_recording"
                        : "common.controls.start_recording",
                    ),
                    children: jsxRuntimeExports.jsx(IconButton, {
                      onClick: async () => {
                        if (ce) {
                          const ve = !H.recording_started;
                          if (
                            (await ae({ ...H, recording_started: ve }), !ve)
                          ) {
                            console.log(
                              T("common.controls.start_download_recording"),
                            );
                            try {
                              x
                                ? await downloadServerRecordingFiles(!0, !0)
                                : await downloadServerRecordingFiles(!1, !0);
                            } catch (xe) {
                              console.error(
                                T("common.controls.download_recording_failed"),
                                xe,
                              );
                            }
                          }
                        } else {
                          const ve = !E;
                          if ((w(ve), x))
                            try {
                              (await ae({ ...H, recording_started: ve }),
                                ve ||
                                  (console.log(
                                    T(
                                      "common.controls.start_download_server_recording",
                                    ),
                                  ),
                                  await downloadServerRecordingFiles(!0, !0)));
                            } catch (xe) {
                              console.error(
                                T("common.controls.server_recording_failed"),
                                xe,
                              );
                            }
                        }
                      },
                      color: he ? "primary" : "default",
                      size: "large",
                      sx: {
                        height: "60px",
                        minWidth: "70px",
                        px: 1,
                        border: "2px solid",
                        borderColor: he ? "primary.main" : "grey.300",
                        borderRadius: "8px",
                        "&:hover": { borderColor: "primary.main" },
                      },
                      children: jsxRuntimeExports.jsxs(Stack, {
                        alignItems: "center",
                        children: [
                          jsxRuntimeExports.jsx(FiberManualRecord, {
                            sx: { fontSize: "1.5rem" },
                          }),
                          jsxRuntimeExports.jsx("span", {
                            style: {
                              fontSize: "11px",
                              marginTop: "2px",
                              whiteSpace: "nowrap",
                            },
                            children: T(
                              he
                                ? "common.controls.recording"
                                : "common.controls.record",
                            ),
                          }),
                        ],
                      }),
                    }),
                  }),
                }),
                jsxRuntimeExports.jsx(Box, { sx: { width: "20px" } }),
                jsxRuntimeExports.jsx(Box, {
                  sx: { minWidth: 0, display: "flex" },
                  children: jsxRuntimeExports.jsx(Tooltip, {
                    title: T(
                      de
                        ? "common.controls.passthrough_disable"
                        : "common.controls.passthrough_enable",
                    ),
                    children: jsxRuntimeExports.jsx(IconButton, {
                      onClick: async () => {
                        ce
                          ? await ae({ ...H, pass_through: !H.pass_through })
                          : _(!R);
                      },
                      color: de ? "primary" : "default",
                      size: "large",
                      sx: {
                        height: "60px",
                        minWidth: "70px",
                        px: 1,
                        border: "2px solid",
                        borderColor: de ? "primary.main" : "grey.300",
                        borderRadius: "8px",
                        "&:hover": { borderColor: "primary.main" },
                      },
                      children: jsxRuntimeExports.jsxs(Stack, {
                        alignItems: "center",
                        children: [
                          jsxRuntimeExports.jsx(SwapHoriz, {
                            sx: { fontSize: "1.5rem" },
                          }),
                          jsxRuntimeExports.jsx("span", {
                            style: {
                              fontSize: "11px",
                              marginTop: "2px",
                              whiteSpace: "nowrap",
                            },
                            children: T("common.controls.passthrough"),
                          }),
                        ],
                      }),
                    }),
                  }),
                }),
                jsxRuntimeExports.jsx(Box, {
                  sx: { minWidth: 0, display: "flex" },
                  children: jsxRuntimeExports.jsx(Tooltip, {
                    title: T("common.controls.settings"),
                    children: jsxRuntimeExports.jsx(IconButton, {
                      onClick: () => O(!0),
                      color: "default",
                      size: "large",
                      sx: {
                        height: "60px",
                        minWidth: "70px",
                        px: 1,
                        border: "2px solid",
                        borderColor: "grey.300",
                        borderRadius: "8px",
                        "&:hover": { borderColor: "primary.main" },
                      },
                      children: jsxRuntimeExports.jsxs(Stack, {
                        alignItems: "center",
                        children: [
                          jsxRuntimeExports.jsx(Settings, {
                            sx: { fontSize: "1.5rem" },
                          }),
                          jsxRuntimeExports.jsx("span", {
                            style: {
                              fontSize: "11px",
                              marginTop: "2px",
                              whiteSpace: "nowrap",
                            },
                            children: T("common.controls.settings"),
                          }),
                        ],
                      }),
                    }),
                  }),
                }),
              ],
            }),
            jsxRuntimeExports.jsx(SettingsDialog, {
              open: A,
              onClose: () => O(!1),
            }),
          ],
        }),
      [w, _, T, E, R, A, O, H, ee, ce, pe, le, ae, de, he, x, me, ye],
    );
  };
