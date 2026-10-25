import 'dart:async';

import '../companion/mood_director.dart';
import '../definition/game_definition.dart';
import '../events/game_event.dart';
import '../history/exchange.dart';
import '../game/game_controller.dart';
import '../game/prompt_config.dart';
import '../../llm/llm_provider.dart';
import '../runtime/game_state.dart';
import '../runtime/state_machine.dart';
import '../scripting/mini_script_runtime.dart';
import '../scripting/script_runtime.dart';
import 'session_snapshot.dart';

/// One play-through of a game: owns the current [GameState] and the
/// conversation, runs turns through the [GameController], and does the
/// companion's work between turns.
///
/// Turns are strictly sequential. After each turn the companion (mood) runs;
/// its result arrives on [sideEvents] and is guaranteed to be applied before
/// the next turn starts.
final class GameSession {
  /// A new play-through, or one continuing at [state] with [history].
  /// [narrationLlm] tells the player what happened; by default that is
  /// [llm] too.
  factory GameSession({
    required GameDefinition definition,
    required LlmProvider llm,
    required PromptConfig prompts,
    LlmProvider? narrationLlm,
    bool personality = true,
    ScriptRuntime scripts = const MiniScriptRuntime(),
    GameState? state,
    List<Exchange> history = const [],
  }) {
    final machine = StateMachine(definition, scripts: scripts);
    return GameSession._(
      definition: definition,
      machine: machine,
      controller: GameController(
        machine: machine,
        llm: llm,
        narrationLlm: narrationLlm ?? llm,
        prompts: prompts,
      ),
      mood: MoodDirector(
        definition: definition,
        llm: llm,
        config: prompts.mood,
      ),
      state: state ?? GameState.initial(definition),
      history: history,
      personality: personality,
    );
  }

  GameSession._({
    required this.definition,
    required this._machine,
    required this._controller,
    required this._mood,
    required this._state,
    required List<Exchange> history,
    required this.personality,
  }) : _history = List.of(history);

  /// Continues a saved play-through, or returns `null` if [snapshot] no
  /// longer fits [definition] (another game, or the room was removed after
  /// the game was edited).
  static GameSession? tryRestore({
    required GameDefinition definition,
    required LlmProvider llm,
    required PromptConfig prompts,
    LlmProvider? narrationLlm,
    required SessionSnapshot snapshot,
    bool personality = true,
    ScriptRuntime scripts = const MiniScriptRuntime(),
  }) {
    if (snapshot.gameId != definition.id ||
        !definition.rooms.containsKey(snapshot.state.roomId)) {
      return null;
    }
    // Variables added to the game since the save start with their default.
    final variables = {
      ...definition.initialVariables,
      ...snapshot.state.variables,
    };
    return GameSession(
      definition: definition,
      llm: llm,
      prompts: prompts,
      narrationLlm: narrationLlm,
      personality: personality,
      scripts: scripts,
      state: snapshot.state.copyWith(variables: variables),
      history: snapshot.history,
    );
  }

  /// The game being played.
  final GameDefinition definition;

  final StateMachine _machine;
  final GameController _controller;
  final MoodDirector _mood;

  /// Whether stage 2 speaks in the game's personality (otherwise in a
  /// neutral voice); may change between turns.
  bool personality;

  /// Saved history is bounded.
  static const _maxStoredExchanges = 50;

  final _sideEvents = StreamController<GameEvent>.broadcast();

  GameState _state;
  final List<Exchange> _history;
  Future<void> _companionWork = Future.value();
  bool _busy = false;
  bool _closed = false;

  /// Room, inventory and turn counter right now.
  GameState get state => _state;

  /// The conversation so far, oldest first.
  List<Exchange> get history => List.unmodifiable(_history);

  /// Whether the opening has been narrated.
  bool get hasStarted => _history.isNotEmpty;

  /// Whether the player reached an end room.
  bool get isOver => definition.room(_state.roomId).isEnd;

  /// Whether a turn is in progress.
  bool get isBusy => _busy;

  /// Events produced between turns: [MoodChanged].
  Stream<GameEvent> get sideEvents => _sideEvents.stream;

  /// Actions available in the current room.
  List<GameAction> availableActions() => _machine.availableActions(_state);

  /// The rendered description of the current room.
  String describeRoom() => _machine.describeRoom(_state);

  /// The ambience of the current room — what to play when resuming.
  AmbienceCue get currentAmbience =>
      AmbienceCue(definition.room(_state.roomId).ambience);

  /// Narrates the opening. Only valid before the first turn.
  Future<TurnResult> start() => _exclusive(() async {
    if (hasStarted) throw StateError('The game has already started');
    final result = await _controller.startGame(
      _state,
      personality: personality,
    );
    _history.add(result.exchange);
    return result;
  });

  /// Processes the player's [input].
  Future<TurnResult> send(String input) => _exclusive(() async {
    if (isOver) throw StateError('The game is over');
    await _companionWork;
    final result = await _controller.processInput(
      _state,
      _history,
      input,
      personality: personality,
    );
    _state = result.state;
    _history.add(result.exchange);
    _trimHistory();
    if (!result.isGameOver) _companionWork = _runCompanion(history);
    return result;
  });

  /// Completes once the companion's work after the last turn is applied —
  /// only then is [state] complete for saving.
  Future<void> get settled => _companionWork;

  /// A persistable copy of the current progress.
  SessionSnapshot snapshot() => SessionSnapshot(
    gameId: definition.id,
    state: _state,
    history: _history,
    savedAt: DateTime.now(),
  );

  /// Stops emitting [sideEvents]; pending companion work is discarded.
  Future<void> close() async {
    _closed = true;
    await _sideEvents.close();
  }

  Future<TurnResult> _exclusive(Future<TurnResult> Function() turn) async {
    if (_closed) throw StateError('The session is closed');
    if (_busy) throw StateError('A turn is already in progress');
    _busy = true;
    try {
      return await turn();
    } finally {
      _busy = false;
    }
  }

  Future<void> _runCompanion(List<Exchange> history) async {
    final mood = _mood;
    if (mood.scale.isNotEmpty) {
      final current = '${_state.variables[mood.variable] ?? mood.scale.first}';
      final next = await mood.nextMood(current: current, history: history);
      if (next != null && !_closed) {
        _state = _state.copyWith(
          variables: {..._state.variables, mood.variable: next},
        );
        _sideEvents.add(MoodChanged(from: current, to: next));
      }
    }
  }

  void _trimHistory() {
    if (_history.length > _maxStoredExchanges) {
      _history.removeRange(0, _history.length - _maxStoredExchanges);
    }
  }
}
