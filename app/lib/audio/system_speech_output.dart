import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/semantics.dart';
import 'package:flutter_tts/flutter_tts.dart';
import 'package:logging/logging.dart';

import 'audio_ports.dart';

final _log = Logger('tts');

/// Offline [SpeechOutput] using the operating system's voices via
/// `flutter_tts` (German by default). Uses the best voice installed on the
/// device instead of the system's default one.
/// The best voice for [language] among [voices] (as `flutter_tts` lists
/// them), or `null` if none is better than the system's default: premium
/// before enhanced, never one that needs the network or is not installed.
@visibleForTesting
Map<String, String>? bestVoice(
  Iterable<Map<String, String>> voices,
  String language,
) {
  int rank(Map<String, String> voice) => switch (voice['quality']) {
    'premium' || 'very high' => 2,
    'enhanced' || 'high' => 1,
    _ => 0,
  };
  final usable = voices.where(
    (voice) =>
        voice['locale'] == language &&
        voice['network_required'] != '1' &&
        !(voice['features'] ?? '').contains('notInstalled') &&
        rank(voice) > 0,
  );
  if (usable.isEmpty) return null;
  return usable.reduce((a, b) => rank(b) > rank(a) ? b : a);
}

final class SystemTtsSpeechOutput implements SpeechOutput {
  SystemTtsSpeechOutput({String language = 'de-DE'}) {
    // speak() returns when speech starts; the handlers report its progress.
    _tts
      ..setLanguage(language)
      ..setSpeechRate(0.5) // normal speed
      ..awaitSpeakCompletion(false)
      ..setStartHandler(() => _set(true))
      ..setCompletionHandler(() => _set(false))
      ..setCancelHandler(() => _set(false))
      ..setErrorHandler((_) => _set(false));
    unawaited(_useBestVoice(language));
  }

  Future<void> _useBestVoice(String language) async {
    try {
      final voices = (await _tts.getVoices as List<Object?>? ?? const [])
          .whereType<Map<Object?, Object?>>()
          .map((voice) => voice.cast<String, String>())
          .toList();
      _log.info(
        'Stimmen für $language: '
        '${voices.where((v) => v['locale'] == language).map((v) => '${v['name']} (${v['quality']})').join(', ')} '
        '— insgesamt ${voices.length} Stimmen',
      );
      final best = bestVoice(voices, language);
      if (best == null) {
        _log.info(
          'Keine Stimme besser als die Standardstimme für $language installiert',
        );
        return;
      }
      await _tts.setVoice(best);
      _log.info(
        'Stimme: ${best['name']} (${best['quality']}) '
        '${best['identifier'] ?? best['locale']}',
      );
    } on Object catch (e) {
      _log.warning('Stimmenwahl fehlgeschlagen, Standardstimme bleibt: $e');
    }
  }

  final FlutterTts _tts = FlutterTts();
  final StreamController<bool> _changes = StreamController.broadcast();
  bool _speaking = false;

  @override
  bool get isSpeaking => _speaking;

  @override
  Stream<bool> get onSpeakingChanged => _changes.stream;

  @override
  Future<void> speak(String text) async {
    if (text.trim().isEmpty) return;
    await _tts.stop();
    await _tts.speak(text);
  }

  @override
  Future<void> stop() async {
    await _tts.stop();
    _set(false);
  }

  @override
  Future<void> dispose() async {
    await _tts.stop();
    await _changes.close();
  }

  void _set(bool speaking) {
    if (_speaking == speaking || _changes.isClosed) return;
    _speaking = speaking;
    _changes.add(speaking);
  }
}

/// [SpeechOutput] that hands narration to the active screen reader
/// (VoiceOver / TalkBack), so a blind player hears one voice — their own,
/// with their own rate settings — instead of a second one competing with it.
final class ScreenReaderSpeechOutput implements SpeechOutput {
  ScreenReaderSpeechOutput();

  final StreamController<bool> _changes = StreamController.broadcast();

  @override
  bool get isSpeaking => false; // the screen reader owns its own speech

  @override
  Stream<bool> get onSpeakingChanged => _changes.stream;

  @override
  Future<void> speak(String text) async {
    if (text.trim().isEmpty) return;
    // sendAnnouncement needs a FlutterView, which this view-less audio layer
    // has no handle to; announce is the right tool here.
    // ignore: deprecated_member_use
    await SemanticsService.announce(text, TextDirection.ltr);
  }

  @override
  Future<void> stop() async {}

  @override
  Future<void> dispose() => _changes.close();
}
