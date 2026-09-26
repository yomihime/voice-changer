/** Reconstructed from shipped JS call sites and PE strings; not upstream source.
 * Nullable/optional declarations are descriptive and need runtime validation for a new Rust host.
 * Native implementation and exact Rust integer types have not been recovered.
 */
export interface ShortcutItem {
  action: string;
  shortcut: string;
  display_name: string;
  description: string;
}
export interface ShortcutConfigDto {
  enabled: boolean;
  shortcuts: ShortcutItem[];
}
export interface NotificationParams {
  title?: string | null;
  message?: string | null;
  icon_url?: string | null;
  slot_id?: number | null;
  started?: boolean | null;
  passthrough?: boolean | null;
  input_gain?: number | null;
  output_gain?: number | null;
  monitor_gain?: number | null;
  model_name?: string | null;
}
export interface ShortcutActionPayload {
  action: 'ShowStatus' | 'NextSlot' | 'PreviousSlot' | 'ToggleVoiceConversion' |
    'TogglePassthrough' | 'VolumeChange';
  volumeType?: 'input' | 'output' | 'monitor';
  delta?: number;
}
export interface NativeCommandArguments {
  get_server_url: undefined;
  get_shortcut_settings: undefined;
  update_shortcut_settings: {configDto: ShortcutConfigDto};
  register_shortcuts: undefined;
  open_browser_url: {url: string};
  hide_notification_window: undefined;
  show_notification_window_with_message: {params: NotificationParams};
  set_clear_site_data_and_stop_app: undefined;
}
// Notification window bridge: window.startCountdown(),
// window.updateNotificationContent(title, message, iconUrl, slotId, started,
//   passthrough, inputGain, outputGain, monitorGain, modelName).
// The native shell emits "shortcut-action"; ordinary web browsers have no Tauri IPC.
