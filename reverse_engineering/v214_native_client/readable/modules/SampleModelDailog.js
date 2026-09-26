// Extracted declaration from ../main-ui.js:95754-96019.
// Navigation/reference excerpt; shared bundle dependencies are NOT imported.
// Edit ../main-ui.js for a runnable change. This is not original TS/TSX source.
const SampleModelDailog = ({ open: S, onClose: C, slotIndex: E }) => {
    const {
        samples: w,
        downloadSample: R,
        triggerToast: _,
        reloadServerSlotInfos: x,
        getTask: T,
      } = useAppRoot(),
      A = useTheme(),
      { t: O } = useTranslation(),
      [H, ee] = reactExports.useState({
        isDownloading: !1,
        progress: 0,
        currentSampleId: null,
        currentSampleName: "",
      }),
      te = reactExports.useCallback(
        async (ie) => {
          const ne = w.find((ae) => ae.id === ie);
          if (ne)
            try {
              ee({
                isDownloading: !0,
                progress: 0,
                currentSampleId: ie,
                currentSampleName: ne.name,
              });
              const ae = await R(E, ie),
                se = async (ce, fe) => {
                  setTimeout(async () => {
                    const pe = await T(ce);
                    if (pe === null) {
                      (console.warn("download sample task is null"),
                        ee((he) => ({ ...he, isDownloading: !1 })));
                      return;
                    }
                    const le = pe.progress || 0,
                      de = Math.round(le * 100);
                    if (
                      (ee((he) => ({ ...he, progress: de })),
                      pe.status === "done")
                    ) {
                      (ee((he) => ({ ...he, progress: 100 })),
                        x(),
                        _(
                          "success",
                          O("common.sample_model_dialog.download_success"),
                        ),
                        setTimeout(() => {
                          ee({
                            isDownloading: !1,
                            progress: 0,
                            currentSampleId: null,
                            currentSampleName: "",
                          });
                        }, 1500),
                        C());
                      return;
                    }
                    if (fe > 60) {
                      (console.warn("download sample check is timeout"),
                        ee((he) => ({ ...he, isDownloading: !1 })),
                        _(
                          "error",
                          O("common.sample_model_dialog.download_timeout"),
                        ));
                      return;
                    } else se(ce, fe + 1);
                  }, 1e3 * 1);
                };
              se(ae.id, 0);
            } catch {
              (ee((ae) => ({ ...ae, isDownloading: !1 })),
                _("error", O("common.sample_model_dialog.download_error")));
            }
        },
        [R, E, _, w, x, T, C, O],
      );
    return jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, {
      children: [
        jsxRuntimeExports.jsxs(Dialog, {
          open: S,
          onClose: C,
          maxWidth: "sm",
          fullWidth: !0,
          children: [
            jsxRuntimeExports.jsxs(DialogTitle, {
              sx: {
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              },
              children: [
                O("common.sample_model_dialog.title"),
                jsxRuntimeExports.jsx(IconButton, {
                  onClick: C,
                  size: "large",
                  children: jsxRuntimeExports.jsx(CloseIcon, {}),
                }),
              ],
            }),
            jsxRuntimeExports.jsx("div", {
              style: {
                padding: "0 24px 8px 24px",
                fontSize: 14,
                color: A.palette.text.secondary,
              },
              children: O("common.sample_model_dialog.slot_id", {
                slotIndex: E + 1,
              }),
            }),
            jsxRuntimeExports.jsx(DialogContent, {
              children: jsxRuntimeExports.jsxs("div", {
                style: {
                  display: "flex",
                  flexDirection: "column",
                  gap: "16px",
                },
                children: [
                  w.length === 0 &&
                    jsxRuntimeExports.jsx("div", {
                      children: O("common.sample_model_dialog.no_samples"),
                    }),
                  w.map((ie) =>
                    jsxRuntimeExports.jsxs(
                      "div",
                      {
                        style: {
                          display: "flex",
                          alignItems: "center",
                          gap: "16px",
                          borderBottom: `1px solid ${A.palette.divider}`,
                          padding: "8px 0",
                        },
                        children: [
                          jsxRuntimeExports.jsx("div", {
                            style: {
                              width: 64,
                              height: 64,
                              borderRadius: 8,
                              overflow: "hidden",
                              background: A.palette.background.default,
                              display: "flex",
                              alignItems: "center",
                              justifyContent: "center",
                            },
                            children: ie.icon_url
                              ? jsxRuntimeExports.jsx("img", {
                                  src: ie.icon_url,
                                  alt: ie.name,
                                  style: {
                                    width: "100%",
                                    height: "100%",
                                    objectFit: "cover",
                                  },
                                })
                              : jsxRuntimeExports.jsx("div", {
                                  style: {
                                    fontSize: 32,
                                    color: A.palette.text.secondary,
                                  },
                                  children: ie.name.charAt(0).toUpperCase(),
                                }),
                          }),
                          jsxRuntimeExports.jsxs("div", {
                            style: { flex: 1, minWidth: 0 },
                            children: [
                              jsxRuntimeExports.jsx("div", {
                                style: {
                                  fontWeight: "bold",
                                  fontSize: 16,
                                  color: A.palette.text.primary,
                                },
                                children: ie.name,
                              }),
                              jsxRuntimeExports.jsx("div", {
                                style: {
                                  fontSize: 13,
                                  color: A.palette.text.secondary,
                                  margin: "2px 0",
                                },
                                children: ie.description,
                              }),
                              jsxRuntimeExports.jsxs("div", {
                                style: {
                                  fontSize: 12,
                                  color: A.palette.text.secondary,
                                },
                                children: [
                                  ie.credit &&
                                    jsxRuntimeExports.jsxs("span", {
                                      children: [
                                        O("common.sample_model.credit"),
                                        " ",
                                        ie.credit,
                                        " ",
                                      ],
                                    }),
                                  ie.lang &&
                                    jsxRuntimeExports.jsxs("span", {
                                      children: [
                                        O("common.sample_model.language"),
                                        " ",
                                        ie.lang,
                                        " ",
                                      ],
                                    }),
                                  ie.tag &&
                                    ie.tag.length > 0 &&
                                    jsxRuntimeExports.jsxs("span", {
                                      children: [
                                        O("common.sample_model.tags"),
                                        " ",
                                        ie.tag.join(", "),
                                        " ",
                                      ],
                                    }),
                                  ie.terms_of_use_url &&
                                    jsxRuntimeExports.jsx("a", {
                                      href: ie.terms_of_use_url,
                                      target: "_blank",
                                      rel: "noopener noreferrer",
                                      style: {
                                        marginLeft: 8,
                                        color: A.palette.primary.main,
                                        textDecoration: "underline",
                                      },
                                      children: O(
                                        "common.sample_model.terms_of_use",
                                      ),
                                    }),
                                ],
                              }),
                            ],
                          }),
                          jsxRuntimeExports.jsx(Stack, {
                            direction: "row",
                            spacing: 1,
                            children: jsxRuntimeExports.jsx(Button, {
                              variant: "contained",
                              color: "primary",
                              onClick: () => te(ie.id),
                              disabled: H.isDownloading,
                              children: O(
                                "common.sample_model_dialog.download_button",
                              ),
                            }),
                          }),
                        ],
                      },
                      ie.id,
                    ),
                  ),
                ],
              }),
            }),
          ],
        }),
        jsxRuntimeExports.jsx(DownloadProgressDialog, {
          open: H.isDownloading,
          sampleName: H.currentSampleName,
          progress: H.progress,
        }),
      ],
    });
  };
