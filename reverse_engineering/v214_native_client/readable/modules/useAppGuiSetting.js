// Extracted declaration from ../main-ui.js:100043-100079.
// Navigation/reference excerpt; shared bundle dependencies are NOT imported.
// Edit ../main-ui.js for a runnable change. This is not original TS/TSX source.
const useAppGuiSetting = () => {
    const { t: S } = useTranslation(),
      [C, E] = reactExports.useState(!1),
      [w, R] = reactExports.useState(defaultAppGuiSettin),
      [_, x] = reactExports.useState(S("common.app_info.unknown_version")),
      [T, A] = reactExports.useState(S("common.app_info.unknown_edition"));
    return (
      reactExports.useEffect(() => {
        (async () => {
          const ee = await (
            await fetch("/assets/gui_settings/GUI.json", { method: "GET" })
          ).json();
          R(ee);
        })();
      }, []),
      reactExports.useEffect(() => {
        (async () => {
          const ee = await (
            await fetch("/assets/gui_settings/version.txt", { method: "GET" })
          ).text();
          x(ee);
        })();
      }, []),
      reactExports.useEffect(() => {
        (async () => {
          const ee = await (
            await fetch("/assets/gui_settings/edition.txt", { method: "GET" })
          ).text();
          A(ee);
        })();
      }, []),
      reactExports.useEffect(() => {
        _ !== null && T !== null && E(!0);
      }, [_, T]),
      { guiSettingLoaded: C, guiSetting: w, version: _, edition: T }
    );
  };
