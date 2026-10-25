import 'package:meta/meta.dart';

/// A complete, immutable game as authored in the editor.
@immutable
final class GameDefinition {
  GameDefinition({
    required this.id,
    required this.initialRoomId,
    required Map<String, Room> rooms,
    required List<GameAction> actions,
    required Map<String, VariableDefinition> variables,
    this.personality = '',
    this.welcomePrompt = '',
    this.gameTarget = '',
    this.helpText = '',
  }) : rooms = Map.unmodifiable(rooms),
       actions = List.unmodifiable(actions),
       variables = Map.unmodifiable(variables) {
    if (!this.rooms.containsKey(initialRoomId)) {
      throw ArgumentError.value(initialRoomId, 'initialRoomId', 'unknown room');
    }
  }

  /// Stable identifier (the game's folder name).
  final String id;

  /// Room the game starts in.
  final String initialRoomId;

  /// Rooms by id.
  final Map<String, Room> rooms;

  /// All actions (triggers and transitions) of the game.
  final List<GameAction> actions;

  /// Inventory variables by key, with their initial values.
  final Map<String, VariableDefinition> variables;

  /// Character/narrator personality; a template over the inventory.
  final String personality;

  /// Prompt that asks the narrator to open the game.
  final String welcomePrompt;

  /// What the player has to achieve — used in the prompt.
  final String gameTarget;

  /// Help shown to the player (simple HTML: `<b>`, `<i>`, line breaks).
  final String helpText;

  /// The room with [id]; throws if it does not exist.
  Room room(String id) =>
      rooms[id] ?? (throw ArgumentError.value(id, 'id', 'unknown room'));

  /// Actions that start in room [roomId] (regardless of their conditions).
  Iterable<GameAction> actionsFrom(String roomId) =>
      actions.where((a) => a.from == roomId);

  /// Initial value of every variable.
  Map<String, Object?> get initialVariables => {
    for (final v in variables.values) v.key: v.initialValue,
  };
}

/// What kind of room it is.
enum RoomKind {
  /// A regular room.
  normal,

  /// The room the game starts in.
  start,

  /// Reaching this room ends the game.
  end,
}

/// A location (a state of the state machine).
@immutable
final class Room {
  const Room({
    required this.id,
    required this.description,
    this.kind = RoomKind.normal,
    this.ambience,
  });

  /// Unique name, also used by actions to reference the room.
  final String id;

  /// Room description; a template over the inventory.
  final String description;

  /// Start, end or regular room.
  final RoomKind kind;

  /// Looping background sound while the player is here.
  final SoundPlayback? ambience;

  /// Whether entering this room ends the game.
  bool get isEnd => kind == RoomKind.end;
}

/// Something the player can do: a trigger ([from] == [to]) or a transition.
@immutable
final class GameAction {
  const GameAction({
    required this.name,
    required this.from,
    required this.to,
    required this.description,
    this.afterFire = '',
    this.conditions = const [],
    this.scripts = const [],
    this.effect,
  });

  /// Identifier the narrator calls; unique within a room.
  final String name;

  /// Room the action is available in.
  final String from;

  /// Room the player is in afterwards.
  final String to;

  /// What the action means — the narrator matches player intent against it.
  final String description;

  /// Hint for the narration once the action fired; a template.
  final String afterFire;

  /// Expressions that must all hold for the action to be available.
  final List<String> conditions;

  /// Statements that update the inventory when the action fires.
  final List<String> scripts;

  /// One-shot sound played when the action fires.
  final SoundPlayback? effect;

  /// Whether the action moves the player to another room.
  bool get isTransition => from != to;
}

/// Type of an inventory variable.
enum VariableType {
  /// Whole number.
  integer,

  /// `true` / `false`.
  boolean,

  /// Free text.
  string,

  /// One of [VariableDefinition.allowedValues].
  enumeration,
}

/// An inventory variable and its initial value.
@immutable
final class VariableDefinition {
  const VariableDefinition({
    required this.key,
    required this.initialValue,
    this.type = VariableType.string,
    this.allowedValues = const [],
  });

  /// Variable name as used in scripts and templates.
  final String key;

  /// Value at the start of the game.
  final Object? initialValue;

  /// Declared type.
  final VariableType type;

  /// For [VariableType.enumeration]: the permitted values.
  final List<Object?> allowedValues;

  /// Whether [value] may be stored in this variable.
  bool accepts(Object? value) =>
      type != VariableType.enumeration || allowedValues.contains(value);
}

/// A reference to a sound as written in the editor, e.g. `map/wind.wav`,
/// `global/forest/birds.wav` or `steps.wav`. Resolving it to a playable file
/// is up to the player (see `arcane_audio`).
@immutable
final class SoundRef {
  const SoundRef(this.path);

  /// Editor path of the sound.
  final String path;

  @override
  bool operator ==(Object other) => other is SoundRef && other.path == path;

  @override
  int get hashCode => path.hashCode;

  @override
  String toString() => path;
}

/// How a sound is played: which file, how loud, and for how long.
@immutable
final class SoundPlayback {
  const SoundPlayback(this.sound, {this.volume = 100, this.duration});

  /// The sound to play.
  final SoundRef sound;

  /// Volume in percent (0–100).
  final int volume;

  /// Cut-off for one-shot effects; `null` plays the whole sound.
  final Duration? duration;
}
