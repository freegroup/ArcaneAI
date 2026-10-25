import 'package:flutter/foundation.dart';

import '../services/prefs_service.dart';

/// The player's one setting: whether answers are reworded in the game's
/// personality. Persisted; a [ChangeNotifier] so the game can follow it.
final class SettingsRepository extends ChangeNotifier {
  SettingsRepository(this._prefs)
    : _personality = _prefs.readSettings()?[_key] as bool? ?? true;

  static const _key = 'personality';

  final PrefsService _prefs;
  bool _personality;

  /// Whether the personality is on.
  bool get personality => _personality;

  /// Switches the personality on or off.
  Future<void> setPersonality(bool value) async {
    _personality = value;
    notifyListeners();
    await _prefs.writeSettings({_key: value});
  }
}
