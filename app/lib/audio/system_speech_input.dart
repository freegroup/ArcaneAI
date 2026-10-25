import 'dart:async';

import 'package:logging/logging.dart';
import 'package:speech_to_text/speech_to_text.dart';

import 'audio_ports.dart';

/// Offline [SpeechInput] using the operating system's recognizer via
/// `speech_to_text`. Initialized lazily on first use: on macOS the permission
/// prompt aborts an app launched from a terminal/IDE if requested too early.
final class SystemSpeechInput implements SpeechInput {
  SystemSpeechInput({String languagePrefix = 'de'})
    : _languagePrefix = languagePrefix;

  static final _log = Logger('arcane_audio.stt');

  final SpeechToText _speech = SpeechToText();
  final String _languagePrefix;
  final StreamController<bool> _listening = StreamController.broadcast();
  bool _available = false;
  String? _localeId;

  @override
  bool get isAvailable => _available;

  @override
  bool get isListening => _speech.isListening;

  @override
  Stream<bool> get onListeningChanged => _listening.stream;

  @override
  Future<bool> initialize() async {
    if (_available) return true;
    _available = await _speech.initialize(
      onStatus: (_) => _emit(_speech.isListening),
      onError: (e) {
        _log.warning('STT error: ${e.errorMsg}');
        _emit(false);
      },
    );
    if (_available) {
      final locales = await _speech.locales();
      _localeId = locales
          .where((l) => l.localeId.toLowerCase().startsWith(_languagePrefix))
          .firstOrNull
          ?.localeId;
    }
    return _available;
  }

  @override
  Future<void> listen(void Function(SpeechResult result) onResult) async {
    if (!await initialize()) return;
    await _speech.listen(
      listenOptions: SpeechListenOptions(
        localeId: _localeId,
        partialResults: true,
        listenMode: ListenMode.dictation,
      ),
      onResult: (r) =>
          onResult((text: r.recognizedWords, isFinal: r.finalResult)),
    );
    _emit(_speech.isListening);
  }

  @override
  Future<void> stop() async {
    await _speech.stop();
    _emit(false);
  }

  @override
  Future<void> dispose() async {
    await _speech.cancel();
    await _listening.close();
  }

  void _emit(bool listening) {
    if (!_listening.isClosed) _listening.add(listening);
  }
}
