import 'package:meta/meta.dart';

import '../definition/game_definition.dart';

/// Immutable snapshot of a play-through: where the player is and what the
/// inventory holds. Every turn produces a new [GameState]; persistence and
/// testing work on plain values.
@immutable
final class GameState {
  GameState({
    required this.roomId,
    required Map<String, Object?> variables,
    this.turn = 0,
  }) : variables = Map.unmodifiable(variables);

  /// The state a new game starts with.
  factory GameState.initial(GameDefinition definition) => GameState(
    roomId: definition.initialRoomId,
    variables: definition.initialVariables,
  );

  /// Restores a state written by [toJson].
  factory GameState.fromJson(Map<String, Object?> json) => GameState(
    roomId: json['room'] as String,
    variables: (json['variables'] as Map).cast<String, Object?>(),
    turn: json['turn'] as int? ?? 0,
  );

  /// Current room.
  final String roomId;

  /// Inventory variables.
  final Map<String, Object?> variables;

  /// Number of player turns taken (the welcome does not count).
  final int turn;

  /// A copy with the given fields replaced.
  GameState copyWith({
    String? roomId,
    Map<String, Object?>? variables,
    int? turn,
  }) => GameState(
    roomId: roomId ?? this.roomId,
    variables: variables ?? this.variables,
    turn: turn ?? this.turn,
  );

  /// JSON representation (values are JSON primitives already).
  Map<String, Object?> toJson() => {
    'room': roomId,
    'variables': variables,
    'turn': turn,
  };
}
