import 'package:meta/meta.dart';

import '../definition/game_definition.dart';

/// Something that happened during a turn and that the outside world (UI,
/// audio) may react to. The engine itself never plays sounds or draws.
@immutable
sealed class GameEvent {
  const GameEvent();
}

/// The player moved to another room.
final class RoomEntered extends GameEvent {
  const RoomEntered(this.roomId);

  /// The room now current.
  final String roomId;
}

/// Inventory variables changed; [variables] is the complete new inventory.
final class InventoryChanged extends GameEvent {
  const InventoryChanged(this.variables, {required this.changedKeys});

  /// All variables after the change.
  final Map<String, Object?> variables;

  /// Keys whose value differs from before.
  final Set<String> changedKeys;
}

/// The game reached an end room.
final class GameOver extends GameEvent {
  const GameOver(this.roomId);

  /// The end room.
  final String roomId;
}

/// The companion's mood shifted (affects the personality template).
final class MoodChanged extends GameEvent {
  const MoodChanged({required this.from, required this.to});

  /// Previous mood.
  final String from;

  /// New mood.
  final String to;
}

/// Something to play.
sealed class SoundCue extends GameEvent {
  const SoundCue();
}

/// Replace the looping room ambience; `null` [playback] stops it.
final class AmbienceCue extends SoundCue {
  const AmbienceCue(this.playback);

  /// What to loop, or `null` for silence.
  final SoundPlayback? playback;
}

/// Play a one-shot effect.
final class EffectCue extends SoundCue {
  const EffectCue(this.playback);

  /// The effect.
  final SoundPlayback playback;
}
