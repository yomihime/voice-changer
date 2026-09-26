// Extracted declaration from ../main-ui.js:104769-104849.
// Navigation/reference excerpt; shared bundle dependencies are NOT imported.
// Edit ../main-ui.js for a runnable change. This is not original TS/TSX source.
const AppRootProvider = ({ children: S }) => {
    const { t: C } = useTranslation(),
      E = reactExports.useCallback((se, ce) => {
        y.info(ce, {
          type: se,
          position: "bottom-right",
          autoClose: 3e3,
          hideProgressBar: !1,
          closeOnClick: !0,
          pauseOnHover: !0,
          draggable: !0,
          progress: void 0,
          theme: "light",
        });
      }, []),
      [w, R] = reactExports.useState(!0),
      _ = useAudioConfig({
        createAudioContextDelay: libExports.isMobile ? 2e3 : 0,
      }),
      x = useAppGuiSetting(),
      T = reactExports.useMemo(() => ({ flatPath: !1, triggerToast: E }), [E]),
      A = useServerConfig(T),
      [O, H] = reactExports.useState("App"),
      [ee, te] = reactExports.useState(null),
      ie = window.location.origin;
    (reactExports.useEffect(() => {
      const fe =
        new URL(window.location.href).searchParams.get("app_mode") || null;
      fe == "Test"
        ? H("Test")
        : fe == "LogViewer"
          ? H("LogViewer")
          : fe == "JsonViewer"
            ? H("JsonViewer")
            : H("App");
    }, []),
      reactExports.useEffect(() => {
        if (A.serverConfiguration == null) return;
        const se = A.serverConfiguration.current_slot_index,
          ce = A.serverSlotInfos.find((fe) => fe.slot_index === se);
        te(ce ?? null);
      }, [A.serverConfiguration, A.serverSlotInfos]));
    const ne = reactExports.useCallback(
      (se) => {
        const ce = se.reason;
        (log$1("error", "Unhandled Rejection", ce),
          log$1(
            "error",
            "Unhandled Rejection",
            C("common.error_messages.unhandled_rejection_possible_cause"),
          ),
          log$1("error", "Unhandled Rejection EVENT", se),
          se.preventDefault());
      },
      [C],
    );
    reactExports.useEffect(
      () => (
        window.addEventListener("unhandledrejection", ne),
        () => {
          window.removeEventListener("unhandledrejection", ne);
        }
      ),
      [w, ne],
    );
    const ae = {
      ..._,
      ...x,
      ...A,
      appMode: O,
      currentSlotInfo: ee,
      setAppMode: H,
      origin: ie,
      triggerToast: E,
      setUnhandledRejectionToastEnabled: R,
    };
    return jsxRuntimeExports.jsx(AppRootContext.Provider, {
      value: ae,
      children: S,
    });
  };
