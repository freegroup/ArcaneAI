import 'dart:async';

import 'package:arcane_player/content/arcane_content.dart';
import 'package:audioplayers/audioplayers.dart';
import 'package:logging/logging.dart';

import 'audio_ports.dart';

/// [Jukebox] backed by `audioplayers`: one looping player for the ambience,
/// a transient player per effect. Port of the PoC jukebox; the content comes
/// pre-resolved from the [SoundLibrary], so this class only maps
/// [ResolvedContent] to an audioplayers [Source] and manages playback.
final class AudioPlayersJukebox implements Jukebox {
  AudioPlayersJukebox();

  static final _log = Logger('arcane_audio.jukebox');

  final AudioPlayer _ambience = AudioPlayer();
  final Set<AudioPlayer> _effects = {};
  int _ambienceVolume = 100;
  double _gain = 1;

  @override
  Future<void> playAmbience(
    ResolvedContent? content, {
    int volume = 100,
  }) async {
    _ambienceVolume = volume;
    final source = _sourceOf(content);
    await _ambience.stop();
    if (source == null) return;
    try {
      await _ambience.setReleaseMode(ReleaseMode.loop);
      await _ambience.play(source, volume: _effectiveAmbience);
    } on Object catch (e) {
      _log.warning('Ambience failed: $e');
    }
  }

  @override
  Future<void> playEffect(
    ResolvedContent content, {
    int volume = 100,
    Duration? duration,
  }) async {
    final source = _sourceOf(content);
    if (source == null) return;
    final player = AudioPlayer();
    _effects.add(player);
    unawaited(player.onPlayerComplete.first.then((_) => _release(player)));
    try {
      await player.play(source, volume: (volume / 100).clamp(0, 1));
      if (duration != null) {
        Timer(duration, () => unawaited(_release(player)));
      }
    } on Object catch (e) {
      _log.warning('Effect failed: $e');
      await _release(player);
    }
  }

  @override
  Future<void> setAmbienceGain(double gain) async {
    _gain = gain.clamp(0, 1);
    await _ambience.setVolume(_effectiveAmbience);
  }

  @override
  Future<void> stopAll() async {
    await _ambience.stop();
    await Future.wait([for (final p in _effects.toList()) _release(p)]);
  }

  @override
  Future<void> dispose() async {
    await stopAll();
    await _ambience.dispose();
  }

  double get _effectiveAmbience => (_ambienceVolume / 100 * _gain).clamp(0, 1);

  Source? _sourceOf(ResolvedContent? content) => switch (content) {
    // AssetSource is relative to the 'assets/' prefix audioplayers adds.
    AssetContent(:final key) => AssetSource(
      key.startsWith('assets/') ? key.substring('assets/'.length) : key,
    ),
    FileContent(:final path) => DeviceFileSource(path),
    null => null,
  };

  Future<void> _release(AudioPlayer player) async {
    if (!_effects.remove(player)) return;
    await player.stop();
    await player.dispose();
  }
}
