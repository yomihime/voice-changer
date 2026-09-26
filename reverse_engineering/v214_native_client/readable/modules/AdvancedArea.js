// Extracted declaration from ../main-ui.js:102260-102349.
// Navigation/reference excerpt; shared bundle dependencies are NOT imported.
// Edit ../main-ui.js for a runnable change. This is not original TS/TSX source.
const AdvancedArea = () => {
  const { t: S } = useTranslation(),
    [C, E] = reactExports.useState(!1),
    [w, R] = reactExports.useState(!1),
    [_, x] = reactExports.useState(!1),
    T = () => {
      const ie = new URL(window.location.href);
      (ie.searchParams.set("app_mode", "LogViewer"),
        window.open(ie.toString(), "_blank"));
    },
    A = () => {
      E(!0);
    },
    O = () => {
      R(!0);
    },
    H = () => {
      x(!0);
    },
    ee = async () => {
      try {
        await invoke("set_clear_site_data_and_stop_app");
      } catch (ie) {
        console.error("Failed to clear site data and stop app:", ie);
      }
    },
    te = reactExports.useCallback(
      async (ie) => {
        try {
          await invoke("open_browser_url", { url: ie });
        } catch (ne) {
          (console.warn(S("common.links.url_open_failed"), ne),
            window.open(ie, "_blank", "noopener,noreferrer"));
        }
      },
      [S],
    );
  return jsxRuntimeExports.jsxs("div", {
    style: {
      display: "flex",
      gap: "16px",
      marginTop: "16px",
      flexWrap: "wrap",
    },
    children: [
      jsxRuntimeExports.jsx(Button, {
        size: "small",
        onClick: T,
        children: S("common.advanced_area.log"),
      }),
      jsxRuntimeExports.jsx(Button, {
        size: "small",
        onClick: A,
        children: S("common.advanced_area.advanced_settings"),
      }),
      jsxRuntimeExports.jsx(Button, {
        size: "small",
        onClick: O,
        children: S("common.advanced_area.key_settings"),
      }),
      jsxRuntimeExports.jsx(Button, {
        size: "small",
        onClick: () => te("https://github.com/w-okada/voice-changer"),
        children: S("common.advanced_area.github_repo"),
      }),
      jsxRuntimeExports.jsx(Button, {
        size: "small",
        onClick: H,
        children: S("common.advanced_area.clear_site_data_and_restart"),
      }),
      jsxRuntimeExports.jsx(AdvancedSettingDialog, {
        open: C,
        onClose: () => E(!1),
      }),
      jsxRuntimeExports.jsx(ShortcutSettingDialog, {
        open: w,
        onClose: () => R(!1),
      }),
      jsxRuntimeExports.jsx(ConfirmDialog, {
        open: _,
        onClose: () => x(!1),
        onConfirm: ee,
        title: S("common.clear_site_data_confirm.title"),
        message: S("common.clear_site_data_confirm.message"),
        confirmText: S("common.dialog.confirm"),
        cancelText: S("common.dialog.cancel"),
      }),
    ],
  });
};
