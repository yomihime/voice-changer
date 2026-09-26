# 主界面代码导航

以下名称由发布包保留下来。行号对应 `main-ui.js`；modules 只是便于阅读的声明摘录，不能单独运行。

| 名称 | 完整文件行号 | 声明摘录 |
| --- | --- | --- |
| LinkArea | 34649–34812 | [查看](modules/LinkArea.js) |
| FileUploaderClient | 35068–35123 | [查看](modules/FileUploaderClient.js) |
| RestClient | 35149–35264 | [查看](modules/RestClient.js) |
| VCRestClient | 35265–35498 | [查看](modules/VCRestClient.js) |
| VoiceChangerClient | 93720–94031 | [查看](modules/VoiceChangerClient.js) |
| IconArea | 94723–94869 | [查看](modules/IconArea.js) |
| InfoArea | 94888–95202 | [查看](modules/InfoArea.js) |
| ModelUploadDialog | 95208–95602 | [查看](modules/ModelUploadDialog.js) |
| SampleModelDailog | 95754–96019 | [查看](modules/SampleModelDailog.js) |
| ModelList | 96020–96146 | [查看](modules/ModelList.js) |
| ModelEditDialog | 96147–96222 | [查看](modules/ModelEditDialog.js) |
| ModelSelector | 96223–96651 | [查看](modules/ModelSelector.js) |
| HeaderArea | 96652–96722 | [查看](modules/HeaderArea.js) |
| VoiceCharacterEditDialog | 96725–96944 | [查看](modules/VoiceCharacterEditDialog.js) |
| PortraitArea | 96947–97235 | [查看](modules/PortraitArea.js) |
| SettingsDialog | 97260–98344 | [查看](modules/SettingsDialog.js) |
| MainControls | 98372–98748 | [查看](modules/MainControls.js) |
| useGlobalSetting | 98988–99126 | [查看](modules/useGlobalSetting.js) |
| InputControls | 99128–99818 | [查看](modules/InputControls.js) |
| VolumeControls | 99819–100036 | [查看](modules/VolumeControls.js) |
| useAppGuiSetting | 100043–100079 | [查看](modules/useAppGuiSetting.js) |
| VoiceControls | 100357–100884 | [查看](modules/VoiceControls.js) |
| Controls | 100885–100911 | [查看](modules/Controls.js) |
| PerformanceArea | 100915–101326 | [查看](modules/PerformanceArea.js) |
| ControlArea | 101327–101362 | [查看](modules/ControlArea.js) |
| AdvancedSettingDialog | 101363–101748 | [查看](modules/AdvancedSettingDialog.js) |
| ShortcutSettingDialog | 101757–102211 | [查看](modules/ShortcutSettingDialog.js) |
| AdvancedArea | 102260–102349 | [查看](modules/AdvancedArea.js) |
| Demo | 102350–102394 | [查看](modules/Demo.js) |
| App | 102395–102415 | [查看](modules/App.js) |
| useAudioConfig | 102418–102504 | [查看](modules/useAudioConfig.js) |
| DefaultServerConfiguration | 102507–102541 | [查看](modules/DefaultServerConfiguration.js) |
| useServerConfig | 102542–102825 | [查看](modules/useServerConfig.js) |
| AppRootProvider | 104769–104849 | [查看](modules/AppRootProvider.js) |
| useVoiceChangerClient | 104852–105157 | [查看](modules/useVoiceChangerClient.js) |
| AppStateProvider | 105158–105176 | [查看](modules/AppStateProvider.js) |
| useHotKeySetting | 105206–105593 | [查看](modules/useHotKeySetting.js) |
| HotkeyProvider | 105594–105600 | [查看](modules/HotkeyProvider.js) |

## 原生调用

- `set_clear_site_data_and_stop_app`：102281
- `open_browser_url`：102289
- `plugin:event|unlisten`：105195
- `plugin:event|listen`：105200
- `get_shortcut_settings`：105290
- `update_shortcut_settings`：105304
- `register_shortcuts`：105305
- `shortcut-action`：105389
- `show_notification_window_with_message`：105553

## HTTP 接口

- `/api/uploader/upload_file_chunk`：35083
- `/api/uploader/concat_uploaded_file_chunk`：35113
- `/api/operation/initialize`：35288
- `/api/audio-device-manager/input_devices`：35292
- `/api/audio-device-manager/output_devices`：35296
- `/api/configuration-manager/configuration`：35300
- `/api/configuration-manager/configuration`：35304
- `/api/gpu-device-manager/devices`：35308
- `/api/module-manager/modules`：35312
- `/api/module-manager/modules/operation/download_applio_modules`：35317
- `/api/sample-manager/samples`：35322
- `/api/sample-manager/samples/operation/download`：35327
- `/api/slot-manager/slots`：35333
- `/api/slot-manager/slots/${C}`：35337
- `/api/slot-manager/slots`：35353
- `/api/slot-manager/slots`：35368
- `/api/slot-manager/slots/operation/set_icon_file`：35382
- `/api/slot-manager/slots/${C.slot_index}`：35388
- `/api/slot-manager/slots/${C}`：35392
- `/api/slot-manager/slots/operation/merge_models`：35397
- `/api/slot-manager/slots/operation/export_onnx`：35403
- `/api/slot-manager/slots/operation/export`：35408
- `/api/slot-manager/slots/operation/move_merged_model`：35413
- `/api/slot-manager/slots/operation/move_exported_onnx_model`：35419
- `/api/slot-manager/slots/operation/move_model`：35424
- `/api/voice-changer/operation/refresh_queue`：35428
- `/api/local-voice-changer-interface/operation/start`：35433
- `/api/local-voice-changer-interface/operation/stop`：35439
- `/api/local-voice-changer-interface/operation/truncate-output-buffer`：35445
- `/api/voice-changer-manager/information`：35450
- `/api/local-voice-changer-interface/information`：35455
- `/api/task-manager/tasks/${C}`：35460
- `/api/task-manager/tasks/${C}`：35464
- `/api/slot-manager/slots/operation/beatricev2/set_voice_icon_file`：35472
- `/api/slot-manager/slots/operation/beatricev2/set_voice_name`：35479
- `/api/slot-manager/slots/operation/beatricev2/set_voice_description`：35486
- `/api/local-voice-changer-interface/operation/set_dummy_input`：35493
- `/api/voice-changer/convert_chunk_bulk`：38161
- `/api/voice-changer/convert_chunk`：38162
