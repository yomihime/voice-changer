// Extracted declaration from ../main-ui.js:96223-96651.
// Navigation/reference excerpt; shared bundle dependencies are NOT imported.
// Edit ../main-ui.js for a runnable change. This is not original TS/TSX source.
const ModelSelector = () => {
    const [S, C] = reactExports.useState(!1),
      [E, w] = reactExports.useState(!1),
      [R, _] = reactExports.useState(null),
      [x, T] = reactExports.useState(1),
      [A, O] = reactExports.useState(5),
      H = 120,
      ee = 15,
      {
        serverSlotInfos: te,
        currentSlotInfo: ie,
        updateServerConfiguration: ne,
        serverConfiguration: ae,
      } = useAppRoot(),
      se = useTheme(),
      { t: ce } = useTranslation(),
      fe = reactExports.useMemo(
        () => te.filter((be) => be.voice_changer_type !== null) || [],
        [te],
      );
    (reactExports.useEffect(() => {
      const be = () => {
        const ve = document.getElementById("model-card-row"),
          xe = ve ? ve.offsetWidth : window.innerWidth - 250,
          Ce = Math.max(1, Math.floor((xe + ee) / (H + ee)));
        O(Ce);
      };
      return (
        be(),
        window.addEventListener("resize", be),
        () => window.removeEventListener("resize", be)
      );
    }, []),
      reactExports.useEffect(() => {
        if (!ie) {
          T(1);
          return;
        }
        const be = fe.findIndex((Ce) => Ce.slot_index === ie.slot_index);
        if (be === -1) {
          T(1);
          return;
        }
        const ve = Math.floor(be / A) + 1,
          xe = Math.max(1, Math.ceil(fe.length / A));
        T(Math.min(ve, xe));
      }, [A, fe, ie]));
    const pe = reactExports.useMemo(() => {
        const be = (x - 1) * A;
        return fe.slice(be, be + A);
      }, [fe, x, A]),
      le = reactExports.useMemo(
        () => Math.max(1, Math.ceil(fe.length / A)),
        [fe.length, A],
      ),
      de = reactExports.useCallback(
        (be) => {
          (console.log("slotId", be), (ae.current_slot_index = be), ne(ae));
        },
        [ae, ne],
      ),
      he = reactExports.useCallback(() => {
        const be = te
          .filter((xe) => xe.voice_changer_type !== null)
          .map((xe) => xe.slot_index);
        let ve = null;
        for (let xe = 0; xe < MAX_SLOT_INDEX; xe++)
          if (!be.includes(xe)) {
            ve = xe;
            break;
          }
        ve !== null
          ? (_(ve), w(!0))
          : alert(ce("common.model_editor.no_empty_slot"));
      }, [te, _, w, ce]),
      me = reactExports.useMemo(
        () =>
          pe.map((be) => {
            const ve = be.icon_file
                ? "model_dir/" +
                  be.slot_index +
                  "/" +
                  be.icon_file.split(/[/\\]/).pop()
                : "./assets/icons/human.png",
              xe = `${be.slot_index + 1}.${be.name}`;
            return jsxRuntimeExports.jsxs(
              "div",
              {
                onClick: () => de(be.slot_index),
                style: {
                  position: "relative",
                  cursor: "pointer",
                  borderRadius: "8px",
                  overflow: "hidden",
                  border: `2px solid ${ie?.slot_index === be.slot_index ? se.palette.primary.main : "transparent"}`,
                  transition: "all 0.2s ease",
                  width: "120px",
                  height: "160px",
                  display: "flex",
                  flexDirection: "column",
                  background: se.palette.background.paper,
                },
                children: [
                  jsxRuntimeExports.jsx("div", {
                    style: {
                      width: "100%",
                      height: "120px",
                      position: "relative",
                      backgroundColor:
                        se.palette.mode === "light"
                          ? "#f0f2f5"
                          : se.palette.background.default,
                    },
                    children: be.icon_file
                      ? jsxRuntimeExports.jsx("img", {
                          src: ve,
                          alt: be.name || "",
                          style: {
                            position: "absolute",
                            width: "100%",
                            height: "100%",
                            objectFit: "cover",
                          },
                        })
                      : jsxRuntimeExports.jsx("div", {
                          style: {
                            position: "absolute",
                            width: "100%",
                            height: "100%",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            fontSize: "36px",
                            fontWeight: "bold",
                            color: se.palette.text.secondary,
                          },
                          children: be.name?.charAt(0).toUpperCase(),
                        }),
                  }),
                  jsxRuntimeExports.jsx("div", {
                    style: {
                      padding: "8px 4px 0 4px",
                      backgroundColor: se.palette.background.paper,
                      borderTop: `1px solid ${se.palette.divider}`,
                      height: "40px",
                      boxSizing: "border-box",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                    },
                    children: jsxRuntimeExports.jsx(Tooltip, {
                      title: xe,
                      placement: "top",
                      arrow: !0,
                      children: jsxRuntimeExports.jsx("div", {
                        style: {
                          fontWeight: "bold",
                          fontSize: "13px",
                          color: se.palette.text.primary,
                          textAlign: "center",
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          whiteSpace: "nowrap",
                          width: "100%",
                        },
                        children: xe,
                      }),
                    }),
                  }),
                ],
              },
              be.slot_index,
            );
          }),
        [pe, se, de, ie],
      );
    return reactExports.useMemo(
      () =>
        jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, {
          children: [
            jsxRuntimeExports.jsxs("div", {
              style: {
                border: `1px solid ${se.palette.divider}`,
                borderRadius: "8px",
                overflow: "hidden",
                backgroundColor: se.palette.background.paper,
                marginBottom: "20px",
              },
              children: [
                jsxRuntimeExports.jsxs("div", {
                  style: {
                    padding: "15px",
                    borderBottom: `1px solid ${se.palette.divider}`,
                    backgroundColor:
                      se.palette.mode === "light"
                        ? "#fafafa"
                        : se.palette.background.default,
                    fontWeight: "bold",
                    fontSize: "16px",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                  },
                  children: [
                    jsxRuntimeExports.jsx("span", {
                      children: ce("common.model.list_title"),
                    }),
                    jsxRuntimeExports.jsxs("span", {
                      style: {
                        fontSize: "14px",
                        color: se.palette.text.secondary,
                      },
                      children: [
                        fe.length,
                        " / ",
                        MAX_SLOT_INDEX,
                        " ",
                        ce("common.model.slots_in_use"),
                      ],
                    }),
                  ],
                }),
                jsxRuntimeExports.jsxs("div", {
                  style: { display: "flex" },
                  children: [
                    jsxRuntimeExports.jsx("div", {
                      style: { flex: "1", minWidth: 0 },
                      children:
                        fe.length === 0
                          ? jsxRuntimeExports.jsx("p", {
                              style: {
                                padding: "15px",
                                margin: 0,
                                color: se.palette.text.primary,
                              },
                              children: ce("common.model.no_models"),
                            })
                          : jsxRuntimeExports.jsxs("div", {
                              style: {
                                maxHeight: "500px",
                                overflowY: "auto",
                                padding: "15px",
                              },
                              children: [
                                jsxRuntimeExports.jsx("div", {
                                  id: "model-card-row",
                                  style: {
                                    display: "flex",
                                    flexDirection: "row",
                                    gap: "15px",
                                    width: "100%",
                                    overflowX: "auto",
                                  },
                                  children: me,
                                }),
                                jsxRuntimeExports.jsx(Box, {
                                  sx: {
                                    display: "flex",
                                    justifyContent: "center",
                                    mt: 2,
                                  },
                                  children: jsxRuntimeExports.jsx(Pagination, {
                                    count: le,
                                    page: x,
                                    onChange: (be, ve) => T(ve),
                                    color: "primary",
                                    shape: "rounded",
                                    size: "small",
                                  }),
                                }),
                              ],
                            }),
                    }),
                    jsxRuntimeExports.jsxs("div", {
                      style: {
                        width: "200px",
                        flexShrink: 0,
                        display: "flex",
                        flexDirection: "column",
                        gap: "10px",
                        padding: "15px",
                        backgroundColor: se.palette.background.paper,
                        borderLeft: `1px solid ${se.palette.divider}`,
                      },
                      children: [
                        jsxRuntimeExports.jsx(Box, {
                          sx: { minWidth: 0, display: "flex", width: "100%" },
                          children: jsxRuntimeExports.jsx(Tooltip, {
                            title: ce("common.model.upload.tooltip"),
                            children: jsxRuntimeExports.jsx(IconButton, {
                              onClick: he,
                              color: "default",
                              size: "large",
                              sx: {
                                height: "48px",
                                width: "100%",
                                px: 2,
                                border: "2px solid",
                                borderColor: "grey.300",
                                borderRadius: "12px",
                                "&:hover": { borderColor: "primary.main" },
                              },
                              children: jsxRuntimeExports.jsxs(Stack, {
                                direction: "row",
                                spacing: 1,
                                alignItems: "center",
                                children: [
                                  jsxRuntimeExports.jsxs("svg", {
                                    width: "16",
                                    height: "16",
                                    viewBox: "0 0 24 24",
                                    fill: "none",
                                    stroke: "currentColor",
                                    strokeWidth: "2",
                                    children: [
                                      jsxRuntimeExports.jsx("path", {
                                        d: "M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4",
                                      }),
                                      jsxRuntimeExports.jsx("polyline", {
                                        points: "17 8 12 3 7 8",
                                      }),
                                      jsxRuntimeExports.jsx("line", {
                                        x1: "12",
                                        y1: "3",
                                        x2: "12",
                                        y2: "15",
                                      }),
                                    ],
                                  }),
                                  jsxRuntimeExports.jsx("span", {
                                    style: {
                                      fontSize: "14px",
                                      whiteSpace: "nowrap",
                                    },
                                    children: ce("common.model.upload.button"),
                                  }),
                                ],
                              }),
                            }),
                          }),
                        }),
                        jsxRuntimeExports.jsx(Box, {
                          sx: { minWidth: 0, display: "flex", width: "100%" },
                          children: jsxRuntimeExports.jsx(Tooltip, {
                            title: ce("common.model.edit.tooltip"),
                            children: jsxRuntimeExports.jsx(IconButton, {
                              onClick: () => C(!0),
                              color: "default",
                              size: "large",
                              sx: {
                                height: "48px",
                                width: "100%",
                                px: 2,
                                border: "2px solid",
                                borderColor: "grey.300",
                                borderRadius: "12px",
                                "&:hover": { borderColor: "primary.main" },
                              },
                              children: jsxRuntimeExports.jsxs(Stack, {
                                direction: "row",
                                spacing: 1,
                                alignItems: "center",
                                children: [
                                  jsxRuntimeExports.jsxs("svg", {
                                    width: "16",
                                    height: "16",
                                    viewBox: "0 0 24 24",
                                    fill: "none",
                                    stroke: "currentColor",
                                    strokeWidth: "2",
                                    children: [
                                      jsxRuntimeExports.jsx("path", {
                                        d: "M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7",
                                      }),
                                      jsxRuntimeExports.jsx("path", {
                                        d: "M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z",
                                      }),
                                    ],
                                  }),
                                  jsxRuntimeExports.jsx("span", {
                                    style: {
                                      fontSize: "14px",
                                      whiteSpace: "nowrap",
                                    },
                                    children: ce("common.model.edit.button"),
                                  }),
                                ],
                              }),
                            }),
                          }),
                        }),
                      ],
                    }),
                  ],
                }),
              ],
            }),
            S
              ? jsxRuntimeExports.jsx(ModelEditDialog, { onClose: () => C(!1) })
              : null,
            E &&
              R !== null &&
              jsxRuntimeExports.jsx(ModelUploadDialog, {
                onClose: () => w(!1),
                slotIndex: R,
              }),
          ],
        }),
      [
        me,
        S,
        C,
        E,
        R,
        fe.length,
        ce,
        se.palette.background.default,
        se.palette.background.paper,
        se.palette.divider,
        se.palette.mode,
        se.palette.text.primary,
        se.palette.text.secondary,
        he,
        x,
        le,
        T,
      ],
    );
  };
