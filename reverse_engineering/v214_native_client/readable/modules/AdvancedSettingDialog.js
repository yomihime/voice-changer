// Extracted declaration from ../main-ui.js:101363-101748.
// Navigation/reference excerpt; shared bundle dependencies are NOT imported.
// Edit ../main-ui.js for a runnable change. This is not original TS/TSX source.
const AdvancedSettingDialog = ({ open: S, onClose: C }) => {
    const {
        realtimeOutputStatusEnabled: E,
        setRealtimeOutputStatusEnabled: w,
        realtimeOutputStatusSendIntervalSec: R,
        setRealtimeOutputStatusSendIntervalSec: _,
        recordForAnalysis: x,
        setRecordForAnalysis: T,
        showSampleAudioButton: A,
        setShowSampleAudioButton: O,
      } = useAppState(),
      { serverConfiguration: H, updateServerConfiguration: ee } = useAppRoot(),
      { t: te } = useTranslation(),
      ie = H.voice_changer_input_mode === VoiceChangerInputMode.server,
      ne = ie ? (H.realtime_output_status_enabled ?? !1) : E,
      ae = ie ? (H.realtime_output_status_send_interval_sec ?? 0.2) : R,
      se = H.realtime_process_status_enabled ?? !1,
      ce = H.realtime_process_status_send_interval_sec ?? 2,
      fe = reactExports.useCallback(
        async (me) => {
          try {
            if (ie) {
              const ye = { ...H, realtime_output_status_enabled: me };
              await ee(ye);
            } else (w(me), console.log("Client config updated successfully"));
          } catch (ye) {
            console.error("Error updating realtime output status setting:", ye);
          }
        },
        [ie, H, ee, w],
      ),
      pe = reactExports.useCallback(
        async (me) => {
          try {
            if (ie) {
              const ye = { ...H, realtime_output_status_send_interval_sec: me };
              await ee(ye);
            } else _(me);
          } catch (ye) {
            console.error(
              "Error updating realtime status send interval setting:",
              ye,
            );
          }
        },
        [ie, H, ee, _],
      ),
      le = reactExports.useCallback(
        async (me) => {
          console.log("RealtimeProcessStatus config updated successfully", me);
          try {
            const ye = { ...H, realtime_process_status_enabled: me };
            (await ee(ye),
              console.log("RealtimeProcessStatus config updated successfully"));
          } catch (ye) {
            console.error(
              "Error updating realtime process status setting:",
              ye,
            );
          }
        },
        [H, ee],
      ),
      de = reactExports.useCallback(
        async (me) => {
          try {
            const ye = { ...H, realtime_process_status_send_interval_sec: me };
            (await ee(ye),
              console.log(
                "RealtimeProcessStatus send interval updated successfully",
              ));
          } catch (ye) {
            console.error(
              "Error updating realtime process status send interval setting:",
              ye,
            );
          }
        },
        [H, ee],
      );
    return reactExports.useMemo(
      () =>
        jsxRuntimeExports.jsxs(Dialog, {
          open: S,
          onClose: C,
          maxWidth: "sm",
          fullWidth: !0,
          children: [
            jsxRuntimeExports.jsxs("div", {
              style: {
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: "20px",
                padding: "20px 20px 0",
              },
              children: [
                jsxRuntimeExports.jsx("h2", {
                  style: { margin: 0 },
                  children: te("common.advanced_settings_dialog.title"),
                }),
                jsxRuntimeExports.jsx("button", {
                  onClick: C,
                  style: {
                    border: "none",
                    background: "none",
                    fontSize: "24px",
                    cursor: "pointer",
                    padding: "0 8px",
                  },
                  children: "×",
                }),
              ],
            }),
            jsxRuntimeExports.jsx(DialogContent, {
              children: jsxRuntimeExports.jsxs("div", {
                style: {
                  display: "flex",
                  flexDirection: "column",
                  gap: "20px",
                  padding: "20px 0",
                },
                children: [
                  jsxRuntimeExports.jsxs("div", {
                    style: { marginTop: "16px" },
                    children: [
                      jsxRuntimeExports.jsx("div", {
                        style: { fontWeight: "bold", marginBottom: "4px" },
                        children: te(
                          "common.advanced_settings_dialog.realtime_analysis_settings",
                        ),
                      }),
                      jsxRuntimeExports.jsxs("div", {
                        style: {
                          marginLeft: "16px",
                          display: "flex",
                          flexDirection: "column",
                          gap: "8px",
                        },
                        children: [
                          jsxRuntimeExports.jsxs("label", {
                            style: {
                              display: "flex",
                              alignItems: "center",
                              gap: "8px",
                            },
                            children: [
                              jsxRuntimeExports.jsx("input", {
                                type: "checkbox",
                                checked: ne,
                                onChange: (me) => fe(me.target.checked),
                              }),
                              te(
                                "common.advanced_settings_dialog.enable_realtime_io_analysis",
                              ),
                            ],
                          }),
                          jsxRuntimeExports.jsxs("div", {
                            style: { marginTop: "8px", paddingLeft: "24px" },
                            children: [
                              jsxRuntimeExports.jsxs("div", {
                                style: {
                                  display: "flex",
                                  alignItems: "center",
                                  gap: "10px",
                                },
                                children: [
                                  jsxRuntimeExports.jsx("span", {
                                    style: { minWidth: "120px" },
                                    children: te(
                                      "common.advanced_settings_dialog.send_interval_seconds",
                                    ),
                                  }),
                                  jsxRuntimeExports.jsx("input", {
                                    type: "range",
                                    min: "0.04",
                                    max: "0.2",
                                    step: "0.04",
                                    value: ae,
                                    onChange: (me) =>
                                      pe(Number(me.target.value)),
                                    style: { width: "100%" },
                                  }),
                                  jsxRuntimeExports.jsx("span", {
                                    style: {
                                      minWidth: "40px",
                                      textAlign: "right",
                                    },
                                    children: ae,
                                  }),
                                ],
                              }),
                              jsxRuntimeExports.jsx("div", {
                                style: {
                                  fontSize: "12px",
                                  color: "#666",
                                  marginTop: "4px",
                                },
                                children: te(
                                  "common.advanced_settings.realtime_description",
                                ),
                              }),
                            ],
                          }),
                          jsxRuntimeExports.jsxs("div", {
                            style: {
                              marginTop: "16px",
                              borderTop: "1px solid #eee",
                              paddingTop: "16px",
                            },
                            children: [
                              jsxRuntimeExports.jsxs("label", {
                                style: {
                                  display: "flex",
                                  alignItems: "center",
                                  gap: "8px",
                                },
                                children: [
                                  jsxRuntimeExports.jsx("input", {
                                    type: "checkbox",
                                    checked: se,
                                    onChange: (me) => le(me.target.checked),
                                  }),
                                  te(
                                    "common.advanced_settings_dialog.enable_realtime_voice_processing_analysis",
                                  ),
                                ],
                              }),
                              jsxRuntimeExports.jsxs("div", {
                                style: {
                                  marginTop: "8px",
                                  paddingLeft: "24px",
                                },
                                children: [
                                  jsxRuntimeExports.jsxs("div", {
                                    style: {
                                      display: "flex",
                                      alignItems: "center",
                                      gap: "10px",
                                    },
                                    children: [
                                      jsxRuntimeExports.jsx("span", {
                                        style: { minWidth: "120px" },
                                        children: te(
                                          "common.advanced_settings_dialog.send_interval_seconds",
                                        ),
                                      }),
                                      jsxRuntimeExports.jsx("input", {
                                        type: "range",
                                        min: "0.1",
                                        max: "5.0",
                                        step: "0.1",
                                        value: ce,
                                        onChange: (me) =>
                                          de(Number(me.target.value)),
                                        style: { width: "100%" },
                                      }),
                                      jsxRuntimeExports.jsx("span", {
                                        style: {
                                          minWidth: "40px",
                                          textAlign: "right",
                                        },
                                        children: ce,
                                      }),
                                    ],
                                  }),
                                  jsxRuntimeExports.jsx("div", {
                                    style: {
                                      fontSize: "12px",
                                      color: "#666",
                                      marginTop: "4px",
                                    },
                                    children: te(
                                      "common.advanced_settings.realtime_description",
                                    ),
                                  }),
                                ],
                              }),
                            ],
                          }),
                        ],
                      }),
                    ],
                  }),
                  jsxRuntimeExports.jsxs("div", {
                    children: [
                      jsxRuntimeExports.jsx("div", {
                        style: { fontWeight: "bold", marginBottom: "4px" },
                        children: te(
                          "common.advanced_settings.recording_settings",
                        ),
                      }),
                      jsxRuntimeExports.jsxs("div", {
                        style: {
                          marginLeft: "16px",
                          display: "flex",
                          flexDirection: "column",
                          gap: "8px",
                        },
                        children: [
                          jsxRuntimeExports.jsxs("label", {
                            style: {
                              display: "flex",
                              alignItems: "center",
                              gap: "8px",
                            },
                            children: [
                              jsxRuntimeExports.jsx("input", {
                                type: "checkbox",
                                checked: x,
                                onChange: (me) => T(me.target.checked),
                              }),
                              te(
                                "common.advanced_settings.record_for_analysis",
                              ),
                            ],
                          }),
                          jsxRuntimeExports.jsx("div", {
                            style: {
                              fontSize: "12px",
                              color: "#666",
                              marginLeft: "24px",
                            },
                            children: te(
                              "common.advanced_settings.record_for_analysis_description",
                            ),
                          }),
                        ],
                      }),
                    ],
                  }),
                  jsxRuntimeExports.jsxs("div", {
                    children: [
                      jsxRuntimeExports.jsx("div", {
                        style: { fontWeight: "bold", marginBottom: "4px" },
                        children: te(
                          "common.advanced_settings.sample_audio_button",
                        ),
                      }),
                      jsxRuntimeExports.jsxs("div", {
                        style: {
                          marginLeft: "16px",
                          display: "flex",
                          flexDirection: "column",
                          gap: "8px",
                        },
                        children: [
                          jsxRuntimeExports.jsxs("label", {
                            style: {
                              display: "flex",
                              alignItems: "center",
                              gap: "8px",
                            },
                            children: [
                              jsxRuntimeExports.jsx("input", {
                                type: "checkbox",
                                checked: A,
                                onChange: (me) => O(me.target.checked),
                              }),
                              te(
                                "common.advanced_settings.show_sample_audio_button",
                              ),
                            ],
                          }),
                          jsxRuntimeExports.jsx("div", {
                            style: {
                              fontSize: "12px",
                              color: "#666",
                              marginLeft: "24px",
                            },
                            children: te(
                              "common.advanced_settings.sample_audio_button_description",
                            ),
                          }),
                        ],
                      }),
                    ],
                  }),
                ],
              }),
            }),
          ],
        }),
      [S, C, ne, fe, ae, pe, se, le, ce, de, x, T, ie, te, A, O],
    );
  };
