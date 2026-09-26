// Extracted declaration from ../main-ui.js:100915-101326.
// Navigation/reference excerpt; shared bundle dependencies are NOT imported.
// Edit ../main-ui.js for a runnable change. This is not original TS/TSX source.
const PerformanceArea = () => {
    const { t: S } = useTranslation(),
      {
        isClientInitialized: C,
        setVoiceChangerStatusListener: E,
        outputBufferSizeHistory: w,
        resetOutputBuffer: R,
      } = useAppState(),
      {
        currentSlotInfo: _,
        serverConfiguration: x,
        truncateOutputBuffer: T,
        refreshVoiceChangerIOQueue: A,
      } = useAppRoot(),
      O = reactExports.useRef(null),
      H = reactExports.useRef(null),
      ee = reactExports.useRef(null),
      te = reactExports.useRef(null),
      ie = reactExports.useRef(null),
      ne = reactExports.useRef(null),
      ae = reactExports.useRef(null),
      se = reactExports.useRef(null),
      ce = reactExports.useRef(null),
      fe = reactExports.useRef([]),
      pe = reactExports.useRef([]),
      le = (be) => (be === 0 ? "0.000" : be.toFixed(3)),
      de = (be, ve) => {
        if (!be) return;
        const xe = be.getContext("2d");
        if (!xe) return;
        (be.width === 0 && ((be.width = 300), (be.height = 25)),
          (xe.fillStyle = "#f0f0f0"),
          xe.fillRect(0, 0, be.width, be.height));
        const Ce = Math.max(0, Math.min(ve * be.width, be.width)),
          _e = xe.createLinearGradient(0, 0, be.width, 0);
        (_e.addColorStop(0, "#4CAF50"),
          _e.addColorStop(0.7, "#FFC107"),
          _e.addColorStop(1, "#F44336"),
          (xe.fillStyle = _e),
          xe.fillRect(0, 0, Ce, be.height),
          (xe.strokeStyle = "#ccc"),
          (xe.lineWidth = 1),
          xe.strokeRect(0, 0, be.width, be.height));
      },
      he = reactExports.useCallback(
        (be, ve, xe) => {
          if (!be) return;
          const Ce = be.getContext("2d");
          if (!Ce) return;
          if (
            ((be.width = 300),
            (be.height = 120),
            (Ce.fillStyle = "#f8f9fa"),
            Ce.fillRect(0, 0, be.width, be.height),
            ve.length === 0 && xe.length === 0)
          ) {
            ((Ce.strokeStyle = "#ddd"),
              (Ce.lineWidth = 1),
              Ce.strokeRect(0, 0, be.width, be.height));
            return;
          }
          const _e = ve.slice(-100),
            Be = xe.slice(-100),
            Ve = _e.map((Me) => Me.size).filter((Me) => Me !== null),
            ke = Be.map((Me) => Me.size).filter((Me) => Me !== null),
            Le = [...Ve, ...ke],
            qe = Le.length > 0 ? Math.max(...Le) : 0,
            ze = _?.chunk_sec || 0.1,
            Ae = ze * Y_AXIS_MULTIPLIER,
            Ne = Math.min(Math.max(qe, 0.1), Ae),
            We = { top: 10, right: 10, bottom: 20, left: 40 },
            Ie = be.width - We.left - We.right,
            $e = be.height - We.top - We.bottom;
          if (
            ((Ce.strokeStyle = "#ddd"),
            (Ce.lineWidth = 1),
            Ce.beginPath(),
            Ce.moveTo(We.left, We.top),
            Ce.lineTo(We.left, We.top + $e),
            Ce.stroke(),
            Ce.beginPath(),
            Ce.moveTo(We.left, We.top + $e),
            Ce.lineTo(We.left + Ie, We.top + $e),
            Ce.stroke(),
            (Ce.fillStyle = "#666"),
            (Ce.font = "12px Arial"),
            (Ce.textAlign = "right"),
            Ce.fillText("0s", We.left - 5, We.top + $e),
            Ce.fillText(`${Ne.toFixed(2)}s`, We.left - 5, We.top + 5),
            _e.length >= 2)
          ) {
            ((Ce.strokeStyle = "#FF9800"), (Ce.lineWidth = 2), Ce.beginPath());
            let Me = !0;
            (_e.forEach((Ge, er) => {
              if (Ge.size !== null) {
                const Ht = Math.min(Ge.size, Ne),
                  rr = We.left + (er / (_e.length - 1)) * Ie,
                  Jt = We.top + $e - (Ht / Ne) * $e;
                Me ? (Ce.moveTo(rr, Jt), (Me = !1)) : Ce.lineTo(rr, Jt);
              }
            }),
              Ce.stroke());
          }
          if (Be.length >= 2) {
            ((Ce.strokeStyle = "#2196F3"), (Ce.lineWidth = 2), Ce.beginPath());
            let Me = !0;
            (Be.forEach((Ge, er) => {
              if (Ge.size !== null) {
                const Ht = Math.min(Ge.size, Ne),
                  rr = We.left + (er / (Be.length - 1)) * Ie,
                  Jt = We.top + $e - (Ht / Ne) * $e;
                Me ? (Ce.moveTo(rr, Jt), (Me = !1)) : Ce.lineTo(rr, Jt);
              }
            }),
              Ce.stroke());
          }
          if (_?.chunk_sec) {
            const Me = We.top + $e - (ze / Ne) * $e;
            ((Ce.strokeStyle = "#ff6b6b"),
              (Ce.lineWidth = 4),
              Ce.setLineDash([5, 5]),
              Ce.beginPath(),
              Ce.moveTo(We.left, Me),
              Ce.lineTo(We.left + Ie, Me),
              Ce.stroke(),
              Ce.setLineDash([]),
              (Ce.fillStyle = "#ff6b6b"),
              (Ce.font = "12px Arial"),
              (Ce.textAlign = "left"),
              Ce.fillText(`${ze.toFixed(3)}s`, We.left + 5, Me - 5));
          }
          ((Ce.strokeStyle = "#ccc"),
            (Ce.lineWidth = 1),
            Ce.strokeRect(We.left, We.top, Ie, $e));
        },
        [_?.chunk_sec],
      ),
      me = (be, ve) => {
        if (!be) return;
        const xe = be.getContext("2d");
        if (!xe) return;
        ((be.width = 300),
          (be.height = 25),
          (xe.fillStyle = "#f8f9fa"),
          xe.fillRect(0, 0, be.width, be.height));
        const Ce = { left: 20, right: 20, top: 5, bottom: 5 },
          _e = be.width - Ce.left - Ce.right,
          Be = be.height - Ce.top - Ce.bottom,
          Ve = 0,
          ke = 2,
          Le = Ce.left + ((1 - Ve) / (ke - Ve)) * _e;
        ((xe.strokeStyle = "#ddd"),
          (xe.lineWidth = 1),
          xe.strokeRect(Ce.left, Ce.top, _e, Be),
          (xe.strokeStyle = "#ff4444"),
          (xe.lineWidth = 3),
          xe.beginPath(),
          xe.moveTo(Le, Ce.top),
          xe.lineTo(Le, Ce.top + Be),
          xe.stroke());
        const qe = Math.max(Ve, Math.min(ke, ve)),
          ze = Ce.left + ((qe - Ve) / (ke - Ve)) * _e;
        ((xe.strokeStyle = "#2196F3"),
          (xe.lineWidth = 2),
          xe.beginPath(),
          xe.moveTo(ze, Ce.top),
          xe.lineTo(ze, Ce.top + Be),
          xe.stroke(),
          (xe.fillStyle = "#666"),
          (xe.font = "10px Arial"),
          (xe.textAlign = "center"),
          xe.fillText("0", Ce.left, be.height - 2),
          xe.fillText("1", Le, be.height - 2),
          xe.fillText("2", Ce.left + _e, be.height - 2));
      };
    return (
      reactExports.useEffect(() => {
        if (C)
          return (
            console.log(
              logPrefix$3,
              "Setting up voice changer status listener",
            ),
            E({
              onRealtimeOutputStatus: (be) => {
                if (
                  (de(O.current, be.inputRms ?? 0),
                  H.current &&
                    (H.current.textContent = `入力音量 Level ${le(be.inputRms ?? 0)}`),
                  de(ee.current, be.outputRms ?? 0),
                  te.current &&
                    (te.current.textContent = `出力音量 Level ${le(be.outputRms ?? 0)}`),
                  be.outputBufferSize !== void 0 && x?.output_sample_rate)
                ) {
                  const ve = be.outputBufferSize / x.output_sample_rate,
                    xe = { timestamp: Date.now(), size: ve },
                    Ce = { timestamp: Date.now(), size: null };
                  ((pe.current = [...pe.current, xe].slice(-100)),
                    (fe.current = [...fe.current, Ce].slice(-100)),
                    he(ie.current, fe.current, pe.current),
                    ae.current &&
                      (ae.current.textContent = S(
                        "common.performance.output_buffer_label",
                        { time: ve.toFixed(3) },
                      )));
                }
              },
              onRealtimeProcessStatus: (be) => {
                if (
                  be.elapsedTime !== void 0 &&
                  be.outputSec !== void 0 &&
                  be.outputSec > 0
                ) {
                  const ve = be.elapsedTime / be.outputSec;
                  (me(se.current, ve),
                    ce.current &&
                      (ce.current.textContent = `RTF: ${ve.toFixed(3)}`));
                }
                if (be.inputBufferSize !== void 0 && x?.input_sample_rate) {
                  const ve = be.inputBufferSize / x.input_sample_rate,
                    xe = { timestamp: Date.now(), size: ve },
                    Ce = { timestamp: Date.now(), size: null };
                  ((fe.current = [...fe.current, xe].slice(-100)),
                    (pe.current = [...pe.current, Ce].slice(-100)),
                    he(ie.current, fe.current, pe.current),
                    ne.current &&
                      (ne.current.textContent = S(
                        "common.performance.input_buffer_label",
                        { time: ve.toFixed(3) },
                      )));
                }
              },
              onData: () => {},
            }),
            () => {
              E({
                onRealtimeOutputStatus: () => {},
                onRealtimeProcessStatus: () => {},
                onData: () => {},
              });
            }
          );
      }, [E, C, he, x.input_sample_rate, x.output_sample_rate, S]),
      reactExports.useEffect(() => {
        w.length > 0 && ((pe.current = w), he(ie.current, fe.current, w));
      }, [w, he]),
      reactExports.useEffect(() => {
        (de(O.current, 0),
          de(ee.current, 0),
          he(ie.current, [], []),
          me(se.current, 0));
      }, []),
      reactExports.useMemo(
        () =>
          jsxRuntimeExports.jsxs("div", {
            style: { display: "flex", flexDirection: "column", gap: "20px" },
            children: [
              jsxRuntimeExports.jsxs("div", {
                id: "input-volume",
                style: {
                  width: "320px",
                  borderRadius: "8px",
                  overflow: "hidden",
                  border: "1px solid #eee",
                  marginRight: "20px",
                  flexShrink: 0,
                  padding: "10px",
                  display: "flex",
                  flexDirection: "column",
                  gap: "5px",
                },
                children: [
                  jsxRuntimeExports.jsx("span", {
                    ref: H,
                    style: { fontSize: "12px", color: "#666" },
                    children: S("common.performance.input_volume_level"),
                  }),
                  jsxRuntimeExports.jsx("canvas", {
                    ref: O,
                    style: { height: "10px" },
                  }),
                ],
              }),
              jsxRuntimeExports.jsxs("div", {
                id: "output-volume",
                style: {
                  width: "320px",
                  borderRadius: "8px",
                  overflow: "hidden",
                  border: "1px solid #eee",
                  marginRight: "20px",
                  flexShrink: 0,
                  padding: "10px",
                  display: "flex",
                  flexDirection: "column",
                  gap: "5px",
                },
                children: [
                  jsxRuntimeExports.jsx("span", {
                    ref: te,
                    style: { fontSize: "12px", color: "#666" },
                    children: S("common.performance.output_volume_level"),
                  }),
                  jsxRuntimeExports.jsx("canvas", {
                    ref: ee,
                    style: { height: "10px" },
                  }),
                ],
              }),
              jsxRuntimeExports.jsxs("div", {
                style: {
                  width: "320px",
                  borderRadius: "8px",
                  overflow: "hidden",
                  border: "1px solid #eee",
                  marginRight: "20px",
                  flexShrink: 0,
                  padding: "10px",
                  display: "flex",
                  flexDirection: "column",
                  gap: "5px",
                },
                children: [
                  jsxRuntimeExports.jsx("span", {
                    ref: ne,
                    style: { fontSize: "12px", color: "#666" },
                    children: S("common.performance.input_buffer_initial"),
                  }),
                  jsxRuntimeExports.jsx("span", {
                    ref: ae,
                    style: { fontSize: "12px", color: "#666" },
                    children: S("common.performance.output_buffer_initial"),
                  }),
                  jsxRuntimeExports.jsxs("div", {
                    style: {
                      fontSize: "12px",
                      color: "#666",
                      marginTop: "5px",
                    },
                    children: [
                      jsxRuntimeExports.jsxs("span", {
                        style: { color: "#FF9800" },
                        children: ["■ ", S("common.performance.input_buffer")],
                      }),
                      jsxRuntimeExports.jsxs("span", {
                        style: { marginLeft: "10px", color: "#2196F3" },
                        children: ["■ ", S("common.performance.output_buffer")],
                      }),
                      jsxRuntimeExports.jsx("button", {
                        style: {
                          marginLeft: "15px",
                          padding: "2px 8px",
                          fontSize: "11px",
                          borderRadius: "4px",
                          border: "1px solid #ddd",
                          backgroundColor: "#f8f9fa",
                          color: "#666",
                          cursor: "pointer",
                          transition: "all 0.2s ease",
                        },
                        onMouseEnter: (be) => {
                          ((be.currentTarget.style.backgroundColor = "#e9ecef"),
                            (be.currentTarget.style.borderColor = "#adb5bd"));
                        },
                        onMouseLeave: (be) => {
                          ((be.currentTarget.style.backgroundColor = "#f8f9fa"),
                            (be.currentTarget.style.borderColor = "#ddd"));
                        },
                        onClick: () => {
                          (R(), T(), A());
                        },
                        children: S("common.performance.clear"),
                      }),
                    ],
                  }),
                  jsxRuntimeExports.jsx("canvas", {
                    ref: ie,
                    style: { height: "120px" },
                  }),
                ],
              }),
              jsxRuntimeExports.jsxs("div", {
                style: {
                  width: "320px",
                  borderRadius: "8px",
                  overflow: "hidden",
                  border: "1px solid #eee",
                  marginRight: "20px",
                  flexShrink: 0,
                  padding: "10px",
                  display: "flex",
                  flexDirection: "column",
                  gap: "5px",
                },
                children: [
                  jsxRuntimeExports.jsx("span", {
                    ref: ce,
                    style: { fontSize: "12px", color: "#666" },
                    children: "RTF: 0.000",
                  }),
                  jsxRuntimeExports.jsx("canvas", {
                    ref: se,
                    style: { height: "25px" },
                  }),
                ],
              }),
            ],
          }),
        [A, R, T, S],
      )
    );
  };
