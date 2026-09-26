// Extracted declaration from ../main-ui.js:99128-99818.
// Navigation/reference excerpt; shared bundle dependencies are NOT imported.
// Edit ../main-ui.js for a runnable change. This is not original TS/TSX source.
const InputControls = () => {
    const {
        setInputAudio: S,
        inputAudioType: C,
        setInputAudioType: E,
        selectedInputAudioDeviceId: w,
        showSampleAudioButton: R,
      } = useAppState(),
      {
        audioContext: _,
        serverConfiguration: x,
        serverAudioInputDevices: T,
        audioInputs: A,
        setLocalVoiceChangerDummyInput: O,
      } = useAppRoot(),
      H = useTheme(),
      { t: ee } = useTranslation(),
      te = reactExports.useRef(null),
      [ie, ne] = reactExports.useState(!1),
      [ae, se] = reactExports.useState(!1),
      [ce, fe] = reactExports.useState(!1),
      [pe, le] = reactExports.useState({}),
      [de, he] = reactExports.useState(""),
      [me, ye] = reactExports.useState(null),
      be = reactExports.useRef(null),
      ve = x.voice_changer_input_mode === VoiceChangerInputMode.server;
    (reactExports.useEffect(() => {
      (async () => {
        try {
          const Me = await (
            await fetch("./assets/voices/sample_voices.json")
          ).json();
          le(Me);
        } catch ($e) {
          console.error(ee("common.controls.sample_voices_load_failed"), $e);
        }
      })();
    }, [ee]),
      reactExports.useEffect(() => {
        ve &&
          (C === InputAudioType.FILE || C === InputAudioType.CAPTURE) &&
          E(InputAudioType.MICROPHONE);
      }, [ve, C, E]));
    const xe = T.find((Ie) => Ie.index === x.audio_input_device_index),
      Ce = A.find((Ie) => Ie.deviceId === w);
    (reactExports.useEffect(() => {
      if (
        (console.log(ee("common.controls.useeffect_log"), me, C),
        _ == null || me == null || C !== InputAudioType.FILE)
      )
        return;
      const Ie = document.getElementById(AUDIO_ELEMENT_FOR_INPUT_MEDIA);
      if (Ie == null) return;
      (Ie.pause(),
        (Ie.srcObject = null),
        (Ie.src = URL.createObjectURL(me)),
        Ie.play(),
        be.current || (be.current = _.createMediaElementSource(Ie)),
        be.current.mediaElement != Ie &&
          (be.current = _.createMediaElementSource(Ie)));
      const $e = _.createMediaStreamDestination();
      (be.current.connect($e), S($e.stream));
      const Me = document.getElementById(
        AUDIO_ELEMENT_FOR_INPUT_MEDIA_ECHOBACK,
      );
      ((Me.srcObject = $e.stream), Me.play());
    }, [me, _, S, C, ee]),
      reactExports.useEffect(() => {
        if (
          _ == null ||
          C !== InputAudioType.SAMPLE ||
          de.length == 0 ||
          pe[de] == null
        )
          return;
        const Ie = document.getElementById(AUDIO_ELEMENT_FOR_INPUT_MEDIA);
        if (Ie == null) {
          console.error(ee("common.controls.audio_element_null"));
          return;
        }
        (Ie.pause(),
          (Ie.srcObject = null),
          C === InputAudioType.SAMPLE ? (Ie.src = pe[de]) : (Ie.src = ""),
          Ie.play(),
          be.current || (be.current = _.createMediaElementSource(Ie)),
          be.current.mediaElement != Ie &&
            (be.current = _.createMediaElementSource(Ie)));
        const $e = _.createMediaStreamDestination();
        (be.current.connect($e), S($e.stream));
        const Me = document.getElementById(
          AUDIO_ELEMENT_FOR_INPUT_MEDIA_ECHOBACK,
        );
        ((Me.srcObject = $e.stream), Me.play());
      }, [_, de, pe, S, C, ee]));
    const _e = reactExports.useCallback(
      async (Ie) => {
        try {
          let $e = Ie;
          (/^https?:\/\//.test($e) ||
            ($e = new URL($e, window.location.href).href),
            O($e));
        } catch ($e) {
          console.error(ee("common.controls.sample_send_failed"), $e);
        }
      },
      [O, ee],
    );
    (reactExports.useEffect(() => {
      const Ie = document.getElementById(
        AUDIO_ELEMENT_FOR_INPUT_MEDIA_ECHOBACK,
      );
      (console.log("Echoback muted:::", ae, _),
        Ie != null && (ae ? (Ie.muted = !1) : (Ie.muted = !0)));
    }, [ae, _, me, de, C]),
      reactExports.useEffect(() => {
        const Ie = document.getElementById(AUDIO_ELEMENT_FOR_INPUT_MEDIA);
        Ie != null && (Ie.loop = ce);
      }, [ce]));
    const Be = reactExports.useMemo(
        () =>
          C !== InputAudioType.MICROPHONE
            ? null
            : ve == !0
              ? jsxRuntimeExports.jsx("div", {
                  style: { marginBottom: "20px", marginTop: "10px" },
                  children: jsxRuntimeExports.jsxs("label", {
                    style: {
                      display: "block",
                      marginBottom: "5px",
                      fontSize: "12px",
                    },
                    children: [
                      ee("common.controls.mic_device"),
                      ":",
                      " ",
                      xe
                        ? `${xe.name} (ID: ${xe.index})`
                        : ee("common.controls.no_device"),
                    ],
                  }),
                })
              : jsxRuntimeExports.jsx("div", {
                  style: { marginBottom: "20px", marginTop: "10px" },
                  children: jsxRuntimeExports.jsxs("label", {
                    style: {
                      display: "block",
                      marginBottom: "5px",
                      fontSize: "12px",
                    },
                    children: [
                      ee("common.controls.mic_device"),
                      ":",
                      " ",
                      Ce ? `${Ce.label} (ID: ${Ce.deviceId})` : w,
                    ],
                  }),
                }),
        [ee, ve, xe, Ce, w, C],
      ),
      Ve = reactExports.useMemo(
        () =>
          jsxRuntimeExports.jsx(Tooltip, {
            title: ee(
              ce
                ? "common.controls.loop_disable"
                : "common.controls.loop_enable",
            ),
            children: jsxRuntimeExports.jsx(IconButton, {
              onClick: () => fe(!ce),
              color: ce ? "primary" : "default",
              size: "large",
              sx: {
                height: "40px",
                width: "40px",
                minWidth: "40px",
                border: "2px solid",
                borderColor: ce ? "primary.main" : "grey.300",
                borderRadius: "8px",
                "&:hover": { borderColor: "primary.main" },
              },
              children: jsxRuntimeExports.jsx(Loop, {
                sx: { fontSize: "20px" },
              }),
            }),
          }),
        [ce, ee],
      ),
      ke = reactExports.useMemo(
        () =>
          jsxRuntimeExports.jsx(Tooltip, {
            title: ee(
              ae
                ? "common.controls.echoback_disable"
                : "common.controls.echoback_enable",
            ),
            children: jsxRuntimeExports.jsx(IconButton, {
              onClick: () => se(!ae),
              color: ae ? "primary" : "default",
              size: "large",
              sx: {
                height: "40px",
                width: "40px",
                minWidth: "40px",
                border: "2px solid",
                borderColor: ae ? "primary.main" : "grey.300",
                borderRadius: "8px",
                "&:hover": { borderColor: "primary.main" },
              },
              children: jsxRuntimeExports.jsx(NetworkPing, {
                sx: { fontSize: "20px" },
              }),
            }),
          }),
        [ae, ee],
      ),
      Le = reactExports.useMemo(
        () =>
          C !== InputAudioType.FILE
            ? null
            : jsxRuntimeExports.jsxs("div", {
                style: { marginBottom: "20px" },
                children: [
                  jsxRuntimeExports.jsx("div", {
                    onClick: () => {
                      const Ie = document.createElement("input");
                      ((Ie.type = "file"),
                        (Ie.onchange = ($e) => {
                          const Me = $e.target.files;
                          Me && ye(Me[0]);
                        }),
                        Ie.click());
                    },
                    onDragOver: (Ie) => {
                      (Ie.preventDefault(), Ie.stopPropagation());
                    },
                    onDrop: (Ie) => {
                      (Ie.preventDefault(), Ie.stopPropagation());
                      const $e = Ie.dataTransfer.files;
                      $e.length > 0 && ye($e[0]);
                    },
                    style: {
                      width: "100%",
                      height: "100px",
                      border: "2px dashed #ccc",
                      borderRadius: "8px",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      cursor: "pointer",
                      backgroundColor:
                        H.palette.mode === "light" ? "#f8f8f8" : "#2f2f2f",
                      marginBottom: "10px",
                      marginTop: "10px",
                    },
                    children: jsxRuntimeExports.jsxs("div", {
                      style: { textAlign: "center" },
                      children: [
                        jsxRuntimeExports.jsx("div", {
                          children: ee("common.controls.drop_files"),
                        }),
                        jsxRuntimeExports.jsx("div", {
                          style: { fontSize: "12px", color: "#666" },
                          children: ee("common.controls.supported_formats"),
                        }),
                      ],
                    }),
                  }),
                  jsxRuntimeExports.jsxs("div", {
                    style: {
                      display: "flex",
                      alignItems: "center",
                      gap: "16px",
                      marginBottom: "20px",
                    },
                    children: [
                      jsxRuntimeExports.jsx("audio", {
                        id: AUDIO_ELEMENT_FOR_INPUT_MEDIA,
                        controls: !0,
                        style: { flex: 1, height: "40px" },
                      }),
                      Ve,
                      ke,
                    ],
                  }),
                  jsxRuntimeExports.jsx("audio", {
                    id: AUDIO_ELEMENT_FOR_INPUT_MEDIA_ECHOBACK,
                    controls: !0,
                    style: { width: "100%", marginBottom: "20px" },
                    hidden: !0,
                  }),
                ],
              }),
        [ee, C, ke, Ve, H.palette.mode],
      ),
      qe = reactExports.useMemo(
        () =>
          C !== InputAudioType.CAPTURE
            ? null
            : jsxRuntimeExports.jsx("div", {
                style: { marginBottom: "20px" },
                children: jsxRuntimeExports.jsx(IconButton, {
                  onClick: () => {
                    (async () => {
                      if (
                        (te.current &&
                          (te.current.getTracks().forEach(($e) => {
                            $e.stop();
                          }),
                          (te.current = null)),
                        ie == !0)
                      ) {
                        ne(!1);
                        return;
                      }
                      try {
                        if (isDesktopApp()) {
                          const $e = {
                            audio: {
                              mandatory: { chromeMediaSource: "desktop" },
                            },
                            video: {
                              mandatory: { chromeMediaSource: "desktop" },
                            },
                          };
                          te.current =
                            await navigator.mediaDevices.getUserMedia($e);
                        } else
                          te.current =
                            await navigator.mediaDevices.getDisplayMedia({
                              video: !0,
                              audio: !0,
                            });
                      } catch ($e) {
                        console.error(ee("common.controls.capture_error"), $e);
                        return;
                      }
                      if (!te.current) {
                        console.error(
                          ee("common.controls.capture_no_media_stream"),
                        );
                        return;
                      }
                      if (te.current.getAudioTracks().length == 0) {
                        (te.current.getTracks().forEach(($e) => {
                          $e.stop();
                        }),
                          (te.current = null),
                          console.error(
                            ee("common.controls.capture_no_audio_track"),
                          ));
                        return;
                      }
                      try {
                        S(te.current);
                      } catch ($e) {
                        console.error(ee("common.controls.capture_error"), $e);
                      }
                      ne(!0);
                    })();
                  },
                  color: ie ? "primary" : "default",
                  size: "large",
                  sx: {
                    width: "100%",
                    height: "80px",
                    minWidth: "100px",
                    px: 2,
                    border: "2px solid",
                    borderColor: ie ? "primary.main" : "grey.300",
                    borderRadius: "8px",
                    "&:hover": { borderColor: "primary.main" },
                    marginTop: "10px",
                  },
                  children: jsxRuntimeExports.jsxs(Stack, {
                    alignItems: "center",
                    children: [
                      jsxRuntimeExports.jsx(ScreenShare, {}),
                      jsxRuntimeExports.jsx("span", {
                        style: {
                          fontSize: "12px",
                          marginTop: "4px",
                          whiteSpace: "nowrap",
                        },
                        children: ee(
                          ie
                            ? "common.controls.stop_capture"
                            : "common.controls.screen_capture",
                        ),
                      }),
                    ],
                  }),
                }),
              }),
        [ee, C, ie, S],
      ),
      ze = reactExports.useMemo(
        () =>
          C !== InputAudioType.SAMPLE || ve != !0 || de == ""
            ? null
            : jsxRuntimeExports.jsxs("div", {
                style: {
                  display: "flex",
                  gap: "8px",
                  justifyContent: "flex-end",
                  marginBottom: "10px",
                },
                children: [
                  jsxRuntimeExports.jsx(Button, {
                    variant: "outlined",
                    startIcon: jsxRuntimeExports.jsx(PlayArrow, {}),
                    onClick: () => {
                      pe[de] &&
                        new Audio(pe[de]).play().catch(($e) => {
                          console.error(
                            ee("common.controls.test_audio_play_failed"),
                            $e,
                          );
                        });
                    },
                    sx: { height: "40px", minWidth: "120px" },
                    children: ee("common.controls.test_play"),
                  }),
                  jsxRuntimeExports.jsx(Button, {
                    variant: "contained",
                    startIcon: jsxRuntimeExports.jsx(Send, {}),
                    onClick: () => {
                      pe[de] && _e(pe[de]);
                    },
                    sx: { height: "40px", minWidth: "120px" },
                    children: ee("common.controls.send_sample"),
                  }),
                ],
              }),
        [_e, C, ve, pe, de, ee],
      ),
      Ae = reactExports.useMemo(
        () =>
          C !== InputAudioType.SAMPLE || ve == !0 || de == ""
            ? null
            : jsxRuntimeExports.jsxs("div", {
                style: {
                  display: "flex",
                  alignItems: "center",
                  gap: "16px",
                  marginBottom: "20px",
                },
                children: [
                  jsxRuntimeExports.jsx("audio", {
                    id: AUDIO_ELEMENT_FOR_INPUT_MEDIA,
                    controls: !0,
                    style: { flex: 1, height: "40px" },
                  }),
                  Ve,
                  ke,
                ],
              }),
        [ke, Ve, C, ve, de],
      ),
      Ne = reactExports.useMemo(
        () =>
          C !== InputAudioType.SAMPLE
            ? null
            : jsxRuntimeExports.jsxs("div", {
                style: { marginBottom: "20px" },
                children: [
                  jsxRuntimeExports.jsx(FormControl, {
                    fullWidth: !0,
                    style: { marginBottom: "10px", marginTop: "10px" },
                    children: jsxRuntimeExports.jsxs(Select, {
                      value: de,
                      onChange: (Ie) => {
                        const $e = Ie.target.value;
                        he($e);
                      },
                      displayEmpty: !0,
                      sx: { height: "40px" },
                      children: [
                        jsxRuntimeExports.jsx(MenuItem, {
                          value: "",
                          children: jsxRuntimeExports.jsx("em", {
                            children: ee("common.controls.select_sample"),
                          }),
                        }),
                        Object.keys(pe).map((Ie) =>
                          jsxRuntimeExports.jsx(
                            MenuItem,
                            { value: Ie, children: Ie },
                            Ie,
                          ),
                        ),
                      ],
                    }),
                  }),
                  ze,
                  Ae,
                  jsxRuntimeExports.jsx("audio", {
                    id: AUDIO_ELEMENT_FOR_INPUT_MEDIA_ECHOBACK,
                    controls: !0,
                    style: { width: "100%", marginBottom: "20px" },
                    hidden: !0,
                  }),
                ],
              }),
        [C, pe, de, ee, ze, Ae],
      );
    return reactExports.useMemo(
      () =>
        jsxRuntimeExports.jsxs("div", {
          children: [
            jsxRuntimeExports.jsx("label", {
              style: { display: "block", fontWeight: "bold", flex: 1 },
              children: ee("common.controls.input_type"),
            }),
            jsxRuntimeExports.jsxs(Stack, {
              direction: "row",
              spacing: 2,
              justifyContent: "flex-start",
              children: [
                jsxRuntimeExports.jsx(Tooltip, {
                  title: ee("common.controls.microphone_input"),
                  children: jsxRuntimeExports.jsx(IconButton, {
                    onClick: () => E("microphone"),
                    color: C === "microphone" ? "primary" : "default",
                    size: "large",
                    sx: {
                      width: "70px",
                      minWidth: "70px",
                      height: "60px",
                      border: "2px solid",
                      borderColor:
                        C === "microphone" ? "primary.main" : "grey.300",
                      borderRadius: "8px",
                      "&:hover": { borderColor: "primary.main" },
                    },
                    children: jsxRuntimeExports.jsxs(Stack, {
                      alignItems: "center",
                      children: [
                        jsxRuntimeExports.jsx(Mic, {
                          sx: { fontSize: "1.5rem" },
                        }),
                        jsxRuntimeExports.jsx("span", {
                          style: {
                            fontSize: "11px",
                            marginTop: "2px",
                            overflow: "hidden",
                            textOverflow: "ellipsis",
                            whiteSpace: "nowrap",
                            width: "100%",
                            textAlign: "center",
                            paddingLeft: "2px",
                            paddingRight: "2px",
                          },
                          children: ee("common.controls.microphone"),
                        }),
                      ],
                    }),
                  }),
                }),
                jsxRuntimeExports.jsx(Tooltip, {
                  title: ee("common.controls.file_input"),
                  children: jsxRuntimeExports.jsx(IconButton, {
                    onClick: () => E("file"),
                    color: C === "file" ? "primary" : "default",
                    size: "large",
                    disabled: ve,
                    sx: {
                      width: "70px",
                      minWidth: "70px",
                      height: "60px",
                      border: "2px solid",
                      borderColor: C === "file" ? "primary.main" : "grey.300",
                      borderRadius: "8px",
                      "&:hover": { borderColor: "primary.main" },
                    },
                    children: jsxRuntimeExports.jsxs(Stack, {
                      alignItems: "center",
                      children: [
                        jsxRuntimeExports.jsx(AudioFile, {
                          sx: { fontSize: "1.5rem" },
                        }),
                        jsxRuntimeExports.jsx("span", {
                          style: {
                            fontSize: "11px",
                            marginTop: "2px",
                            overflow: "hidden",
                            textOverflow: "ellipsis",
                            whiteSpace: "nowrap",
                            width: "100%",
                            textAlign: "center",
                            paddingLeft: "2px",
                            paddingRight: "2px",
                          },
                          children: ee("common.controls.file"),
                        }),
                      ],
                    }),
                  }),
                }),
                jsxRuntimeExports.jsx(Tooltip, {
                  title: ee("common.controls.screen_capture"),
                  children: jsxRuntimeExports.jsx(IconButton, {
                    onClick: () => E("capture"),
                    color: C === "capture" ? "primary" : "default",
                    size: "large",
                    disabled: ve,
                    sx: {
                      width: "70px",
                      minWidth: "70px",
                      height: "60px",
                      border: "2px solid",
                      borderColor:
                        C === "capture" ? "primary.main" : "grey.300",
                      borderRadius: "8px",
                      "&:hover": { borderColor: "primary.main" },
                    },
                    children: jsxRuntimeExports.jsxs(Stack, {
                      alignItems: "center",
                      children: [
                        jsxRuntimeExports.jsx(ScreenShare, {
                          sx: { fontSize: "1.5rem" },
                        }),
                        jsxRuntimeExports.jsx("span", {
                          style: {
                            fontSize: "11px",
                            marginTop: "2px",
                            overflow: "hidden",
                            textOverflow: "ellipsis",
                            whiteSpace: "nowrap",
                            width: "100%",
                            textAlign: "center",
                            paddingLeft: "2px",
                            paddingRight: "2px",
                          },
                          children: ee("common.controls.capture"),
                        }),
                      ],
                    }),
                  }),
                }),
                R &&
                  jsxRuntimeExports.jsx(Tooltip, {
                    title: ee("common.controls.sample_input"),
                    children: jsxRuntimeExports.jsx(IconButton, {
                      onClick: () => E("sample"),
                      color: C === "sample" ? "primary" : "default",
                      size: "large",
                      sx: {
                        width: "70px",
                        minWidth: "70px",
                        height: "60px",
                        border: "2px solid",
                        borderColor:
                          C === "sample" ? "primary.main" : "grey.300",
                        borderRadius: "8px",
                        "&:hover": { borderColor: "primary.main" },
                      },
                      children: jsxRuntimeExports.jsxs(Stack, {
                        alignItems: "center",
                        children: [
                          jsxRuntimeExports.jsx(LibraryMusic, {
                            sx: { fontSize: "1.5rem" },
                          }),
                          jsxRuntimeExports.jsx("span", {
                            style: {
                              fontSize: "11px",
                              marginTop: "2px",
                              overflow: "hidden",
                              textOverflow: "ellipsis",
                              whiteSpace: "nowrap",
                              width: "100%",
                              textAlign: "center",
                              paddingLeft: "2px",
                              paddingRight: "2px",
                            },
                            children: ee("common.controls.sample"),
                          }),
                        ],
                      }),
                    }),
                  }),
              ],
            }),
            Be,
            Le,
            qe,
            Ne,
          ],
        }),
      [E, ee, C, ve, Be, Le, qe, Ne, R],
    );
  };
