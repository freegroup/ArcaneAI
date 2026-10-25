import 'dart:async';

import 'package:arcane_player/content/arcane_content.dart';

/// Plays game sounds: one looping ambience plus transient effects.
abstract interface class Jukebox {
  /// Loops [content] as the room ambience at [volume] percent; `null` stops
  /// the ambience.
  Future<void> playAmbience(ResolvedContent? content, {int volume = 100});

  /// Plays [content] once at [volume] percent, cut off after [duration].
  Future<void> playEffect(
    ResolvedContent content, {
    int volume = 100,
    Duration? duration,
  });

  /// Multiplier (0..1) on the ambience volume, used for ducking.
  Future<void> setAmbienceGain(double gain);

  /// Stops ambience and all effects.
  Future<void> stopAll();

  /// Releases resources.
  Future<void> dispose();
}

/// Speaks narration aloud, offline.
abstract interface class SpeechOutput {
  /// Starts speaking [text], interrupting anything already speaking. Returns
  /// once speech has started; progress is reported on [onSpeakingChanged].
  Future<void> speak(String text);

  /// Stops speaking immediately.
  Future<void> stop();

  /// Whether speech is in progress.
  bool get isSpeaking;

  /// Fires whenever [isSpeaking] changes (started, finished, stopped).
  Stream<bool> get onSpeakingChanged;

  /// Releases resources.
  Future<void> dispose();
}

/// A recognized speech result.
typedef SpeechResult = ({String text, bool isFinal});

/// Listens to the microphone and transcribes speech (offline where the OS
/// supports it).
abstract interface class SpeechInput {
  /// Prepares the recognizer; returns whether it is usable.
  Future<bool> initialize();

  /// Whether [initialize] succeeded.
  bool get isAvailable;

  /// Whether the microphone is currently listening.
  bool get isListening;

  /// Starts listening, delivering partial and final [SpeechResult]s.
  Future<void> listen(void Function(SpeechResult result) onResult);

  /// Stops listening.
  Future<void> stop();

  /// Fires whenever [isListening] changes.
  Stream<bool> get onListeningChanged;

  /// Releases resources.
  Future<void> dispose();
}
