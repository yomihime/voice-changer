// Extracted declaration from ../main-ui.js:102395-102415.
// Navigation/reference excerpt; shared bundle dependencies are NOT imported.
// Edit ../main-ui.js for a runnable change. This is not original TS/TSX source.
function App() {
  const { appMode: S } = useAppRoot(),
    { displayColorMode: C } = useAppState(),
    E = reactExports.useMemo(
      () =>
        C == "light"
          ? (document.body.classList.toggle("dark-mode", !1),
            createTheme({ palette: { mode: "light" } }))
          : (document.body.classList.toggle("dark-mode", !0),
            createTheme({ palette: { mode: "dark" } })),
      [C],
    ),
    w = reactExports.useMemo(() => {
      if (S === "App") return jsxRuntimeExports.jsx(Demo, {});
      if (S === "LogViewer") return jsxRuntimeExports.jsx(LogViewer, {});
    }, [S]);
  return jsxRuntimeExports.jsxs(ThemeProvider, {
    theme: E,
    children: [w, jsxRuntimeExports.jsx(Lt, { style: { zIndex: 2001 } })],
  });
}
