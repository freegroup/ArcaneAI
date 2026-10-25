import 'dart:async';

import 'package:arcane_player/engine/arcane_engine.dart';

import 'audio_ports.dart';
import 'sound_library.dart';

/// The single place that arbitrates audio focus between the microphone,
/// the narrator's voice and the room ambience — the Flutter counterpart of
/// the Python engine's `voice.stop()` / jukebox interplay.
///
/// Rules:
/// - The ambience is ducked while the microphone listens or a voice speaks.
/// - Listening stops the voice; a new turn stops the previous voice.
/// - Narration is read aloud only if [reading] is on and the mic is idle.
///
/// All collaborators are interfaces, so the policy is testable without
/// plugins.
final class AudioCoordinator {
  AudioCoordinator({
    required Jukebox jukebox,
    SpeechOutput? speech,
    SpeechInput? microphone,
    this.duckedGain = 0.2,
  }) : _jukebox = jukebox,
       _speech = speech,
       _microphone = microphone {
    _subscriptions = [
      ?_microphone?.onListeningChanged.listen((listening) {
        if (listening) unawaited(_speech?.stop());
        unawaited(_applyDucking());
      }),
      ?_speech?.onSpeakingChanged.listen((_) => unawaited(_applyDucking())),
    ];
  }

  final Jukebox _jukebox;
  final SpeechOutput? _speech;
  final SpeechInput? _microphone;
  late final List<StreamSubscription<bool>> _subscriptions;

  SoundLibrary? _library;

  /// Ambience multiplier while the mic listens or a voice speaks.
  final double duckedGain;

  /// The sound table of the game being played — the output stays shared.
  set library(SoundLibrary library) => _library = library;

  /// Plays the sound cues of [events] and reads [narration] aloud. Call once
  /// per turn; returns once speech has started.
  Future<void> handleTurn(List<GameEvent> events, {String? narration}) async {
    await _speech?.stop();
    for (final event in events) {
      await _playCue(event);
    }
    if (narration != null) await announce(narration);
  }

  /// Reads [text] aloud, if the microphone is idle.
  Future<void> announce(String text) async {
    if (_microphone?.isListening ?? false) return;
    await _speech?.speak(text);
  }

  /// Plays the ambience of the current room without narration — used when a
  /// saved game is resumed.
  Future<void> resumeAmbience(AmbienceCue cue) => _playCue(cue);

  /// Whether a microphone is available at all.
  bool get hasMicrophone => _microphone != null;

  /// Whether the microphone is listening right now.
  bool get isListening => _microphone?.isListening ?? false;

  /// Fires whenever listening starts or stops.
  Stream<bool> get onListeningChanged =>
      _microphone?.onListeningChanged ?? const Stream.empty();

  /// Starts listening (stops the voice, ducks the ambience).
  Future<bool> startListening(
    void Function(SpeechResult result) onResult,
  ) async {
    final mic = _microphone;
    if (mic == null || !await mic.initialize()) return false;
    await _speech?.stop();
    await mic.listen(onResult);
    return true;
  }

  /// Stops listening.
  Future<void> stopListening() => _microphone?.stop() ?? Future.value();

  /// Stops everything and releases the outputs.
  Future<void> dispose() async {
    for (final subscription in _subscriptions) {
      await subscription.cancel();
    }
    await _microphone?.dispose();
    await _speech?.dispose();
    await _jukebox.dispose();
  }

  Future<void> _applyDucking() {
    final busy =
        (_microphone?.isListening ?? false) || (_speech?.isSpeaking ?? false);
    return _jukebox.setAmbienceGain(busy ? duckedGain : 1);
  }

  Future<void> _playCue(GameEvent event) async {
    switch (event) {
      case AmbienceCue(:final playback):
        final content = playback == null
            ? null
            : await _library?.resolve(playback.sound);
        await _jukebox.playAmbience(content, volume: playback?.volume ?? 100);
      case EffectCue(:final playback):
        final content = await _library?.resolve(playback.sound);
        if (content != null) {
          await _jukebox.playEffect(
            content,
            volume: playback.volume,
            duration: playback.duration,
          );
        }
      default:
        break;
    }
  }
}
