// Extracted declaration from ../main-ui.js:105206-105593.
// Navigation/reference excerpt; shared bundle dependencies are NOT imported.
// Edit ../main-ui.js for a runnable change. This is not original TS/TSX source.
const useHotKeySetting = () => {
    const { t: S } = useTranslation(),
      [C, E] = reactExports.useState(null),
      [w, R] = reactExports.useState(null),
      {
        serverConfiguration: _,
        localVoiceChangerInterfaceInfo: x,
        startServerDevice: T,
        stopServerDevice: A,
        updateServerConfiguration: O,
        serverSlotInfos: H,
        currentSlotInfo: ee,
        origin: te,
      } = useAppRoot(),
      {
        isStarted: ie,
        isPassthrough: ne,
        setIsStarted: ae,
        setIsPassthrough: se,
        setNodeInputGain: ce,
        nodeInputGain: fe,
        setNodeOutputGain: pe,
        nodeOutputGain: le,
        setNodeMonitorGain: de,
        nodeMonitorGain: he,
      } = useAppState(),
      me = _.voice_changer_input_mode === VoiceChangerInputMode.server,
      ye = !!x?.local_voice_changer_interface_active,
      be = me ? ye : ie,
      ve = me ? _.pass_through : ne,
      xe = reactExports.useCallback(async () => {
        if (me) {
          if (
            _.audio_input_device_index === -1 ||
            _.audio_output_device_index === -1
          )
            return;
          await T();
        } else ae(!0);
      }, [me, _.audio_input_device_index, _.audio_output_device_index, T, ae]),
      Ce = reactExports.useCallback(async () => {
        me ? await A() : ae(!1);
      }, [me, A, ae]),
      _e = reactExports.useCallback(async () => {
        me ? await O({ ..._, pass_through: !0 }) : se(!0);
      }, [me, O, se, _]),
      Be = reactExports.useCallback(async () => {
        me ? await O({ ..._, pass_through: !1 }) : se(!1);
      }, [me, O, se, _]),
      Ve = reactExports.useCallback(
        async (Ie) => {
          const $e = me ? _.audio_input_device_gain : fe,
            Me = Math.min(Math.max($e + Ie, 0), 10);
          return (
            me ? await O({ ..._, audio_input_device_gain: Me }) : ce(Me),
            Me
          );
        },
        [me, _, O, ce, fe],
      ),
      ke = reactExports.useCallback(
        async (Ie) => {
          const $e = me ? _.audio_output_device_gain : le,
            Me = Math.min(Math.max($e + Ie, 0), 10);
          return (
            me ? await O({ ..._, audio_output_device_gain: Me }) : pe(Me),
            Me
          );
        },
        [me, _, O, pe, le],
      ),
      Le = reactExports.useCallback(
        async (Ie) => {
          const $e = me ? _.audio_monitor_device_gain : he,
            Me = Math.min(Math.max($e + Ie, 0), 10);
          return (
            me ? await O({ ..._, audio_monitor_device_gain: Me }) : de(Me),
            Me
          );
        },
        [me, _, O, de, he],
      ),
      qe = async () => {
        try {
          const Ie = await invoke("get_shortcut_settings");
          (console.log(S("common.shortcut_settings.config_load_success"), Ie),
            E(Ie),
            R(null));
        } catch (Ie) {
          (R(`${S("common.shortcut_settings.config_load_failed")} ${Ie}`),
            console.error(
              S("common.shortcut_settings.settings_load_error"),
              Ie,
            ));
        }
      },
      ze = async (Ie) => {
        try {
          (await invoke("update_shortcut_settings", { configDto: Ie }),
            await invoke("register_shortcuts"),
            E(Ie),
            R(null),
            console.log(S("common.shortcut_settings.config_save_success")));
        } catch ($e) {
          (R(`${S("common.shortcut_settings.config_save_failed")} ${$e}`),
            console.error(
              S("common.shortcut_settings.settings_save_error"),
              $e,
            ));
        }
      },
      Ae = (Ie, $e) => {
        if (!C || !$e.trim()) return null;
        const Me = C.shortcuts.find(
          (Ge) => Ge.shortcut === $e && Ge.action !== Ie,
        );
        return Me
          ? S("common.shortcut_settings.duplicate_key_error", {
              shortcut: $e,
              displayName: Me.display_name,
            })
          : null;
      },
      Ne = async (Ie, $e) => {
        if (!C) return;
        const Me = C.shortcuts.map((er) =>
            er.action === Ie ? { ...er, shortcut: $e } : er,
          ),
          Ge = { ...C, shortcuts: Me };
        await ze(Ge);
      },
      We = async (Ie) => {
        if (!C) return;
        const $e = { ...C, enabled: Ie };
        await ze($e);
      };
    return (
      reactExports.useEffect(() => {
        qe();
      }, []),
      reactExports.useEffect(() => {
        const Ie = (Ht, rr) => {
            const Jt = H.find((vr) => vr.slot_index === Ht) || null;
            if (Jt == null || Jt.voice_changer_type !== "Beatrice_v2")
              return null;
            const Kt = Jt,
              dr = Kt.model_info.voice[rr],
              ar = Kt.toml_file.replace(/\\\\/g, "/").replace(/\\/g, "/");
            return (
              ar.substring(0, ar.lastIndexOf("/")) +
              "/" +
              dr.portrait.path.split(/[/\\]/).pop()
            );
          },
          $e = (Ht) => {
            const rr = H.find((Jt) => Jt.slot_index === Ht) || null;
            return rr == null
              ? null
              : rr.voice_changer_type === "RVC"
                ? rr.icon_file != null
                  ? "model_dir/" +
                    rr.slot_index +
                    "/" +
                    rr.icon_file.split(/[/\\]/).pop()
                  : "./assets/icons/human.png"
                : rr.voice_changer_type === "Beatrice_v2"
                  ? Ie(Ht, ee.dst_id)
                  : null;
          },
          Me = {
            title: S("common.shortcut_settings.vcclient_notification"),
            message: "operation",
            icon_url:
              te + "/" + $e(_.current_slot_index) || "./assets/icons/human.png",
            slot_id: _.current_slot_index,
            started: be,
            passthrough: ve,
            input_gain: me ? _.audio_input_device_gain : fe,
            output_gain: me ? _.audio_output_device_gain : le,
            monitor_gain: me ? _.audio_monitor_device_gain : he,
            model_name: ee?.name || S("common.shortcut_settings.unknown_model"),
          },
          er = (async () => {
            const Ht = await listen("shortcut-action", async (rr) => {
              console.log("🎯 shortcut-action イベント受信:", rr);
              const { action: Jt, volumeType: Kt, delta: dr } = rr.payload;
              switch (
                ((Me.title = S(
                  "common.shortcut_settings.vcclient_notification",
                )),
                Jt)
              ) {
                case "ShowStatus": {
                  (console.log(
                    S("common.shortcut_settings.show_status_action"),
                  ),
                    (Me.message = S("common.shortcut_settings.status")));
                  break;
                }
                case "NextSlot": {
                  const or = H.filter((Ut) => Ut.voice_changer_type !== null)
                    .map((Ut) => Ut.slot_index)
                    .sort((Ut, nr) => Ut - nr);
                  if (or.length <= 1) {
                    Me.message = S("common.shortcut_settings.slot_change_skip");
                    break;
                  }
                  const ar = _.current_slot_index,
                    ur = or.findIndex((Ut) => Ut === ar);
                  let pr;
                  (ur === -1 || ur === or.length - 1
                    ? (pr = or[0])
                    : (pr = or[ur + 1]),
                    await O({ ..._, current_slot_index: pr }),
                    (Me.message = S(
                      "common.shortcut_settings.slot_changed_to_next",
                      { from: ar, to: pr },
                    )),
                    (Me.slot_id = pr),
                    (Me.icon_url =
                      te + "/" + $e(pr) || "./assets/icons/human.png"));
                  const vr = H.find((Ut) => Ut.slot_index === pr);
                  ((Me.model_name =
                    vr?.name || S("common.shortcut_settings.unknown_model")),
                    console.log(
                      S("common.shortcut_settings.slot_changed_log", {
                        from: ar,
                        to: pr,
                      }),
                    ));
                  break;
                }
                case "PreviousSlot": {
                  console.log(
                    S("common.shortcut_settings.previous_slot_action"),
                  );
                  const or = H.filter((Ut) => Ut.voice_changer_type !== null)
                    .map((Ut) => Ut.slot_index)
                    .sort((Ut, nr) => Ut - nr);
                  if (or.length <= 1) {
                    Me.message = S("common.shortcut_settings.slot_change_skip");
                    break;
                  }
                  const ar = _.current_slot_index,
                    ur = or.findIndex((Ut) => Ut === ar);
                  let pr;
                  (ur === -1 || ur === 0
                    ? (pr = or[or.length - 1])
                    : (pr = or[ur - 1]),
                    await O({ ..._, current_slot_index: pr }),
                    (Me.message = S(
                      "common.shortcut_settings.slot_changed_to_previous",
                      { from: ar, to: pr },
                    )),
                    (Me.slot_id = pr),
                    (Me.icon_url =
                      te + "/" + $e(pr) || "./assets/icons/human.png"));
                  const vr = H.find((Ut) => Ut.slot_index === pr);
                  ((Me.model_name =
                    vr?.name || S("common.shortcut_settings.unknown_model")),
                    console.log(
                      S("common.shortcut_settings.slot_changed_log", {
                        from: ar,
                        to: pr,
                      }),
                    ));
                  break;
                }
                case "ToggleVoiceConversion":
                  try {
                    be
                      ? (await Ce(),
                        (Me.message = S(
                          "common.shortcut_settings.voice_conversion_stopped",
                        )),
                        (Me.started = !1))
                      : (await xe(),
                        (Me.message = S(
                          "common.shortcut_settings.voice_conversion_started",
                        )),
                        (Me.started = !0));
                  } catch (or) {
                    console.error(
                      S("common.shortcut_settings.notification_window_error"),
                      or,
                    );
                  }
                  break;
                case "TogglePassthrough":
                  try {
                    ve
                      ? (await Be(),
                        (Me.message = S(
                          "common.shortcut_settings.passthrough_disabled",
                        )),
                        (Me.passthrough = !1))
                      : (await _e(),
                        (Me.message = S(
                          "common.shortcut_settings.passthrough_enabled",
                        )),
                        (Me.passthrough = !0));
                  } catch (or) {
                    console.error(
                      S("common.shortcut_settings.notification_window_error"),
                      or,
                    );
                  }
                  break;
                case "VolumeChange":
                  if (!dr) return;
                  if (Kt === "input") {
                    const or = await Ve(dr),
                      ar = Math.round(or * 10) / 10;
                    ((Me.input_gain = ar),
                      (Me.message = S(
                        "common.shortcut_settings.input_volume_changed",
                        { volume: ar },
                      )));
                  } else if (Kt === "output") {
                    const or = await ke(dr),
                      ar = Math.round(or * 10) / 10;
                    ((Me.output_gain = ar),
                      (Me.message = S(
                        "common.shortcut_settings.output_volume_changed",
                        { volume: ar },
                      )));
                  } else if (Kt === "monitor") {
                    const or = await Le(dr),
                      ar = Math.round(or * 10) / 10;
                    ((Me.monitor_gain = ar),
                      (Me.message = S(
                        "common.shortcut_settings.monitor_volume_changed",
                        { volume: ar },
                      )));
                  }
                  break;
                default:
                  Me.message = S(
                    "common.shortcut_settings.unknown_shortcut_action",
                    { action: Jt },
                  );
                  break;
              }
              (console.log(
                S("common.shortcut_settings.notification_payload_log"),
                Me,
              ),
                await invoke("show_notification_window_with_message", {
                  params: Me,
                }));
            });
            return () => {
              Ht();
            };
          })();
        return () => {
          er.then((Ht) => Ht());
        };
      }, [
        te,
        be,
        ve,
        xe,
        Ce,
        _e,
        Be,
        Ve,
        ke,
        Le,
        _,
        H,
        O,
        ee,
        me,
        fe,
        he,
        le,
        S,
      ]),
      {
        config: C,
        updateShortcut: Ne,
        setShorcutEnabled: We,
        checkDuplicationKey: Ae,
        hotKeySettingError: w,
      }
    );
  };
