import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';

/// Thin wrapper over [SharedPreferences] for a single JSON-encoded settings
/// blob.
final class PrefsService {
  PrefsService(this._prefs);

  static const _settingsKey = 'settings';

  final SharedPreferences _prefs;

  /// Loads the application support instance.
  static Future<PrefsService> load() async =>
      PrefsService(await SharedPreferences.getInstance());

  /// The stored settings map, or `null` if none/unreadable.
  Map<String, Object?>? readSettings() {
    final raw = _prefs.getString(_settingsKey);
    if (raw == null) return null;
    try {
      return jsonDecode(raw) as Map<String, Object?>;
    } on Object {
      return null;
    }
  }

  /// Persists the settings map.
  Future<void> writeSettings(Map<String, Object?> data) =>
      _prefs.setString(_settingsKey, jsonEncode(data));
}
