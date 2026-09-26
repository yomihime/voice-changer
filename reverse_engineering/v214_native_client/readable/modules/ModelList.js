// Extracted declaration from ../main-ui.js:96020-96146.
// Navigation/reference excerpt; shared bundle dependencies are NOT imported.
// Edit ../main-ui.js for a runnable change. This is not original TS/TSX source.
const ModelList = () => {
    const { t: S } = useTranslation(),
      { serverSlotInfos: C } = useAppRoot(),
      E = useTheme(),
      [w, R] = reactExports.useState(null),
      [_, x] = reactExports.useState(10),
      [T, A] = reactExports.useState(!1),
      [O, H] = reactExports.useState(null),
      [ee, te] = reactExports.useState(!1),
      [ie, ne] = reactExports.useState(null),
      ae = reactExports.useMemo(
        () => C.sort((pe, le) => pe.slot_index - le.slot_index),
        [C],
      );
    (reactExports.useEffect(() => {
      if (_ >= ae.length) return;
      const pe = setTimeout(() => {
        x((le) => Math.min(le + 5, ae.length));
      }, 100);
      return () => clearTimeout(pe);
    }, [_, ae.length]),
      reactExports.useEffect(() => {
        x(10);
      }, [ae.length]));
    const se = (pe) => {
        (H(pe), A(!0));
      },
      ce = (pe) => {
        (ne(pe), te(!0));
      },
      fe = reactExports.useMemo(
        () =>
          ae.slice(0, _).map((le, de) => {
            const he = w !== null && w !== de && le.voice_changer_type == null;
            return jsxRuntimeExports.jsxs(
              "div",
              {
                style: {
                  padding: "15px",
                  borderBottom: `1px solid ${E.palette.divider}`,
                  display: "flex",
                  alignItems: "center",
                  gap: "15px",
                  backgroundColor: he
                    ? E.palette.mode === "light"
                      ? "rgba(25, 118, 210, 0.08)"
                      : "rgba(144, 202, 249, 0.08)"
                    : "transparent",
                  transition: "background-color 0.2s",
                  width: "100%",
                },
                onClick: () => {
                  he && console.log("isMovingTarget", w, de);
                },
                children: [
                  jsxRuntimeExports.jsx(IconArea, { model: le }),
                  jsxRuntimeExports.jsx(InfoArea, { model: le }),
                  jsxRuntimeExports.jsx(RightButtonArea, {
                    model: le,
                    isMoving: w,
                    setIsMoving: R,
                    isMovingTarget: he,
                    onUploadClick: se,
                    onSampleModelClick: ce,
                  }),
                ],
              },
              de,
            );
          }),
        [ae, _, w, R, E.palette.divider, E.palette.mode],
      );
    return jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, {
      children: [
        jsxRuntimeExports.jsx(Box, {
          style: { maxHeight: "60vh", overflowY: "auto" },
          children: fe,
        }),
        w !== null &&
          jsxRuntimeExports.jsx("div", {
            style: {
              position: "sticky",
              bottom: 0,
              backgroundColor: E.palette.background.paper,
              padding: "15px",
              borderTop: `1px solid ${E.palette.divider}`,
              textAlign: "center",
            },
            children: jsxRuntimeExports.jsx(IconButton, {
              onClick: () => R(null),
              color: "default",
              sx: {
                height: "48px",
                minWidth: "160px",
                px: 2,
                border: "2px solid",
                borderColor: "grey.300",
                borderRadius: "12px",
                "&:hover": { borderColor: "primary.main" },
              },
              children: jsxRuntimeExports.jsx(Stack, {
                direction: "row",
                spacing: 1,
                alignItems: "center",
                children: jsxRuntimeExports.jsx("span", {
                  style: { fontSize: "14px", whiteSpace: "nowrap" },
                  children: S("common.model_editor.cancel_move"),
                }),
              }),
            }),
          }),
        T &&
          O !== null &&
          jsxRuntimeExports.jsx(ModelUploadDialog, {
            onClose: () => A(!1),
            slotIndex: O,
          }),
        ee &&
          ie !== null &&
          jsxRuntimeExports.jsx(SampleModelDailog, {
            open: ee,
            onClose: () => te(!1),
            slotIndex: ie,
          }),
      ],
    });
  };
