// Extracted declaration from ../main-ui.js:99819-100036.
// Navigation/reference excerpt; shared bundle dependencies are NOT imported.
// Edit ../main-ui.js for a runnable change. This is not original TS/TSX source.
const VolumeControls = () => {
    const { t: S } = useTranslation(),
      {
        nodeInputGain: C,
        nodeOutputGain: E,
        nodeMonitorGain: w,
        setNodeInputGain: R,
        setNodeOutputGain: _,
        setNodeMonitorGain: x,
      } = useAppState(),
      { serverConfiguration: T, updateServerConfiguration: A } = useAppRoot(),
      O = T.voice_changer_input_mode === VoiceChangerInputMode.server,
      [H, ee] = reactExports.useState(!0),
      te = O ? T.audio_input_device_gain : C,
      ie = O ? T.audio_output_device_gain : E,
      ne = O ? T.audio_monitor_device_gain : w,
      ae = reactExports.useCallback(
        async (pe) => {
          O ? await A({ ...T, audio_input_device_gain: pe }) : R(pe);
        },
        [O, T, A, R],
      ),
      se = reactExports.useCallback(
        async (pe) => {
          O ? await A({ ...T, audio_output_device_gain: pe }) : _(pe);
        },
        [O, T, A, _],
      ),
      ce = reactExports.useCallback(
        async (pe) => {
          O ? await A({ ...T, audio_monitor_device_gain: pe }) : x(pe);
        },
        [O, T, A, x],
      );
    return reactExports.useMemo(
      () =>
        jsxRuntimeExports.jsxs("div", {
          style: { marginBottom: "20px" },
          children: [
            jsxRuntimeExports.jsxs("div", {
              style: {
                display: "flex",
                alignItems: "center",
                marginBottom: "10px",
              },
              children: [
                jsxRuntimeExports.jsx("label", {
                  style: { display: "block", fontWeight: "bold", flex: 1 },
                  children: S("common.controls.volume_control"),
                }),
                jsxRuntimeExports.jsx(IconButton, {
                  onClick: () => ee(!H),
                  size: "small",
                  children: H
                    ? jsxRuntimeExports.jsx(ExpandLess, {})
                    : jsxRuntimeExports.jsx(ExpandMore, {}),
                }),
              ],
            }),
            H &&
              jsxRuntimeExports.jsxs("div", {
                style: {
                  border: "1px solid #ddd",
                  borderRadius: "8px",
                  padding: "16px",
                  display: "flex",
                  flexDirection: "column",
                  gap: "16px",
                },
                children: [
                  jsxRuntimeExports.jsxs("div", {
                    style: {
                      display: "flex",
                      alignItems: "center",
                      gap: "16px",
                    },
                    children: [
                      jsxRuntimeExports.jsxs("div", {
                        style: {
                          minWidth: "100px",
                          display: "flex",
                          flexDirection: "column",
                          alignItems: "center",
                        },
                        children: [
                          jsxRuntimeExports.jsx(Tooltip, {
                            title: S("common.controls.input_volume"),
                            children: jsxRuntimeExports.jsx(Mic, {}),
                          }),
                          jsxRuntimeExports.jsx("span", {
                            style: {
                              fontSize: "12px",
                              marginTop: "4px",
                              userSelect: "none",
                            },
                            children: S("common.controls.input"),
                          }),
                        ],
                      }),
                      jsxRuntimeExports.jsx("input", {
                        type: "range",
                        min: "0",
                        max: "10",
                        step: "0.1",
                        value: te,
                        onChange: async (pe) => {
                          const le = parseFloat(pe.target.value);
                          await ae(le);
                        },
                        style: { flex: 1 },
                      }),
                      jsxRuntimeExports.jsx("span", {
                        style: { minWidth: "50px", textAlign: "right" },
                        children: te?.toFixed(1) || "unknown",
                      }),
                    ],
                  }),
                  jsxRuntimeExports.jsxs("div", {
                    style: {
                      display: "flex",
                      alignItems: "center",
                      gap: "16px",
                    },
                    children: [
                      jsxRuntimeExports.jsxs("div", {
                        style: {
                          minWidth: "100px",
                          display: "flex",
                          flexDirection: "column",
                          alignItems: "center",
                        },
                        children: [
                          jsxRuntimeExports.jsx(Tooltip, {
                            title: S("common.controls.output_volume"),
                            children: jsxRuntimeExports.jsx(VolumeUp, {}),
                          }),
                          jsxRuntimeExports.jsx("span", {
                            style: {
                              fontSize: "12px",
                              marginTop: "4px",
                              userSelect: "none",
                            },
                            children: S("common.controls.output1"),
                          }),
                        ],
                      }),
                      jsxRuntimeExports.jsx("input", {
                        type: "range",
                        min: "0",
                        max: "10",
                        step: "0.1",
                        value: ie,
                        onChange: async (pe) => {
                          const le = parseFloat(pe.target.value);
                          await se(le);
                        },
                        style: { flex: 1 },
                      }),
                      jsxRuntimeExports.jsx("span", {
                        style: { minWidth: "50px", textAlign: "right" },
                        children: ie?.toFixed(1) || "unknown",
                      }),
                    ],
                  }),
                  jsxRuntimeExports.jsxs("div", {
                    style: {
                      display: "flex",
                      alignItems: "center",
                      gap: "16px",
                    },
                    children: [
                      jsxRuntimeExports.jsxs("div", {
                        style: {
                          minWidth: "100px",
                          display: "flex",
                          flexDirection: "column",
                          alignItems: "center",
                        },
                        children: [
                          jsxRuntimeExports.jsx(Tooltip, {
                            title: S("common.controls.monitor_volume"),
                            children: jsxRuntimeExports.jsx(VolumeUp, {}),
                          }),
                          jsxRuntimeExports.jsx("span", {
                            style: {
                              fontSize: "12px",
                              marginTop: "4px",
                              userSelect: "none",
                            },
                            children: S("common.controls.output2"),
                          }),
                        ],
                      }),
                      jsxRuntimeExports.jsx("input", {
                        type: "range",
                        min: "0",
                        max: "10",
                        step: "0.1",
                        value: ne,
                        onChange: async (pe) => {
                          const le = parseFloat(pe.target.value);
                          await ce(le);
                        },
                        style: { flex: 1 },
                      }),
                      jsxRuntimeExports.jsx("span", {
                        style: { minWidth: "50px", textAlign: "right" },
                        children: ne?.toFixed(1) || "unknwon",
                      }),
                    ],
                  }),
                ],
              }),
          ],
        }),
      [H, S, te, ne, ie, ae, ce, se],
    );
  };
