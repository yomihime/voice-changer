// Extracted declaration from ../main-ui.js:96725-96944.
// Navigation/reference excerpt; shared bundle dependencies are NOT imported.
// Edit ../main-ui.js for a runnable change. This is not original TS/TSX source.
const VoiceCharacterEditDialog = ({ open: S, onClose: C }) => {
    const {
        currentSlotInfo: E,
        updateBeatriceV2VoiceName: w,
        updateBeatriceV2VoiceDescription: R,
        uploadBeatriceV2VoiceIconFile: _,
        triggerToast: x,
      } = useAppRoot(),
      { t: T } = useTranslation(),
      A = reactExports.useMemo(() => {
        if (E == null || E.voice_changer_type === "RVC") return null;
        if (E.voice_changer_type === "Beatrice_v2") {
          const de = E;
          return de.model_info.voice[de.dst_id];
        }
        return (
          log$1(
            "error",
            logPrefix$5,
            "currentSlotInfo.voice_changer_type is not supported",
          ),
          null
        );
      }, [E]),
      [O, H] = reactExports.useState(A?.name || ""),
      [ee, te] = reactExports.useState(A?.description || ""),
      [ie, ne] = reactExports.useState(null),
      [ae, se] = reactExports.useState(""),
      [ce, fe] = reactExports.useState(""),
      pe = reactExports.useCallback(
        (de) => {
          if (E == null || E.voice_changer_type !== "Beatrice_v2") return null;
          const he = E,
            me = he.model_info.voice[de],
            be = he.toml_file.replace(/\\\\/g, "/").replace(/\\/g, "/");
          return (
            be.substring(0, be.lastIndexOf("/")) +
            "/" +
            me.portrait.path.split(/[/\\]/).pop()
          );
        },
        [E],
      );
    return (
      reactExports.useEffect(() => {
        if (S && A) {
          (H(A.name), te(A.description), ne(null), fe(""));
          const he = pe(E.dst_id);
          se(he || "./assets/icons/human.png");
        }
      }, [S, A, E, pe]),
      reactExports.useEffect(
        () => (
          S ||
            (ae && ae.startsWith("blob:") && URL.revokeObjectURL(ae),
            ce && URL.revokeObjectURL(ce)),
          () => {
            (ae && ae.startsWith("blob:") && URL.revokeObjectURL(ae),
              ce && URL.revokeObjectURL(ce));
          }
        ),
        [S, ae, ce],
      ),
      reactExports.useMemo(() => {
        if (!E || !A) return null;
        const de = () => {
            (ne(null), C());
          },
          he = async () => {
            if (!E || E.voice_changer_type !== "Beatrice_v2") {
              C();
              return;
            }
            const ye = E,
              be = ye.slot_index,
              ve = ye.dst_id;
            try {
              (O !== A?.name && (await w(be, ve, O)),
                ee !== A?.description && (await R(be, ve, ee)),
                ie && (await _(be, ve, ie, () => {})),
                x("success", T("common.voice_character_editor.save_success")));
            } catch {
              x("error", T("common.voice_character_editor.save_error"));
            }
            C();
          },
          me = (ye) => {
            if (ye.target.files && ye.target.files[0]) {
              const be = ye.target.files[0];
              (ne(be),
                ce && URL.revokeObjectURL(ce),
                fe(URL.createObjectURL(be)));
            }
          };
        return jsxRuntimeExports.jsxs(Dialog, {
          open: S,
          onClose: de,
          maxWidth: "sm",
          fullWidth: !0,
          children: [
            jsxRuntimeExports.jsx(DialogTitle, {
              children: T("common.voice_character_editor.title"),
            }),
            jsxRuntimeExports.jsx(DialogContent, {
              children: jsxRuntimeExports.jsxs(Box, {
                sx: { display: "flex", flexDirection: "column", gap: 2, mt: 2 },
                children: [
                  jsxRuntimeExports.jsx(TextField, {
                    label: T("common.voice_character_editor.name"),
                    value: O,
                    onChange: (ye) => H(ye.target.value),
                    fullWidth: !0,
                  }),
                  jsxRuntimeExports.jsx(TextField, {
                    label: T("common.voice_character_editor.description"),
                    value: ee,
                    onChange: (ye) => te(ye.target.value),
                    multiline: !0,
                    rows: 4,
                    fullWidth: !0,
                  }),
                  jsxRuntimeExports.jsxs(Box, {
                    children: [
                      jsxRuntimeExports.jsx("input", {
                        accept: "image/*",
                        style: { display: "none" },
                        id: "icon-file",
                        type: "file",
                        onChange: me,
                      }),
                      jsxRuntimeExports.jsx("label", {
                        htmlFor: "icon-file",
                        children: jsxRuntimeExports.jsx(Button, {
                          variant: "outlined",
                          component: "span",
                          children: T(
                            "common.voice_character_editor.select_icon",
                          ),
                        }),
                      }),
                      jsxRuntimeExports.jsxs(Box, {
                        sx: {
                          mt: 2,
                          display: "flex",
                          gap: 2,
                          alignItems: "center",
                        },
                        children: [
                          ae &&
                            jsxRuntimeExports.jsxs(Box, {
                              children: [
                                jsxRuntimeExports.jsx(Box, {
                                  sx: { mb: 1, color: "text.secondary" },
                                  children: T(
                                    "common.voice_character_edit_dialog.current_icon",
                                  ),
                                }),
                                jsxRuntimeExports.jsx("img", {
                                  src: ae,
                                  alt: T(
                                    "common.voice_character_edit_dialog.current_icon",
                                  ),
                                  style: {
                                    width: "100px",
                                    height: "100px",
                                    objectFit: "cover",
                                    borderRadius: "4px",
                                  },
                                }),
                              ],
                            }),
                          ce &&
                            jsxRuntimeExports.jsxs(Box, {
                              children: [
                                jsxRuntimeExports.jsx(Box, {
                                  sx: { mb: 1, color: "text.secondary" },
                                  children: T(
                                    "common.voice_character_edit_dialog.new_icon",
                                  ),
                                }),
                                jsxRuntimeExports.jsx("img", {
                                  src: ce,
                                  alt: T(
                                    "common.voice_character_edit_dialog.new_icon",
                                  ),
                                  style: {
                                    width: "100px",
                                    height: "100px",
                                    objectFit: "cover",
                                    borderRadius: "4px",
                                  },
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
            jsxRuntimeExports.jsxs(DialogActions, {
              children: [
                jsxRuntimeExports.jsx(Button, {
                  onClick: de,
                  children: T("common.voice_character_editor.cancel"),
                }),
                jsxRuntimeExports.jsx(Button, {
                  onClick: he,
                  variant: "contained",
                  color: "primary",
                  children: T("common.voice_character_editor.save"),
                }),
              ],
            }),
          ],
        });
      }, [S, A, O, ee, ae, ce, C, E, w, R, _, x, ie, T])
    );
  };
