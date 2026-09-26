// Extracted declaration from ../main-ui.js:102542-102825.
// Navigation/reference excerpt; shared bundle dependencies are NOT imported.
// Edit ../main-ui.js for a runnable change. This is not original TS/TSX source.
const useServerConfig = (S) => {
    const { t: C } = useTranslation(),
      E = reactExports.useMemo(() => VCRestClient.getInstance(), []),
      [w, R] = reactExports.useState(DefaultServerConfiguration),
      [_, x] = reactExports.useState([]),
      [T, A] = reactExports.useState([]),
      [O, H] = reactExports.useState([]),
      [ee, te] = reactExports.useState([]),
      [ie, ne] = reactExports.useState([]),
      [ae, se] = reactExports.useState([]),
      [ce, fe] = reactExports.useState(),
      pe = reactExports.useCallback(async () => {
        const Ut = await E.getServerConfiguration();
        R(Ut);
      }, [E]),
      le = reactExports.useCallback(
        async (Ut = !1) => {
          const nr = await E.getServerAudioInputDevices(Ut);
          x(nr);
        },
        [E],
      ),
      de = reactExports.useCallback(
        async (Ut = !1) => {
          const nr = await E.getServerAudioOutputDevices(Ut);
          A(nr);
        },
        [E],
      ),
      he = reactExports.useCallback(async () => {
        const Ut = await E.getServerGPUInfo();
        H(Ut);
      }, [E]),
      me = reactExports.useCallback(
        async (Ut = !1) => {
          const nr = await E.getServerModuleStatus(Ut);
          te(nr);
        },
        [E],
      ),
      ye = reactExports.useCallback(async () => {
        const Ut = await E.getSamples();
        se(Ut);
      }, [E]),
      be = reactExports.useCallback(async () => {
        const Ut = await E.getServerSlotInfos();
        ne(Ut);
      }, [E]),
      ve = reactExports.useCallback(async () => {
        const Ut = await E.getLocalVoiceChangerInterfaceInfo();
        fe(Ut);
      }, [E]);
    (reactExports.useEffect(() => {
      (log$1("info", logPrefix$1, "load server information"),
        pe(),
        le(),
        de(),
        he(),
        me(),
        ye(),
        be(),
        ve());
    }, [E, pe, le, de, he, me, ye, be, ve]),
      reactExports.useEffect(() => {
        E.setEnableFlatPath(S.flatPath);
      }, [E, S.flatPath]));
    const xe = reactExports.useCallback(
        async (Ut) => {
          try {
            await Ut();
          } catch (nr) {
            log$1(
              "error",
              logPrefix$1,
              C("common.error_messages.error_occurred"),
              nr,
            );
            const mr = nr;
            if (mr.type == VOICE_CHANGER_CLIENT_EXCEPTION.ERR_HTTP_EXCEPTION) {
              const gr = `${mr.status}[${mr.statusText}]: ${mr.reason} ${mr.action}`;
              S.triggerToast("error", gr);
            } else throw nr;
          }
        },
        [S, C],
      ),
      Ce = reactExports.useCallback(
        async (Ut) => {
          (await E.updateServerConfiguration(Ut), pe(), be());
        },
        [E, pe, be],
      ),
      _e = reactExports.useCallback(
        async (Ut) => {
          await xe(async () => {
            await Ce(Ut);
          });
        },
        [xe, Ce],
      ),
      Be = reactExports.useCallback(async () => {
        const Ut = await E.downloadApplioModules();
        return (me(), Ut);
      }, [E, me]),
      Ve = reactExports.useCallback(
        async (Ut, nr) => {
          const mr = await E.downloadSample(Ut, nr);
          return (be(), mr);
        },
        [E, be],
      ),
      ke = reactExports.useCallback(
        async (Ut, nr, mr, gr = null, Zt) => {
          if (nr === "RVC") {
            const yr = mr.find((_r) => _r.kind === "rvcModel")?.file,
              xr = mr.find((_r) => _r.kind === "rvcIndex")?.file || null;
            if (!yr)
              throw new Error(
                C("common.error_messages.rvc_model_file_required"),
              );
            await E.uploadRVCModelFile(Ut, yr, xr, gr, Zt);
          } else if (nr === "Beatrice_v2") {
            const yr = mr.find((xr) => xr.kind === "beatriceV2Zip")?.file;
            if (!yr)
              throw new Error(
                C("common.error_messages.beatrice_v2_zip_file_required"),
              );
            await E.uploadBeatriceV2ModelFile(Ut, yr, Zt);
          } else
            throw new Error(
              C("common.error_messages.not_supported_voice_changer_type"),
            );
          be();
        },
        [E, be, C],
      ),
      Le = reactExports.useCallback(
        async (Ut) => {
          (await E.updateServerSlotInfo(Ut), be());
        },
        [E, be],
      ),
      qe = reactExports.useCallback(
        async (Ut) => {
          (await E.deleteServerSlotInfo(Ut), be());
        },
        [E, be],
      ),
      ze = reactExports.useCallback(
        async (Ut, nr, mr) => {
          (await E.uploadIconFile(Ut, nr, mr), be());
        },
        [E, be],
      ),
      Ae = reactExports.useCallback(
        async (Ut, nr, mr, gr) => {
          (await E.uploadBeatriceV2VoiceIconFile(Ut, nr, mr, gr), be());
        },
        [E, be],
      ),
      Ne = reactExports.useCallback(
        async (Ut, nr, mr) => {
          (await E.updateBeatriceV2VoiceName(Ut, nr, mr), be());
        },
        [E, be],
      ),
      We = reactExports.useCallback(
        async (Ut, nr, mr) => {
          (await E.updateBeatriceV2VoiceDescription(Ut, nr, mr), be());
        },
        [E, be],
      ),
      Ie = reactExports.useCallback(async (Ut) => await E.getTask(Ut), [E]),
      $e = reactExports.useCallback(
        async (Ut) => {
          await E.deleteTask(Ut);
        },
        [E],
      ),
      Me = reactExports.useCallback(async () => {
        (await E.initializeServer(), be());
      }, [E, be]),
      Ge = reactExports.useCallback(
        async (Ut) => {
          (await E.mergeModels(Ut), be());
        },
        [E, be],
      ),
      er = reactExports.useCallback(
        async (Ut) => {
          (await E.exportToOnnx(Ut), be());
        },
        [E, be],
      ),
      Ht = reactExports.useCallback(
        async (Ut) => {
          const nr = await E.export(Ut);
          return (be(), nr);
        },
        [E, be],
      ),
      rr = reactExports.useCallback(
        async (Ut) => {
          const nr = { dst: Ut };
          (await E.moveMergedModel(nr), be());
        },
        [E, be],
      ),
      Jt = reactExports.useCallback(
        async (Ut) => {
          const nr = { dst: Ut };
          (await E.moveExportedOnnxModel(nr), be());
        },
        [E, be],
      ),
      Kt = reactExports.useCallback(
        async (Ut, nr) => {
          const mr = { src: Ut, dst: nr };
          (await E.moveModel(mr), be());
        },
        [E, be],
      ),
      dr = reactExports.useCallback(async () => {
        (await xe(async () => {
          await E.startServerDevice();
        }),
          ve());
      }, [E, xe, ve]),
      or = reactExports.useCallback(async () => {
        (await E.stopServerDevice(), ve());
      }, [E, ve]),
      ar = reactExports.useCallback(
        async (Ut) => {
          await E.setLocalVoiceChangerDummyInput(Ut);
        },
        [E],
      ),
      ur = reactExports.useCallback(async () => {
        await E.truncateOutputBuffer();
      }, [E]),
      pr = reactExports.useCallback(async () => {
        await E.refreshQueue();
      }, [E]);
    return {
      serverConfiguration: w,
      serverAudioInputDevices: _,
      serverAudioOutputDevices: T,
      serverGpuInfo: O,
      serverModuleStatus: ee,
      samples: ae,
      serverSlotInfos: ie,
      localVoiceChangerInterfaceInfo: ce,
      reloadServerConfiguration: pe,
      reloadServerAudioInputDevices: le,
      reloadServerAudioOutputDevices: de,
      reloadServerSlotInfos: be,
      reloadLocalVoiceChangerInterfaceInfo: ve,
      reloadServerModuleStatus: me,
      updateServerConfiguration: _e,
      downloadApplioModules: Be,
      downloadSample: Ve,
      uploadModelFile: ke,
      updateServerSlotInfo: Le,
      deleteServerSlotInfo: qe,
      uploadIconFile: ze,
      uploadBeatriceV2VoiceIconFile: Ae,
      updateBeatriceV2VoiceName: Ne,
      updateBeatriceV2VoiceDescription: We,
      getTask: Ie,
      deleteTask: $e,
      initializeServer: Me,
      mergeModels: Ge,
      exportToOnnx: er,
      exportModel: Ht,
      moveMergedModel: rr,
      moveExportedOnnxModel: Jt,
      moveModel: Kt,
      startServerDevice: dr,
      stopServerDevice: or,
      setLocalVoiceChangerDummyInput: ar,
      truncateOutputBuffer: ur,
      refreshVoiceChangerIOQueue: pr,
    };
  };
