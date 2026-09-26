// Extracted declaration from ../main-ui.js:105594-105600.
// Navigation/reference excerpt; shared bundle dependencies are NOT imported.
// Edit ../main-ui.js for a runnable change. This is not original TS/TSX source.
const HotkeyProvider = ({ children: S }) => {
    const E = { ...useHotKeySetting() };
    return jsxRuntimeExports.jsx(HotkeyContext.Provider, {
      value: E,
      children: S,
    });
  };
