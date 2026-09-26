// Extracted declaration from ../main-ui.js:97260-98344.
// Navigation/reference excerpt; shared bundle dependencies are NOT imported.
// Edit ../main-ui.js for a runnable change. This is not original TS/TSX source.
const SettingsDialog = ({ open: S, onClose: C }) => {
    const {
        setSelectedInputAudioDeviceId: E,
        setOutputAudio: w,
        setMonitorAudio: R,
        selectedInputAudioDeviceId: _,
        outputAudio: x,
        monitorAudio: T,
        enableEchoCancellation: A,
        setEnableEchoCancellation: O,
        enableNoiseSuppression: H,
        setEnableNoiseSuppression: ee,
        enableNoiseSuppression2: te,
        setEnableNoiseSuppression2: ie,
        isOutputRecording: ne,
        isPassthrough: ae,
        abortAllRequests: se,
        isStarted: ce,
      } = useAppState(),
      {
        audioInputs: fe,
        audioOutputs: pe,
        serverConfiguration: le,
        updateServerConfiguration: de,
        serverAudioInputDevices: he,
        serverAudioOutputDevices: me,
        serverGpuInfo: ye,
        localVoiceChangerInterfaceInfo: be,
        stopServerDevice: ve,
        startServerDevice: xe,
      } = useAppRoot(),
      { t: Ce } = useTranslation(),
      _e = le.voice_changer_input_mode === VoiceChangerInputMode.client,
      Be = le.voice_changer_input_mode === VoiceChangerInputMode.server,
      Ve =
        !!be?.local_voice_changer_interface_active ||
        !!le.recording_started ||
        !!le.pass_through,
      ke = !!be?.local_voice_changer_interface_active,
      qe = Be ? Ve : ce || ne || ae,
      [ze, Ae] = reactExports.useState(!1),
      [Ne, We] = reactExports.useState(""),
      [Ie, $e] = reactExports.useState(""),
      [Me, Ge] = reactExports.useState(""),
      er = reactExports.useMemo(
        () => Array.from(new Set(he.map((Fe) => Fe.host_api))),
        [he],
      ),
      Ht = reactExports.useMemo(
        () => Array.from(new Set(me.map((Fe) => Fe.host_api))),
        [me],
      ),
      rr = reactExports.useMemo(
        () => (Ne === "" ? he : he.filter((Fe) => Fe.host_api === Ne)),
        [he, Ne],
      ),
      Jt = reactExports.useMemo(
        () => (Ie === "" ? me : me.filter((Fe) => Fe.host_api === Ie)),
        [me, Ie],
      ),
      Kt = reactExports.useMemo(
        () => (Me === "" ? me : me.filter((Fe) => Fe.host_api === Me)),
        [me, Me],
      ),
      dr = reactExports.useMemo(
        () => he.find((Fe) => Fe.index === le.audio_input_device_index),
        [he, le.audio_input_device_index],
      ),
      or = reactExports.useMemo(
        () => me.find((Fe) => Fe.index === le.audio_output_device_index),
        [me, le.audio_output_device_index],
      ),
      ar = reactExports.useMemo(
        () => me.find((Fe) => Fe.index === le.audio_monitor_device_index),
        [me, le.audio_monitor_device_index],
      ),
      ur = reactExports.useRef(""),
      pr = reactExports.useRef(""),
      vr = reactExports.useRef("");
    (reactExports.useEffect(() => {
      _e ||
        (Ne !== ur.current &&
          ((ur.current = Ne),
          Ne !== "" &&
            le.audio_input_device_index !== -1 &&
            (rr.some((Dt) => Dt.index === le.audio_input_device_index) ||
              de({
                ...le,
                audio_input_device_index: -1,
                audio_input_device_sample_rate: -1,
              }))));
    }, [Ne, rr, _e, le, de]),
      reactExports.useEffect(() => {
        _e ||
          (Ie !== pr.current &&
            ((pr.current = Ie),
            Ie !== "" &&
              le.audio_output_device_index !== -1 &&
              (Jt.some((Dt) => Dt.index === le.audio_output_device_index) ||
                de({
                  ...le,
                  audio_output_device_index: -1,
                  audio_output_device_sample_rate: -1,
                }))));
      }, [Ie, Jt, _e, le, de]),
      reactExports.useEffect(() => {
        _e ||
          (Me !== vr.current &&
            ((vr.current = Me),
            Me !== "" &&
              le.audio_monitor_device_index !== -1 &&
              (Kt.some((Dt) => Dt.index === le.audio_monitor_device_index) ||
                de({
                  ...le,
                  audio_monitor_device_index: -1,
                  audio_monitor_device_sample_rate: -1,
                }))));
      }, [Me, Kt, _e, le, de]));
    const Ut = reactExports.useMemo(
        () =>
          _e == !1
            ? null
            : jsxRuntimeExports.jsx("select", {
                value: _,
                onChange: (Fe) => E(Fe.target.value),
                style: { width: "100%", padding: "8px" },
                children: fe.map((Fe) =>
                  jsxRuntimeExports.jsx(
                    "option",
                    { value: Fe.deviceId, children: Fe.label },
                    Fe.deviceId,
                  ),
                ),
              }),
        [fe, _, E, _e],
      ),
      nr = reactExports.useMemo(
        () =>
          _e
            ? null
            : jsxRuntimeExports.jsxs("div", {
                style: { display: "flex", gap: "8px" },
                children: [
                  jsxRuntimeExports.jsxs("select", {
                    value: Ne,
                    onChange: (Fe) => We(Fe.target.value),
                    style: { width: "25%", padding: "8px" },
                    children: [
                      jsxRuntimeExports.jsx("option", {
                        value: "",
                        children: Ce("common.settings_dialog.all_hosts"),
                      }),
                      er.map((Fe) =>
                        jsxRuntimeExports.jsx(
                          "option",
                          { value: Fe, children: Fe },
                          Fe,
                        ),
                      ),
                    ],
                  }),
                  jsxRuntimeExports.jsxs("select", {
                    value: le.audio_input_device_index,
                    onChange: async (Fe) => {
                      const Dt = parseInt(Fe.target.value);
                      Ae(!0);
                      try {
                        (await de({
                          ...le,
                          audio_input_device_index: Dt,
                          audio_input_device_sample_rate: -1,
                        }),
                          ke &&
                            (await ve(),
                            await new Promise((dt) => setTimeout(dt, 100)),
                            await xe(),
                            await new Promise((dt) => setTimeout(dt, 100))));
                      } finally {
                        Ae(!1);
                      }
                    },
                    style: { width: "50%", padding: "8px" },
                    children: [
                      ke == !1 &&
                        jsxRuntimeExports.jsx(
                          "option",
                          {
                            value: -1,
                            children: Ce("common.settings_dialog.unselected"),
                          },
                          -1,
                        ),
                      rr.map((Fe) =>
                        jsxRuntimeExports.jsx(
                          "option",
                          {
                            value: Fe.index,
                            children:
                              Ne === ""
                                ? `(${Fe.host_api})${Fe.name}`
                                : Fe.name,
                          },
                          Fe.index,
                        ),
                      ),
                    ],
                  }),
                  dr &&
                    dr.available_samplerates.length > 0 &&
                    jsxRuntimeExports.jsxs("select", {
                      value: le.audio_input_device_sample_rate,
                      onChange: async (Fe) => {
                        const Dt = parseInt(Fe.target.value);
                        Ae(!0);
                        try {
                          (await de({
                            ...le,
                            audio_input_device_sample_rate: Dt,
                          }),
                            ke &&
                              (await ve(),
                              await new Promise((dt) => setTimeout(dt, 100)),
                              await xe(),
                              await new Promise((dt) => setTimeout(dt, 100))));
                        } finally {
                          Ae(!1);
                        }
                      },
                      style: { width: "25%", padding: "8px" },
                      children: [
                        jsxRuntimeExports.jsx("option", {
                          value: -1,
                          children: Ce("common.settings_dialog.auto"),
                        }),
                        dr.available_samplerates.map((Fe) =>
                          jsxRuntimeExports.jsxs(
                            "option",
                            { value: Fe, children: [Fe, " Hz"] },
                            Fe,
                          ),
                        ),
                      ],
                    }),
                ],
              }),
        [_e, Ne, er, rr, le, de, dr, Ae, ke, ve, xe, Ce],
      ),
      mr = reactExports.useMemo(
        () =>
          _e
            ? jsxRuntimeExports.jsx("select", {
                value: x,
                onChange: (Fe) => w(Fe.target.value),
                style: { width: "100%", padding: "8px" },
                children: pe.map((Fe) =>
                  jsxRuntimeExports.jsx(
                    "option",
                    { value: Fe.deviceId, children: Fe.label },
                    Fe.deviceId,
                  ),
                ),
              })
            : null,
        [pe, x, w, _e],
      ),
      gr = reactExports.useMemo(
        () =>
          _e
            ? null
            : jsxRuntimeExports.jsxs("div", {
                style: { display: "flex", gap: "8px" },
                children: [
                  jsxRuntimeExports.jsxs("select", {
                    value: Ie,
                    onChange: (Fe) => $e(Fe.target.value),
                    style: { width: "25%", padding: "8px" },
                    children: [
                      jsxRuntimeExports.jsx("option", {
                        value: "",
                        children: Ce("common.settings_dialog.all_hosts"),
                      }),
                      Ht.map((Fe) =>
                        jsxRuntimeExports.jsx(
                          "option",
                          { value: Fe, children: Fe },
                          Fe,
                        ),
                      ),
                    ],
                  }),
                  jsxRuntimeExports.jsxs("select", {
                    value: le.audio_output_device_index,
                    onChange: async (Fe) => {
                      const Dt = parseInt(Fe.target.value);
                      Ae(!0);
                      try {
                        (await de({
                          ...le,
                          audio_output_device_index: Dt,
                          audio_output_device_sample_rate: -1,
                        }),
                          ke &&
                            (await ve(),
                            await new Promise((dt) => setTimeout(dt, 100)),
                            await xe(),
                            await new Promise((dt) => setTimeout(dt, 100))));
                      } finally {
                        Ae(!1);
                      }
                    },
                    style: { width: "50%", padding: "8px" },
                    children: [
                      ke == !1 &&
                        jsxRuntimeExports.jsx(
                          "option",
                          {
                            value: -1,
                            children: Ce("common.settings_dialog.unselected"),
                          },
                          -1,
                        ),
                      Jt.map((Fe) =>
                        jsxRuntimeExports.jsx(
                          "option",
                          {
                            value: Fe.index,
                            children:
                              Ie === ""
                                ? `(${Fe.host_api})${Fe.name}`
                                : Fe.name,
                          },
                          Fe.index,
                        ),
                      ),
                    ],
                  }),
                  or &&
                    or.available_samplerates.length > 0 &&
                    jsxRuntimeExports.jsxs("select", {
                      value: le.audio_output_device_sample_rate,
                      onChange: async (Fe) => {
                        const Dt = parseInt(Fe.target.value);
                        try {
                          (await de({
                            ...le,
                            audio_output_device_sample_rate: Dt,
                          }),
                            ke &&
                              (await ve(),
                              await new Promise((dt) => setTimeout(dt, 100)),
                              await xe(),
                              await new Promise((dt) => setTimeout(dt, 100))));
                        } finally {
                          Ae(!1);
                        }
                      },
                      style: { width: "25%", padding: "8px" },
                      children: [
                        jsxRuntimeExports.jsx("option", {
                          value: -1,
                          children: Ce("common.settings_dialog.auto"),
                        }),
                        or.available_samplerates.map((Fe) =>
                          jsxRuntimeExports.jsxs(
                            "option",
                            { value: Fe, children: [Fe, " Hz"] },
                            Fe,
                          ),
                        ),
                      ],
                    }),
                ],
              }),
        [_e, Ie, Ht, Jt, le, de, or, Ae, ve, xe, ke, Ce],
      ),
      Zt = reactExports.useMemo(
        () =>
          _e
            ? jsxRuntimeExports.jsx("select", {
                value: T,
                onChange: (Fe) => R(Fe.target.value),
                style: { width: "100%", padding: "8px" },
                children: pe.map((Fe) =>
                  jsxRuntimeExports.jsx(
                    "option",
                    { value: Fe.deviceId, children: Fe.label },
                    Fe.deviceId,
                  ),
                ),
              })
            : null,
        [pe, T, R, _e],
      ),
      yr = reactExports.useMemo(
        () =>
          _e
            ? null
            : jsxRuntimeExports.jsxs("div", {
                style: { display: "flex", gap: "8px" },
                children: [
                  jsxRuntimeExports.jsxs("select", {
                    value: Me,
                    onChange: (Fe) => Ge(Fe.target.value),
                    style: { width: "25%", padding: "8px" },
                    children: [
                      jsxRuntimeExports.jsx("option", {
                        value: "",
                        children: Ce("common.settings_dialog.all_hosts"),
                      }),
                      Ht.map((Fe) =>
                        jsxRuntimeExports.jsx(
                          "option",
                          { value: Fe, children: Fe },
                          Fe,
                        ),
                      ),
                    ],
                  }),
                  jsxRuntimeExports.jsxs("select", {
                    value: le.audio_monitor_device_index,
                    onChange: async (Fe) => {
                      const Dt = parseInt(Fe.target.value);
                      Ae(!0);
                      try {
                        (await de({
                          ...le,
                          audio_monitor_device_index: Dt,
                          audio_monitor_device_sample_rate: -1,
                        }),
                          ke &&
                            (await ve(),
                            await new Promise((dt) => setTimeout(dt, 100)),
                            await xe(),
                            await new Promise((dt) => setTimeout(dt, 100))));
                      } finally {
                        Ae(!1);
                      }
                    },
                    style: { width: "50%", padding: "8px" },
                    children: [
                      jsxRuntimeExports.jsx(
                        "option",
                        {
                          value: -1,
                          children: Ce("common.settings_dialog.unselected"),
                        },
                        -1,
                      ),
                      Kt.map((Fe) =>
                        jsxRuntimeExports.jsx(
                          "option",
                          {
                            value: Fe.index,
                            children:
                              Me === ""
                                ? `(${Fe.host_api})${Fe.name}`
                                : Fe.name,
                          },
                          Fe.index,
                        ),
                      ),
                    ],
                  }),
                  ar &&
                    ar.available_samplerates.length > 0 &&
                    jsxRuntimeExports.jsxs("select", {
                      value: le.audio_monitor_device_sample_rate,
                      onChange: async (Fe) => {
                        const Dt = parseInt(Fe.target.value);
                        Ae(!0);
                        try {
                          (await de({
                            ...le,
                            audio_monitor_device_sample_rate: Dt,
                          }),
                            ke &&
                              (await ve(),
                              await new Promise((dt) => setTimeout(dt, 100)),
                              await xe(),
                              await new Promise((dt) => setTimeout(dt, 100))));
                        } finally {
                          Ae(!1);
                        }
                      },
                      style: { width: "25%", padding: "8px" },
                      children: [
                        jsxRuntimeExports.jsx("option", {
                          value: -1,
                          children: Ce("common.settings_dialog.auto"),
                        }),
                        ar.available_samplerates.map((Fe) =>
                          jsxRuntimeExports.jsxs(
                            "option",
                            { value: Fe, children: [Fe, " Hz"] },
                            Fe,
                          ),
                        ),
                      ],
                    }),
                ],
              }),
        [_e, Me, Ht, Kt, le, de, ar, Ae, ke, ve, xe, Ce],
      ),
      xr = reactExports.useMemo(() => {
        if (!_e) {
          const Fe = he.find((Te) => Te.index === le.audio_input_device_index),
            Dt = me.find((Te) => Te.index === le.audio_output_device_index),
            dt = me.find((Te) => Te.index === le.audio_monitor_device_index);
          return (
            (Fe && Fe.host_api === "Windows WASAPI") ||
            (Dt && Dt.host_api === "Windows WASAPI") ||
            (dt && dt.host_api === "Windows WASAPI")
          );
        }
        return !1;
      }, [
        _e,
        he,
        me,
        le.audio_input_device_index,
        le.audio_output_device_index,
        le.audio_monitor_device_index,
      ]);
    return reactExports.useMemo(
      () =>
        jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, {
          children: [
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
                      children: Ce("common.settings_dialog.title"),
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
                      children: Ce("common.settings_dialog.close"),
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
                            children: Ce("common.settings_dialog.gpu_settings"),
                          }),
                          jsxRuntimeExports.jsx("div", {
                            style: { marginLeft: "16px" },
                            children: jsxRuntimeExports.jsx("select", {
                              value: le.gpu_device_id_int,
                              onChange: async (Fe) => {
                                const Dt = parseInt(Fe.target.value);
                                (se(),
                                  await de({ ...le, gpu_device_id_int: Dt }));
                              },
                              style: { width: "100%", padding: "8px" },
                              children: ye.map((Fe) =>
                                jsxRuntimeExports.jsx(
                                  "option",
                                  {
                                    value: Fe.device_id_int,
                                    children: Fe.name,
                                  },
                                  Fe.device_id_int,
                                ),
                              ),
                            }),
                          }),
                        ],
                      }),
                      jsxRuntimeExports.jsxs("div", {
                        style: { marginTop: "8px" },
                        children: [
                          jsxRuntimeExports.jsx("div", {
                            style: { fontWeight: "bold", marginBottom: "4px" },
                            children: Ce(
                              "common.settings_dialog.voice_changer_input_mode",
                            ),
                          }),
                          jsxRuntimeExports.jsxs("div", {
                            style: { marginLeft: "16px" },
                            children: [
                              jsxRuntimeExports.jsxs(ButtonGroup, {
                                variant: "outlined",
                                fullWidth: !0,
                                children: [
                                  jsxRuntimeExports.jsx("span", {
                                    style: { width: "100%" },
                                    children: jsxRuntimeExports.jsx(Button, {
                                      variant:
                                        le.voice_changer_input_mode ===
                                        VoiceChangerInputMode.client
                                          ? "contained"
                                          : "outlined",
                                      color:
                                        le.voice_changer_input_mode ===
                                        VoiceChangerInputMode.client
                                          ? "primary"
                                          : "inherit",
                                      onClick: async () => {
                                        le.voice_changer_input_mode !==
                                          VoiceChangerInputMode.client &&
                                          (await de({
                                            ...le,
                                            voice_changer_input_mode:
                                              VoiceChangerInputMode.client,
                                            input_sample_rate: 48e3,
                                            output_sample_rate: 48e3,
                                            monitor_sample_rate: 48e3,
                                          }));
                                      },
                                      disabled: qe,
                                      children: Ce(
                                        "common.settings_dialog.client_mode",
                                      ),
                                    }),
                                  }),
                                  jsxRuntimeExports.jsx("span", {
                                    style: { width: "100%" },
                                    children: jsxRuntimeExports.jsx(Button, {
                                      variant:
                                        le.voice_changer_input_mode ===
                                        VoiceChangerInputMode.server
                                          ? "contained"
                                          : "outlined",
                                      color:
                                        le.voice_changer_input_mode ===
                                        VoiceChangerInputMode.server
                                          ? "primary"
                                          : "inherit",
                                      onClick: async () => {
                                        le.voice_changer_input_mode !==
                                          VoiceChangerInputMode.server &&
                                          (await de({
                                            ...le,
                                            voice_changer_input_mode:
                                              VoiceChangerInputMode.server,
                                          }));
                                      },
                                      disabled: qe,
                                      children: Ce(
                                        "common.settings_dialog.server_mode",
                                      ),
                                    }),
                                  }),
                                ],
                              }),
                              qe &&
                                jsxRuntimeExports.jsx("div", {
                                  style: {
                                    color: "#f44336",
                                    fontSize: "12px",
                                    marginTop: "4px",
                                  },
                                  children: Ce(
                                    "common.settings_dialog.mode_switch_disabled",
                                  ),
                                }),
                            ],
                          }),
                        ],
                      }),
                      jsxRuntimeExports.jsxs("div", {
                        style: { marginTop: "8px" },
                        children: [
                          jsxRuntimeExports.jsx("div", {
                            style: { fontWeight: "bold", marginBottom: "4px" },
                            children: Ce(
                              "common.settings_dialog.audio_device_settings",
                            ),
                          }),
                          jsxRuntimeExports.jsxs("div", {
                            style: {
                              marginLeft: "16px",
                              display: "flex",
                              flexDirection: "column",
                              gap: "12px",
                            },
                            children: [
                              jsxRuntimeExports.jsxs("div", {
                                children: [
                                  jsxRuntimeExports.jsx("label", {
                                    style: {
                                      display: "block",
                                      marginBottom: "5px",
                                    },
                                    children: Ce(
                                      "common.settings_dialog.input_device",
                                    ),
                                  }),
                                  Ut,
                                  nr,
                                ],
                              }),
                              jsxRuntimeExports.jsxs("div", {
                                children: [
                                  jsxRuntimeExports.jsx("label", {
                                    style: {
                                      display: "block",
                                      marginBottom: "5px",
                                    },
                                    children: Ce(
                                      "common.settings_dialog.output_device",
                                    ),
                                  }),
                                  mr,
                                  gr,
                                ],
                              }),
                              jsxRuntimeExports.jsxs("div", {
                                children: [
                                  jsxRuntimeExports.jsx("label", {
                                    style: {
                                      display: "block",
                                      marginBottom: "5px",
                                    },
                                    children: Ce(
                                      "common.settings_dialog.monitor_device",
                                    ),
                                  }),
                                  Zt,
                                  yr,
                                ],
                              }),
                              xr &&
                                jsxRuntimeExports.jsx("div", {
                                  style: { marginTop: "8px" },
                                  children: jsxRuntimeExports.jsxs("label", {
                                    style: {
                                      display: "flex",
                                      alignItems: "center",
                                      gap: "8px",
                                    },
                                    children: [
                                      jsxRuntimeExports.jsx("input", {
                                        type: "checkbox",
                                        checked: le.wasapi_exclude_emabled,
                                        onChange: (Fe) =>
                                          de({
                                            ...le,
                                            wasapi_exclude_emabled:
                                              Fe.target.checked,
                                          }),
                                      }),
                                      Ce(
                                        "common.settings_dialog.wasapi_exclusive_mode",
                                      ),
                                    ],
                                  }),
                                }),
                            ],
                          }),
                        ],
                      }),
                      jsxRuntimeExports.jsxs("div", {
                        style: { marginTop: "16px" },
                        children: [
                          jsxRuntimeExports.jsx("div", {
                            style: { fontWeight: "bold", marginBottom: "4px" },
                            children: Ce(
                              "common.settings_dialog.noise_suppression",
                            ),
                          }),
                          jsxRuntimeExports.jsxs("div", {
                            style: {
                              marginLeft: "16px",
                              display: "flex",
                              flexDirection: "column",
                              gap: "4px",
                            },
                            children: [
                              _e &&
                                jsxRuntimeExports.jsxs(
                                  jsxRuntimeExports.Fragment,
                                  {
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
                                            onChange: (Fe) =>
                                              O(Fe.target.checked),
                                          }),
                                          Ce(
                                            "common.settings_dialog.enable_echo_cancellation",
                                          ),
                                        ],
                                      }),
                                      jsxRuntimeExports.jsxs("label", {
                                        style: {
                                          display: "flex",
                                          alignItems: "center",
                                          gap: "8px",
                                        },
                                        children: [
                                          jsxRuntimeExports.jsx("input", {
                                            type: "checkbox",
                                            checked: H,
                                            onChange: (Fe) =>
                                              ee(Fe.target.checked),
                                          }),
                                          Ce(
                                            "common.settings_dialog.enable_noise_suppression",
                                          ),
                                        ],
                                      }),
                                      jsxRuntimeExports.jsxs("label", {
                                        style: {
                                          display: "flex",
                                          alignItems: "center",
                                          gap: "8px",
                                        },
                                        children: [
                                          jsxRuntimeExports.jsx("input", {
                                            type: "checkbox",
                                            checked: te,
                                            onChange: (Fe) =>
                                              ie(Fe.target.checked),
                                          }),
                                          Ce(
                                            "common.settings_dialog.enable_noise_suppression2",
                                          ),
                                        ],
                                      }),
                                    ],
                                  },
                                ),
                              jsxRuntimeExports.jsxs("div", {
                                style: {
                                  display: "flex",
                                  alignItems: "center",
                                  gap: "10px",
                                  marginTop: "8px",
                                },
                                children: [
                                  jsxRuntimeExports.jsx("span", {
                                    style: { minWidth: "80px" },
                                    children: Ce(
                                      "common.settings_dialog.noise_gate",
                                    ),
                                  }),
                                  jsxRuntimeExports.jsx("input", {
                                    type: "range",
                                    min: "0",
                                    max: "0.5",
                                    step: "0.001",
                                    value: le.noise_gate,
                                    onChange: async (Fe) => {
                                      await de({
                                        ...le,
                                        noise_gate: Number(Fe.target.value),
                                      });
                                    },
                                    style: { width: "100%" },
                                  }),
                                  jsxRuntimeExports.jsx("span", {
                                    style: {
                                      minWidth: "30px",
                                      textAlign: "right",
                                    },
                                    children: le.noise_gate,
                                  }),
                                ],
                              }),
                              jsxRuntimeExports.jsxs("div", {
                                style: { marginTop: "12px" },
                                children: [
                                  jsxRuntimeExports.jsxs("label", {
                                    style: {
                                      display: "flex",
                                      alignItems: "center",
                                      gap: "8px",
                                      marginBottom: "8px",
                                    },
                                    children: [
                                      jsxRuntimeExports.jsx("input", {
                                        type: "checkbox",
                                        checked: le.enable_high_pass_filter,
                                        onChange: async (Fe) => {
                                          await de({
                                            ...le,
                                            enable_high_pass_filter:
                                              Fe.target.checked,
                                          });
                                        },
                                      }),
                                      Ce(
                                        "common.settings_dialog.enable_high_pass_filter",
                                      ),
                                    ],
                                  }),
                                  le.enable_high_pass_filter &&
                                    jsxRuntimeExports.jsxs("div", {
                                      style: {
                                        display: "flex",
                                        alignItems: "center",
                                        gap: "10px",
                                        marginLeft: "24px",
                                      },
                                      children: [
                                        jsxRuntimeExports.jsx("span", {
                                          style: { minWidth: "80px" },
                                          children: Ce(
                                            "common.settings_dialog.cutoff",
                                          ),
                                        }),
                                        jsxRuntimeExports.jsx("input", {
                                          type: "range",
                                          min: "20",
                                          max: "200",
                                          step: "10",
                                          value: le.high_pass_filter_cutoff,
                                          onChange: async (Fe) => {
                                            await de({
                                              ...le,
                                              high_pass_filter_cutoff: Number(
                                                Fe.target.value,
                                              ),
                                            });
                                          },
                                          style: { width: "100%" },
                                        }),
                                        jsxRuntimeExports.jsxs("span", {
                                          style: {
                                            minWidth: "50px",
                                            textAlign: "right",
                                          },
                                          children: [
                                            le.high_pass_filter_cutoff,
                                            " Hz",
                                          ],
                                        }),
                                      ],
                                    }),
                                ],
                              }),
                              jsxRuntimeExports.jsxs("div", {
                                style: { marginTop: "12px" },
                                children: [
                                  jsxRuntimeExports.jsxs("label", {
                                    style: {
                                      display: "flex",
                                      alignItems: "center",
                                      gap: "8px",
                                      marginBottom: "8px",
                                    },
                                    children: [
                                      jsxRuntimeExports.jsx("input", {
                                        type: "checkbox",
                                        checked: le.enable_low_pass_filter,
                                        onChange: async (Fe) => {
                                          await de({
                                            ...le,
                                            enable_low_pass_filter:
                                              Fe.target.checked,
                                          });
                                        },
                                      }),
                                      Ce(
                                        "common.settings_dialog.enable_low_pass_filter",
                                      ),
                                    ],
                                  }),
                                  le.enable_low_pass_filter &&
                                    jsxRuntimeExports.jsxs("div", {
                                      style: {
                                        display: "flex",
                                        alignItems: "center",
                                        gap: "10px",
                                        marginLeft: "24px",
                                      },
                                      children: [
                                        jsxRuntimeExports.jsx("span", {
                                          style: { minWidth: "80px" },
                                          children: Ce(
                                            "common.settings_dialog.cutoff",
                                          ),
                                        }),
                                        jsxRuntimeExports.jsx("input", {
                                          type: "range",
                                          min: "3500",
                                          max: "15000",
                                          step: "500",
                                          value: le.low_pass_filter_cutoff,
                                          onChange: async (Fe) => {
                                            await de({
                                              ...le,
                                              low_pass_filter_cutoff: Number(
                                                Fe.target.value,
                                              ),
                                            });
                                          },
                                          style: { width: "100%" },
                                        }),
                                        jsxRuntimeExports.jsxs("span", {
                                          style: {
                                            minWidth: "50px",
                                            textAlign: "right",
                                          },
                                          children: [
                                            le.low_pass_filter_cutoff,
                                            " Hz",
                                          ],
                                        }),
                                      ],
                                    }),
                                ],
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
            jsxRuntimeExports.jsx(WaitingDialog, {
              open: ze,
              message: Ce("common.settings_dialog.changing_device_settings"),
            }),
          ],
        }),
      [
        S,
        C,
        Ce,
        le,
        de,
        Ut,
        mr,
        Zt,
        nr,
        gr,
        yr,
        xr,
        A,
        O,
        H,
        ee,
        te,
        ie,
        _e,
        ye,
        qe,
        se,
        ze,
      ],
    );
  };
