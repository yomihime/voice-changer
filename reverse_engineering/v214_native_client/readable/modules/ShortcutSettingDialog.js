// Extracted declaration from ../main-ui.js:101757-102211.
// Navigation/reference excerpt; shared bundle dependencies are NOT imported.
// Edit ../main-ui.js for a runnable change. This is not original TS/TSX source.
const ShortcutSettingDialog = ({ open: S, onClose: C }) => {
    const {
        config: E,
        updateShortcut: w,
        setShorcutEnabled: R,
        checkDuplicationKey: _,
        hotKeySettingError: x,
      } = useHotkey(),
      { t: T } = useTranslation(),
      [A, O] = reactExports.useState(null),
      [H, ee] = reactExports.useState(""),
      [te, ie] = reactExports.useState(null),
      [ne, ae] = reactExports.useState(null),
      [se, ce] = reactExports.useState(!1);
    reactExports.useEffect(() => {
      A === null && ne !== null && (R(ne), ae(null));
    }, [A, ne, R]);
    const fe = reactExports.useCallback(() => {
        (O(null), ee(""), ie(null), ce(!1));
      }, []),
      pe = reactExports.useCallback(
        async (ye, be) => {
          (ye.preventDefault(), ye.stopPropagation());
          const ve = [];
          (ye.shiftKey && ve.push("shift"),
            ye.ctrlKey && ve.push("control"),
            ye.altKey && ve.push("alt"),
            ye.metaKey && ve.push("meta"));
          const xe = ye.key;
          let Ce = !1;
          if (
            xe !== "Control" &&
            xe !== "Alt" &&
            xe !== "Shift" &&
            xe !== "Meta"
          )
            if (xe === " ") ve.push("Space");
            else if (xe === "Enter") ve.push("Enter");
            else if (xe === "Tab") ve.push("Tab");
            else if (xe === "Escape") {
              fe();
              return;
            } else if (xe === "Backspace") ve.push("Backspace");
            else if (xe === "Delete") ve.push("Delete");
            else if (xe === "ArrowUp") ve.push("ArrowUp");
            else if (xe === "ArrowDown") ve.push("ArrowDown");
            else if (xe === "ArrowLeft") ve.push("ArrowLeft");
            else if (xe === "ArrowRight") ve.push("ArrowRight");
            else if (xe.startsWith("F") && xe.length > 1) ve.push(xe);
            else if (xe.length === 1) {
              const _e = xe.toUpperCase();
              _e.match(/[A-Z]/)
                ? ve.push(`Key${_e}`)
                : _e.match(/[0-9]/)
                  ? ve.push(`Digit${_e}`)
                  : ve.push(xe);
            } else ve.push(xe);
          else Ce = !0;
          if ((console.log("🎯 duplicateError:11", ve), ve.length > 0)) {
            const _e = ve.join("+");
            if ((ee(_e), !Ce && E)) {
              const Be = _(be, _e);
              Be ? ie(Be) : (await w(be, _e), fe());
            }
          }
        },
        [E, w, _, fe],
      ),
      le = reactExports.useCallback(() => {
        fe();
      }, [fe]),
      de = reactExports.useCallback(
        (ye, be) => {
          (E && ne === null && (ae(E.enabled), R(!1)),
            O(ye),
            ee(be),
            ie(null),
            ce(!0));
        },
        [E, ne, R],
      ),
      he = reactExports.useCallback(() => {
        (A !== null && fe(), C());
      }, [A, fe, C]);
    return reactExports.useMemo(
      () =>
        E
          ? jsxRuntimeExports.jsxs(Dialog, {
              open: S,
              onClose: he,
              maxWidth: "md",
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
                      children: T("common.shortcut_settings.title"),
                    }),
                    jsxRuntimeExports.jsx("button", {
                      onClick: he,
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
                      x &&
                        jsxRuntimeExports.jsx("div", {
                          style: {
                            color: "red",
                            fontSize: "14px",
                            marginBottom: "16px",
                          },
                          children: x,
                        }),
                      jsxRuntimeExports.jsxs("div", {
                        children: [
                          jsxRuntimeExports.jsxs("label", {
                            style: {
                              display: "flex",
                              alignItems: "center",
                              gap: "8px",
                              opacity: se ? 0.5 : 1,
                              pointerEvents: se ? "none" : "auto",
                            },
                            children: [
                              jsxRuntimeExports.jsx("input", {
                                type: "checkbox",
                                checked: se ? (ne ?? E.enabled) : E.enabled,
                                onChange: (ye) => {
                                  se || R(ye.target.checked);
                                },
                                disabled: se,
                              }),
                              T(
                                "common.shortcut_settings_dialog.enable_shortcuts",
                              ),
                            ],
                          }),
                          se &&
                            jsxRuntimeExports.jsx("div", {
                              style: {
                                marginTop: "8px",
                                padding: "8px 12px",
                                backgroundColor: "#fff3cd",
                                border: "1px solid #ffeaa7",
                                borderRadius: "4px",
                                fontSize: "12px",
                                color: "#856404",
                              },
                              children: T(
                                "common.shortcut_settings.shortcuts_disabled_notice",
                              ),
                            }),
                        ],
                      }),
                      jsxRuntimeExports.jsxs("div", {
                        children: [
                          jsxRuntimeExports.jsx("div", {
                            style: { fontWeight: "bold", marginBottom: "16px" },
                            children: T(
                              "common.shortcut_settings_dialog.shortcut_settings",
                            ),
                          }),
                          jsxRuntimeExports.jsx("div", {
                            style: {
                              display: "flex",
                              flexDirection: "column",
                              gap: "12px",
                            },
                            children: E.shortcuts.map((ye) =>
                              jsxRuntimeExports.jsxs(
                                "div",
                                {
                                  style: {
                                    display: "flex",
                                    flexDirection: "column",
                                    gap: "8px",
                                    padding: "12px",
                                    border: "1px solid #e0e0e0",
                                    borderRadius: "4px",
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
                                          style: { flex: "1" },
                                          children: [
                                            jsxRuntimeExports.jsx("div", {
                                              style: {
                                                fontWeight: "bold",
                                                marginBottom: "4px",
                                              },
                                              children: T(ye.display_name),
                                            }),
                                            jsxRuntimeExports.jsx("div", {
                                              style: {
                                                fontSize: "12px",
                                                color: "#666",
                                              },
                                              children: T(ye.description),
                                            }),
                                          ],
                                        }),
                                        jsxRuntimeExports.jsx("div", {
                                          style: {
                                            display: "flex",
                                            alignItems: "center",
                                            gap: "8px",
                                            minWidth: "250px",
                                          },
                                          children:
                                            A === ye.action
                                              ? jsxRuntimeExports.jsxs(
                                                  jsxRuntimeExports.Fragment,
                                                  {
                                                    children: [
                                                      jsxRuntimeExports.jsx(
                                                        "input",
                                                        {
                                                          type: "text",
                                                          value: H,
                                                          onKeyDown: (be) =>
                                                            pe(be, ye.action),
                                                          placeholder: T(
                                                            "common.shortcut_settings_dialog.press_key_placeholder",
                                                          ),
                                                          style: {
                                                            flex: 1,
                                                            padding: "6px 12px",
                                                            border:
                                                              "2px solid #2196F3",
                                                            borderRadius: "4px",
                                                            fontSize: "14px",
                                                            outline: "none",
                                                          },
                                                          autoFocus: !0,
                                                          readOnly: !0,
                                                        },
                                                      ),
                                                      jsxRuntimeExports.jsx(
                                                        "button",
                                                        {
                                                          onClick: le,
                                                          style: {
                                                            padding: "6px 12px",
                                                            fontSize: "12px",
                                                            backgroundColor:
                                                              "#f44336",
                                                            color: "white",
                                                            border: "none",
                                                            borderRadius: "4px",
                                                            cursor: "pointer",
                                                          },
                                                          title: T(
                                                            "common.shortcut_settings.cancel_tooltip",
                                                          ),
                                                          children: "×",
                                                        },
                                                      ),
                                                    ],
                                                  },
                                                )
                                              : jsxRuntimeExports.jsx("div", {
                                                  onClick: () =>
                                                    de(ye.action, ye.shortcut),
                                                  style: {
                                                    flex: 1,
                                                    padding: "6px 12px",
                                                    backgroundColor: "#f5f5f5",
                                                    border: "1px solid #ddd",
                                                    borderRadius: "4px",
                                                    fontSize: "14px",
                                                    minHeight: "20px",
                                                    cursor: "pointer",
                                                    transition: "all 0.2s ease",
                                                  },
                                                  onMouseEnter: (be) => {
                                                    ((be.currentTarget.style.backgroundColor =
                                                      "#e8e8e8"),
                                                      (be.currentTarget.style.borderColor =
                                                        "#bbb"));
                                                  },
                                                  onMouseLeave: (be) => {
                                                    ((be.currentTarget.style.backgroundColor =
                                                      "#f5f5f5"),
                                                      (be.currentTarget.style.borderColor =
                                                        "#ddd"));
                                                  },
                                                  title: T(
                                                    "common.shortcut_settings_dialog.click_to_edit",
                                                  ),
                                                  children:
                                                    ye.shortcut ||
                                                    T(
                                                      "common.shortcut_settings_dialog.not_set",
                                                    ),
                                                }),
                                        }),
                                      ],
                                    }),
                                    A === ye.action &&
                                      te &&
                                      jsxRuntimeExports.jsx("div", {
                                        style: {
                                          color: "#f44336",
                                          fontSize: "12px",
                                          marginTop: "4px",
                                          paddingLeft: "8px",
                                          backgroundColor: "#ffebee",
                                          padding: "8px",
                                          borderRadius: "4px",
                                          border: "1px solid #ffcdd2",
                                        },
                                        children: te,
                                      }),
                                  ],
                                },
                                ye.action,
                              ),
                            ),
                          }),
                        ],
                      }),
                      jsxRuntimeExports.jsxs("div", {
                        style: {
                          marginTop: "20px",
                          padding: "16px",
                          backgroundColor: "#f5f5f5",
                          borderRadius: "4px",
                        },
                        children: [
                          jsxRuntimeExports.jsx("div", {
                            style: { fontWeight: "bold", marginBottom: "8px" },
                            children: T(
                              "common.shortcut_settings.usage_instructions.title",
                            ),
                          }),
                          jsxRuntimeExports.jsxs("div", {
                            style: { fontSize: "14px", lineHeight: "1.5" },
                            children: [
                              jsxRuntimeExports.jsx("div", {
                                children: T(
                                  "common.shortcut_settings.usage_instructions.instruction1",
                                ),
                              }),
                              jsxRuntimeExports.jsx("div", {
                                children: T(
                                  "common.shortcut_settings.usage_instructions.instruction2",
                                ),
                              }),
                              jsxRuntimeExports.jsx("div", {
                                children: T(
                                  "common.shortcut_settings.usage_instructions.instruction3",
                                ),
                              }),
                              jsxRuntimeExports.jsx("div", {
                                children: T(
                                  "common.shortcut_settings.usage_instructions.instruction4",
                                ),
                              }),
                              jsxRuntimeExports.jsx("div", {
                                children: T(
                                  "common.shortcut_settings_dialog.enable_shortcut_checkbox",
                                ),
                              }),
                              jsxRuntimeExports.jsx("div", {
                                style: {
                                  marginTop: "8px",
                                  fontSize: "12px",
                                  color: "#666",
                                },
                                children: T(
                                  "common.shortcut_settings_dialog.example",
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
            })
          : jsxRuntimeExports.jsxs(Dialog, {
              open: S,
              onClose: he,
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
                      children: T("common.shortcut_settings.title"),
                    }),
                    jsxRuntimeExports.jsx("button", {
                      onClick: he,
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
                  children: jsxRuntimeExports.jsx("div", {
                    style: { padding: "20px", textAlign: "center" },
                    children: T("common.shortcut_settings_dialog.loading"),
                  }),
                }),
              ],
            }),
      [S, he, E, x, A, H, te, se, ne, pe, le, de, R, T],
    );
  };
