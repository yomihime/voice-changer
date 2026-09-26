// Extracted declaration from ../main-ui.js:35265-35498.
// Navigation/reference excerpt; shared bundle dependencies are NOT imported.
// Edit ../main-ui.js for a runnable change. This is not original TS/TSX source.
class VCRestClient {
  static _instance = null;
  restClient;
  fileUploaderClient;
  enableFlatPath = !1;
  constructor() {
    ((this.restClient = new RestClient()),
      (this.fileUploaderClient = new FileUploaderClient()));
  }
  static getInstance = () => (
    VCRestClient._instance === null &&
      (VCRestClient._instance = new VCRestClient()),
    VCRestClient._instance
  );
  setBaseUrl = (C) => {
    (this.restClient.setBaseUrl(C), this.fileUploaderClient.setBaseUrl(C));
  };
  setEnableFlatPath = (C) => {
    ((this.enableFlatPath = C), this.fileUploaderClient.setEnableFlatPath(C));
  };
  generatePath = (C) =>
    this.enableFlatPath ? C[0] + C.slice(1).replace(/\//g, "_") : C;
  initializeServer = async () => {
    const C = this.generatePath("/api/operation/initialize");
    await this.restClient.postRequest(C, null);
  };
  getServerAudioInputDevices = async (C = !1) => {
    let E = this.generatePath("/api/audio-device-manager/input_devices");
    return (C && (E += "?reload=true"), await this.restClient.getRequest(E));
  };
  getServerAudioOutputDevices = async (C = !1) => {
    let E = this.generatePath("/api/audio-device-manager/output_devices");
    return (C && (E += "?reload=true"), await this.restClient.getRequest(E));
  };
  getServerConfiguration = async () => {
    const C = this.generatePath("/api/configuration-manager/configuration");
    return await this.restClient.getRequest(C);
  };
  updateServerConfiguration = async (C) => {
    const E = this.generatePath("/api/configuration-manager/configuration");
    await this.restClient.putRequest(E, C);
  };
  getServerGPUInfo = async () => {
    const C = this.generatePath("/api/gpu-device-manager/devices");
    return await this.restClient.getRequest(C);
  };
  getServerModuleStatus = async (C = !1) => {
    let E = this.generatePath("/api/module-manager/modules");
    return (C && (E += "?reload=true"), await this.restClient.getRequest(E));
  };
  downloadApplioModules = async () => {
    const C = this.generatePath(
      "/api/module-manager/modules/operation/download_applio_modules",
    );
    return await this.restClient.postRequest(C, null);
  };
  getSamples = async () => {
    const C = this.generatePath("/api/sample-manager/samples");
    return await this.restClient.getRequest(C);
  };
  downloadSample = async (C, E) => {
    const w = this.generatePath(
        "/api/sample-manager/samples/operation/download",
      ),
      R = { slot_index: C, sample_id: E };
    return await this.restClient.postRequest(w, R);
  };
  getServerSlotInfos = async () => {
    const C = this.generatePath("/api/slot-manager/slots");
    return await this.restClient.getRequest(C);
  };
  getServerSlotInfo = async (C) => {
    const E = this.generatePath(`/api/slot-manager/slots/${C}`);
    return await this.restClient.getRequest(E);
  };
  uploadFile = async (C, E, w) => {
    const R = await this.fileUploaderClient.uploadFile(C, E, w);
    await this.fileUploaderClient.concatUploadedFile(E.name, R);
  };
  uploadRVCModelFile = async (C, E, w, R, _) => {
    const x = w != null ? 2 : 1;
    (await this.uploadFile("", E, (O, H) => {
      _(O / x, !1);
    }),
      w != null &&
        (await this.uploadFile("", w, (O, H) => {
          _(O / x + 100 / x, !1);
        })));
    const T = this.generatePath("/api/slot-manager/slots"),
      A = {
        slot_index: C ?? null,
        voice_changer_type: "RVC",
        name: E.name.split(".")[0],
        model_file: E.name,
        index_file: w?.name ?? null,
        embedder: R,
      };
    (await this.restClient.postRequest(T, A), _(100, !0));
  };
  uploadBeatriceV2ModelFile = async (C, E, w) => {
    await this.uploadFile("", E, (x, T) => {
      w(x / 1, !1);
    });
    const R = this.generatePath("/api/slot-manager/slots"),
      _ = {
        slot_index: C ?? null,
        voice_changer_type: "Beatrice_v2",
        name: E.name.split(".")[0],
        zip_file: E.name,
      };
    await this.restClient.postRequest(R, _);
  };
  uploadIconFile = async (C, E, w) => {
    await this.uploadFile("", E, (x, T) => {
      w(x, !1);
    });
    const R = this.generatePath(
        "/api/slot-manager/slots/operation/set_icon_file",
      ),
      _ = { slot_index: C, icon_file: E.name };
    await this.restClient.postRequest(R, _);
  };
  updateServerSlotInfo = async (C) => {
    const E = this.generatePath(`/api/slot-manager/slots/${C.slot_index}`);
    await this.restClient.putRequest(E, C);
  };
  deleteServerSlotInfo = async (C) => {
    const E = this.generatePath(`/api/slot-manager/slots/${C}`);
    await this.restClient.deleteRequest(E, null);
  };
  mergeModels = async (C) => {
    const E = this.generatePath(
      "/api/slot-manager/slots/operation/merge_models",
    );
    await this.restClient.postRequest(E, C);
  };
  exportToOnnx = async (C) => {
    const E = this.generatePath(
      "/api/slot-manager/slots/operation/export_onnx",
    );
    await this.restClient.postRequest(E, C);
  };
  export = async (C) => {
    const E = this.generatePath("/api/slot-manager/slots/operation/export");
    return await this.restClient.postRequest(E, C, "blob");
  };
  moveMergedModel = async (C) => {
    const E = this.generatePath(
      "/api/slot-manager/slots/operation/move_merged_model",
    );
    await this.restClient.postRequest(E, C);
  };
  moveExportedOnnxModel = async (C) => {
    const E = this.generatePath(
      "/api/slot-manager/slots/operation/move_exported_onnx_model",
    );
    await this.restClient.postRequest(E, C);
  };
  moveModel = async (C) => {
    const E = this.generatePath("/api/slot-manager/slots/operation/move_model");
    await this.restClient.postRequest(E, C);
  };
  refreshQueue = async () => {
    const C = this.generatePath("/api/voice-changer/operation/refresh_queue");
    await this.restClient.postRequest(C, null);
  };
  startServerDevice = async () => {
    const C = this.generatePath(
      "/api/local-voice-changer-interface/operation/start",
    );
    await this.restClient.postRequest(C, null);
  };
  stopServerDevice = async () => {
    const C = this.generatePath(
      "/api/local-voice-changer-interface/operation/stop",
    );
    await this.restClient.postRequest(C, null);
  };
  truncateOutputBuffer = async () => {
    const C = this.generatePath(
      "/api/local-voice-changer-interface/operation/truncate-output-buffer",
    );
    await this.restClient.postRequest(C, null);
  };
  getVoiceChangerManagerInfo = async () => {
    const C = this.generatePath("/api/voice-changer-manager/information");
    return await this.restClient.getRequest(C);
  };
  getLocalVoiceChangerInterfaceInfo = async () => {
    const C = this.generatePath(
      "/api/local-voice-changer-interface/information",
    );
    return await this.restClient.getRequest(C);
  };
  getTask = async (C) => {
    const E = this.generatePath(`/api/task-manager/tasks/${C}`);
    return await this.restClient.getRequest(E);
  };
  deleteTask = async (C) => {
    const E = this.generatePath(`/api/task-manager/tasks/${C}`);
    await this.restClient.deleteRequest(E, null);
  };
  uploadBeatriceV2VoiceIconFile = async (C, E, w, R) => {
    await this.uploadFile("", w, (T, A) => {
      R(T, !1);
    });
    const _ = this.generatePath(
        "/api/slot-manager/slots/operation/beatricev2/set_voice_icon_file",
      ),
      x = { slot_index: C, voice_index: E, icon_file: w.name };
    await this.restClient.postRequest(_, x);
  };
  updateBeatriceV2VoiceName = async (C, E, w) => {
    const R = this.generatePath(
        "/api/slot-manager/slots/operation/beatricev2/set_voice_name",
      ),
      _ = { slot_index: C, voice_index: E, voice_name: w };
    await this.restClient.postRequest(R, _);
  };
  updateBeatriceV2VoiceDescription = async (C, E, w) => {
    const R = this.generatePath(
        "/api/slot-manager/slots/operation/beatricev2/set_voice_description",
      ),
      _ = { slot_index: C, voice_index: E, voice_description: w };
    await this.restClient.postRequest(R, _);
  };
  setLocalVoiceChangerDummyInput = async (C) => {
    const E = this.generatePath(
        "/api/local-voice-changer-interface/operation/set_dummy_input",
      ),
      w = { url: C };
    await this.restClient.postRequest(E, w);
  };
}
