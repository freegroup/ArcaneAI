import 'dart:async';

import 'audio_ports.dart';

/// Speaks through the system voice, or through the screen reader while one
/// is active ([useScreenReader]), so narration never competes with
/// VoiceOver/TalkBack. The UI keeps [useScreenReader] in sync with the
/// platform's accessibility state.
final class AdaptiveSpeechOutput implements SpeechOutput {
  AdaptiveSpeechOutput({
    required SpeechOutput voice,
    required SpeechOutput screenReader,
  }) : _voice = voice,
       _screenReader = screenReader {
    _subscription = _voice.onSpeakingChanged.listen(_changes.add);
  }

  final SpeechOutput _voice;
  final SpeechOutput _screenReader;
  final StreamController<bool> _changes = StreamController.broadcast();
  late final StreamSubscription<bool> _subscription;
  bool _useScreenReader = false;

  /// Whether narration goes to the screen reader instead of the voice.
  bool get useScreenReader => _useScreenReader;
  set useScreenReader(bool value) {
    if (value == _useScreenReader) return;
    _useScreenReader = value;
    if (value) unawaited(_voice.stop());
  }

  SpeechOutput get _active => _useScreenReader ? _screenReader : _voice;

  @override
  bool get isSpeaking => _active.isSpeaking;

  @override
  Stream<bool> get onSpeakingChanged => _changes.stream;

  @override
  Future<void> speak(String text) => _active.speak(text);

  @override
  Future<void> stop() => _active.stop();

  @override
  Future<void> dispose() async {
    await _subscription.cancel();
    await _changes.close();
    await _voice.dispose();
    await _screenReader.dispose();
  }
}
