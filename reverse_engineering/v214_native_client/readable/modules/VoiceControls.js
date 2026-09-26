// Extracted declaration from ../main-ui.js:100357-100884.
// Navigation/reference excerpt; shared bundle dependencies are NOT imported.
// Edit ../main-ui.js for a runnable change. This is not original TS/TSX source.
const VoiceControls = () => {
    const {
        currentSlotInfo: S,
        updateServerSlotInfo: C,
        serverConfiguration: E,
        updateServerConfiguration: w,
      } = useAppRoot(),
      { t: R } = useTranslation(),
      [_, x] = reactExports.useState(!0),
      { guiSetting: T } = useAppGuiSetting(),
      [A, O] = reactExports.useState(!1),
      [H, ee] = reactExports.useState(null),
      te = reactExports.useMemo(() => {
        if (S == null)
          return jsxRuntimeExports.jsx(jsxRuntimeExports.Fragment, {});
        if (S.voice_changer_type != "RVC")
          return jsxRuntimeExports.jsx(jsxRuntimeExports.Fragment, {});
        const le = S,
          de = le.pitch_estimator;
        return jsxRuntimeExports.jsxs("div", {
          style: {
            display: "flex",
            alignItems: "center",
            gap: "16px",
            marginTop: "8px",
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
                  title: R("common.voice_controls.pitch_estimator_tooltip"),
                  children: jsxRuntimeExports.jsx(GraphicEq, {}),
                }),
                jsxRuntimeExports.jsx("span", {
                  style: {
                    fontSize: "12px",
                    marginTop: "4px",
                    userSelect: "none",
                  },
                  children: R("common.voice_controls.pitch_estimator"),
                }),
              ],
            }),
            jsxRuntimeExports.jsx("select", {
              value: de,
              onChange: async (he) => {
                const me = he.target.value;
                le.pitch_estimator !== me &&
                  (await C({ ...le, pitch_estimator: me }));
              },
              style: { flex: 1, minWidth: "120px", padding: "4px" },
              children: Object.values(PitchEstimatorType).map((he) =>
                jsxRuntimeExports.jsx(
                  "option",
                  { value: he, children: he },
                  he,
                ),
              ),
            }),
          ],
        });
      }, [S, C, R]),
      ie = reactExports.useMemo(() => {
        if (S == null)
          return jsxRuntimeExports.jsx(jsxRuntimeExports.Fragment, {});
        if (S.voice_changer_type != "RVC")
          return jsxRuntimeExports.jsx(jsxRuntimeExports.Fragment, {});
        const le = S,
          de = le.override_embedder;
        return jsxRuntimeExports.jsxs("div", {
          style: {
            display: "flex",
            alignItems: "center",
            gap: "16px",
            marginTop: "8px",
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
                  title: R("common.voice_controls.embedder_override_tooltip"),
                  children: jsxRuntimeExports.jsx(EmbedderIcon, {}),
                }),
                jsxRuntimeExports.jsx("span", {
                  style: {
                    fontSize: "12px",
                    marginTop: "4px",
                    userSelect: "none",
                  },
                  children: R("common.voice_controls.embedder"),
                }),
              ],
            }),
            jsxRuntimeExports.jsxs("select", {
              value: de || "",
              onChange: async (he) => {
                const me = he.target.value === "" ? null : he.target.value;
                le.override_embedder !== me &&
                  (ee({
                    slotInfo: le,
                    newEmbedder: me,
                    selectElement: he.target,
                  }),
                  O(!0));
              },
              style: { flex: 1, minWidth: "120px", padding: "4px" },
              children: [
                jsxRuntimeExports.jsx("option", {
                  value: "",
                  children: R("common.voice_controls.embedder_default", {
                    embedder: le.embedder,
                  }),
                }),
                Object.values(EmbedderType).map((he) =>
                  jsxRuntimeExports.jsx(
                    "option",
                    { value: he, children: he },
                    he,
                  ),
                ),
              ],
            }),
          ],
        });
      }, [S, R]),
      ne = reactExports.useMemo(() => {
        if (S == null)
          return jsxRuntimeExports.jsx(jsxRuntimeExports.Fragment, {});
        let le = 0;
        if (S.voice_changer_type == "RVC") le = S.pitch_shift;
        else if (S.voice_changer_type == "Beatrice_v2") {
          const de = S;
          de.use_merged_speaker_embedding
            ? (le = de.merged_speaker_pitch_shifts[de.merged_speaker_id] || 0)
            : (le = de.pitch_shifts[de.dst_id] || 0);
        }
        return jsxRuntimeExports.jsxs("div", {
          style: { display: "flex", alignItems: "center", gap: "16px" },
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
                  title: R("common.controls.pitch_adjust"),
                  children: jsxRuntimeExports.jsx(Tune, {}),
                }),
                jsxRuntimeExports.jsx("span", {
                  style: {
                    fontSize: "12px",
                    marginTop: "4px",
                    userSelect: "none",
                  },
                  children: R("common.controls.pitch"),
                }),
              ],
            }),
            jsxRuntimeExports.jsx("input", {
              type: "range",
              min: "-24",
              max: "24",
              step: "1",
              value: le,
              onChange: (de) => {
                const he = parseInt(de.target.value);
                if (S != null) {
                  if (S.voice_changer_type == "RVC") {
                    const me = S;
                    ((me.pitch_shift = he), C(me));
                  } else if (S.voice_changer_type == "Beatrice_v2") {
                    const me = S;
                    if (me.use_merged_speaker_embedding) {
                      const ye = me.merged_speaker_pitch_shifts;
                      ye[me.merged_speaker_id] = he;
                    } else {
                      const ye = me.pitch_shifts;
                      ye[me.dst_id] = he;
                      for (let be = 0; be < me.dst_id; be++)
                        ye[be] || (ye[be] = 0);
                    }
                    C(me);
                  }
                }
              },
              style: { flex: 1 },
            }),
            jsxRuntimeExports.jsx("span", {
              style: { minWidth: "50px", textAlign: "right" },
              children: le,
            }),
          ],
        });
      }, [S, C, R]),
      ae = reactExports.useMemo(() => {
        if (S == null)
          return jsxRuntimeExports.jsx(jsxRuntimeExports.Fragment, {});
        if (S.voice_changer_type != "RVC")
          return jsxRuntimeExports.jsx(jsxRuntimeExports.Fragment, {});
        const le = S,
          de = le.index_ratio,
          he = le.index_file != null;
        return jsxRuntimeExports.jsxs("div", {
          style: { display: "flex", alignItems: "center", gap: "16px" },
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
                  title: R("common.controls.index_adjust"),
                  children: jsxRuntimeExports.jsx(IndexIcon, {}),
                }),
                jsxRuntimeExports.jsx("span", {
                  style: {
                    fontSize: "12px",
                    marginTop: "4px",
                    userSelect: "none",
                  },
                  children: R("common.controls.index"),
                }),
              ],
            }),
            jsxRuntimeExports.jsx("input", {
              type: "range",
              min: "0",
              max: "1",
              step: "0.1",
              value: de,
              disabled: !he,
              onChange: (me) => {
                if (de == null || !he) return;
                const ye = parseFloat(me.target.value),
                  be = S;
                ((be.index_ratio = ye), C(be));
              },
              style: {
                flex: 1,
                opacity: he ? 1 : 0.5,
                cursor: he ? "pointer" : "not-allowed",
              },
            }),
            jsxRuntimeExports.jsx("span", {
              style: {
                minWidth: "50px",
                textAlign: "right",
                opacity: he ? 1 : 0.5,
              },
              children: he ? de.toFixed(2) : "N/A",
            }),
          ],
        });
      }, [S, R, C]),
      se = reactExports.useMemo(() => {
        if (S == null)
          return jsxRuntimeExports.jsx(jsxRuntimeExports.Fragment, {});
        if (S.voice_changer_type != "Beatrice_v2")
          return jsxRuntimeExports.jsx(jsxRuntimeExports.Fragment, {});
        const le = S;
        let de = 0;
        return (
          le.use_merged_speaker_embedding
            ? (de = le.merged_speaker_formant_shifts[le.merged_speaker_id] || 0)
            : (de = le.formant_shifts[le.dst_id] || 0),
          jsxRuntimeExports.jsxs("div", {
            style: { display: "flex", alignItems: "center", gap: "16px" },
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
                    title: R("common.controls.formant_adjust"),
                    children: jsxRuntimeExports.jsx(GraphicEq, {}),
                  }),
                  jsxRuntimeExports.jsx("span", {
                    style: {
                      fontSize: "12px",
                      marginTop: "4px",
                      userSelect: "none",
                    },
                    children: R("common.controls.formant"),
                  }),
                ],
              }),
              jsxRuntimeExports.jsx("input", {
                type: "range",
                min: "-2",
                max: "2",
                step: "0.5",
                value: de,
                onChange: (he) => {
                  if (S == null || S.voice_changer_type != "Beatrice_v2")
                    return;
                  const me = parseFloat(he.target.value);
                  if ([-2, -1.5, -1, -0.5, 0, 0.5, 1, 1.5, 2].includes(me)) {
                    const be = S;
                    if (be.use_merged_speaker_embedding) {
                      const ve = be.merged_speaker_formant_shifts;
                      ve[be.merged_speaker_id] = me;
                    } else {
                      const ve = be.formant_shifts;
                      ve[be.dst_id] = me;
                      for (let xe = 0; xe < be.dst_id; xe++)
                        ve[xe] || (ve[xe] = 0);
                    }
                    C(be);
                  }
                },
                style: { flex: 1 },
              }),
              jsxRuntimeExports.jsx("span", {
                style: { minWidth: "50px", textAlign: "right" },
                children: de.toFixed(1),
              }),
            ],
          })
        );
      }, [S, R, C]),
      ce = reactExports.useMemo(
        () =>
          !T.inputChunkSec || T.inputChunkSec.length === 0 || S == null
            ? jsxRuntimeExports.jsx(jsxRuntimeExports.Fragment, {})
            : jsxRuntimeExports.jsxs("div", {
                style: {
                  display: "flex",
                  alignItems: "center",
                  gap: "16px",
                  marginTop: "8px",
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
                        title: R("common.controls.chunksec_adjust"),
                        children: jsxRuntimeExports.jsx(WaveformIcon, {}),
                      }),
                      jsxRuntimeExports.jsx("span", {
                        style: {
                          fontSize: "12px",
                          marginTop: "4px",
                          userSelect: "none",
                        },
                        children: R("common.controls.chunksec_label"),
                      }),
                    ],
                  }),
                  jsxRuntimeExports.jsx("select", {
                    value: S.chunk_sec,
                    onChange: async (le) => {
                      const de = Number(le.target.value);
                      S.chunk_sec !== de && (await C({ ...S, chunk_sec: de }));
                    },
                    style: { flex: 1, minWidth: "120px", padding: "4px" },
                    children: T.inputChunkSec.map((le) =>
                      jsxRuntimeExports.jsx(
                        "option",
                        {
                          value: le,
                          children: `${Math.round(48e3 * le)} [${le} sec]`,
                        },
                        le,
                      ),
                    ),
                  }),
                ],
              }),
        [T.inputChunkSec, S, C, R],
      ),
      fe = reactExports.useMemo(
        () =>
          !T.extraFrameSec || T.extraFrameSec.length === 0 || !E
            ? jsxRuntimeExports.jsx(jsxRuntimeExports.Fragment, {})
            : S?.voice_changer_type != "RVC"
              ? jsxRuntimeExports.jsx(jsxRuntimeExports.Fragment, {})
              : jsxRuntimeExports.jsxs("div", {
                  style: {
                    display: "flex",
                    alignItems: "center",
                    gap: "16px",
                    marginTop: "8px",
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
                          title: R("common.controls.extraframe_adjust"),
                          children: jsxRuntimeExports.jsx(WaveformPlusIcon, {}),
                        }),
                        jsxRuntimeExports.jsx("span", {
                          style: {
                            fontSize: "12px",
                            marginTop: "4px",
                            userSelect: "none",
                          },
                          children: R("common.controls.extraframesec_label"),
                        }),
                      ],
                    }),
                    jsxRuntimeExports.jsx("select", {
                      value: E.extra_frame_sec,
                      onChange: async (le) => {
                        const de = Number(le.target.value);
                        E.extra_frame_sec !== de &&
                          (await w({ ...E, extra_frame_sec: de }));
                      },
                      style: { flex: 1, minWidth: "120px", padding: "4px" },
                      children: T.extraFrameSec.map((le) =>
                        jsxRuntimeExports.jsx(
                          "option",
                          {
                            value: le,
                            children: `${Math.round(48e3 * le)} [${le} sec]`,
                          },
                          le,
                        ),
                      ),
                    }),
                  ],
                }),
        [T.extraFrameSec, E, w, R, S?.voice_changer_type],
      ),
      pe = reactExports.useMemo(
        () =>
          S == null
            ? jsxRuntimeExports.jsx(jsxRuntimeExports.Fragment, {})
            : jsxRuntimeExports.jsxs("div", {
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
                        style: {
                          display: "block",
                          fontWeight: "bold",
                          flex: 1,
                        },
                        children: R("common.controls.voice_control"),
                      }),
                      jsxRuntimeExports.jsx(IconButton, {
                        onClick: () => x(!_),
                        size: "small",
                        children: _
                          ? jsxRuntimeExports.jsx(ExpandLess, {})
                          : jsxRuntimeExports.jsx(ExpandMore, {}),
                      }),
                    ],
                  }),
                  _ &&
                    jsxRuntimeExports.jsxs("div", {
                      style: {
                        border: "1px solid #ddd",
                        borderRadius: "8px",
                        padding: "16px",
                        display: "flex",
                        flexDirection: "column",
                        gap: "16px",
                      },
                      children: [te, ne, ae, se, ce, fe, ie],
                    }),
                ],
              }),
        [S, te, ne, ae, se, ce, fe, ie, R, _],
      );
    return jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, {
      children: [
        pe,
        jsxRuntimeExports.jsx(ConfirmationDialog, {
          isOpen: A,
          title: R("common.voice_controls.embedder_change_title"),
          message: R("common.voice_controls.embedder_change_message"),
          confirmButtonText: R("common.voice_controls.embedder_change_confirm"),
          cancelButtonText: R("common.voice_controls.embedder_change_cancel"),
          onConfirm: async () => {
            (H &&
              (await C({ ...H.slotInfo, override_embedder: H.newEmbedder })),
              O(!1),
              ee(null));
          },
          onCancel: () => {
            (H && (H.selectElement.value = H.slotInfo.override_embedder || ""),
              O(!1),
              ee(null));
          },
        }),
      ],
    });
  };
