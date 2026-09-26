// Extracted declaration from ../main-ui.js:105158-105176.
// Navigation/reference excerpt; shared bundle dependencies are NOT imported.
// Edit ../main-ui.js for a runnable change. This is not original TS/TSX source.
const AppStateProvider = ({ children: S }) => {
    const { audioContext: C, triggerToast: E } = useAppRoot(),
      w = useGlobalSetting(),
      R = useVoiceChangerClient({ globaSetting: w, ctx: C, triggerToast: E });
    reactExports.useEffect(
      () => (
        console.log("AppStateProvider mounted"),
        () => {
          console.log("AppStateProvider unmounted");
        }
      ),
      [],
    );
    const _ = { ...w, ...R };
    return jsxRuntimeExports.jsx(AppStateContext.Provider, {
      value: _,
      children: S,
    });
  };
