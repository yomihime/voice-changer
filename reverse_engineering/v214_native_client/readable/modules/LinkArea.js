// Extracted declaration from ../main-ui.js:34649-34812.
// Navigation/reference excerpt; shared bundle dependencies are NOT imported.
// Edit ../main-ui.js for a runnable change. This is not original TS/TSX source.
const LinkArea = () => {
    const {
        displayColorMode: S,
        setDisplayColorMode: C,
        setSelectedLanguage: E,
        selectedLanguage: w,
      } = useAppState(),
      { initializeServer: R, guiSetting: _ } = useAppRoot(),
      [x, T] = reactExports.useState(!1),
      { t: A } = useTranslation(),
      O = reactExports.useCallback(
        (te) => {
          (E(te.target.value), instance.changeLanguage(te.target.value));
        },
        [E],
      ),
      H = reactExports.useCallback(() => {
        C(S === "light" ? "dark" : "light");
      }, [S, C]);
    return reactExports.useMemo(
      () =>
        jsxRuntimeExports.jsxs("div", {
          style: {
            display: "flex",
            justifyContent: "flex-start",
            alignItems: "center",
            marginBottom: "20px",
            marginTop: "20px",
          },
          children: [
            _.lang &&
              jsxRuntimeExports.jsx(FormControl, {
                size: "small",
                sx: { minWidth: 120, marginRight: 2 },
                children: jsxRuntimeExports.jsx(Select, {
                  value: w,
                  onChange: O,
                  sx: { height: "32px", fontSize: "13px" },
                  startAdornment: jsxRuntimeExports.jsx(LanguageIcon, {
                    sx: { fontSize: "1.2rem", marginRight: 1 },
                  }),
                  children: _.lang.map((te) =>
                    jsxRuntimeExports.jsx(
                      MenuItem,
                      {
                        value: te,
                        children: languageNativeNames[te] || te.toUpperCase(),
                      },
                      te,
                    ),
                  ),
                }),
              }),
            jsxRuntimeExports.jsx(Tooltip, {
              title: A(`common.theme.${S === "light" ? "dark" : "light"}`),
              children: jsxRuntimeExports.jsx(IconButton, {
                onClick: H,
                color: "default",
                size: "small",
                sx: {
                  px: 1.5,
                  marginLeft: "10px",
                  border: "2px solid",
                  borderColor: "grey.300",
                  borderRadius: "8px",
                  "&:hover": { borderColor: "primary.main" },
                  height: "32px",
                },
                children: jsxRuntimeExports.jsx(Stack, {
                  alignItems: "center",
                  direction: "row",
                  sx: { height: "18px" },
                  children:
                    S === "light"
                      ? jsxRuntimeExports.jsx(DarkModeIcon, {
                          sx: { fontSize: "18px" },
                        })
                      : jsxRuntimeExports.jsx(LightModeIcon, {
                          sx: { fontSize: "18px" },
                        }),
                }),
              }),
            }),
            jsxRuntimeExports.jsx(Tooltip, {
              title: A("common.initialize.button"),
              children: jsxRuntimeExports.jsx(IconButton, {
                onClick: () => {
                  T(!0);
                },
                color: "default",
                size: "small",
                sx: {
                  px: 1.5,
                  marginLeft: "20px",
                  border: "2px solid",
                  borderColor: "grey.300",
                  borderRadius: "8px",
                  "&:hover": { borderColor: "primary.main" },
                  height: "32px",
                },
                children: jsxRuntimeExports.jsx(Stack, {
                  alignItems: "center",
                  justifyContent: "center",
                  sx: { height: "18px" },
                  children: jsxRuntimeExports.jsx("span", {
                    style: { fontSize: "13px", whiteSpace: "nowrap" },
                    children: A("common.initialize.button"),
                  }),
                }),
              }),
            }),
            jsxRuntimeExports.jsx(Tooltip, {
              title: A("common.links.download_native_client"),
              children: jsxRuntimeExports.jsx("a", {
                href: "/native_client/voice-changer-native-client-win.exe",
                download: "voice-changer-native-client-win.exe",
                style: { textDecoration: "none" },
                children: jsxRuntimeExports.jsx(IconButton, {
                  color: "default",
                  size: "small",
                  sx: {
                    px: 1.5,
                    marginLeft: "10px",
                    border: "2px solid",
                    borderColor: "grey.300",
                    borderRadius: "8px",
                    "&:hover": { borderColor: "primary.main" },
                    height: "32px",
                  },
                  children: jsxRuntimeExports.jsxs(Stack, {
                    alignItems: "center",
                    direction: "row",
                    sx: { height: "18px" },
                    children: [
                      jsxRuntimeExports.jsx(DownloadIcon, {
                        sx: { fontSize: "18px", marginRight: "5px" },
                      }),
                      jsxRuntimeExports.jsx("span", {
                        style: { fontSize: "13px", whiteSpace: "nowrap" },
                        children: A("common.links.download_native_client"),
                      }),
                    ],
                  }),
                }),
              }),
            }),
            jsxRuntimeExports.jsx(ConfirmationDialog, {
              isOpen: x,
              title: A("common.initialize.confirm_title"),
              message: A("common.initialize.confirm_message"),
              confirmButtonText: A("common.initialize.confirm"),
              cancelButtonText: A("common.initialize.cancel"),
              onConfirm: async () => {
                (await R(), T(!1));
              },
              onCancel: () => {
                T(!1);
              },
            }),
          ],
        }),
      [R, _.lang, x, A, O, H, w, S],
    );
  };
