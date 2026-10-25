import 'package:meta/meta.dart';

import '../../llm/llm_provider.dart';
import '../builtin_functions/builtin_registry.dart';
import '../events/game_event.dart';
import '../history/exchange.dart';
import '../runtime/game_state.dart';
import '../runtime/state_machine.dart';
import 'function_executor.dart';
import 'prompt_builder.dart';
import 'prompt_config.dart';
import 'stage_1_decision.dart';
import 'stage_2_narration.dart';

/// Runs one turn of the game loop. Port of the Python `GameController`:
///
/// 1. **Stage 1** ([DecisionStage]): the model picks the function the
///    player's input asks for — a game action or a built-in one.
/// 2. **Run it** ([FunctionExecutor]): a game action changes the world; a
///    built-in function only says how to answer.
/// 3. **Stage 2** ([NarrationStage]): the model tells the player, in the
///    game's personality unless the player switched it off.
///
/// Stateless: the caller owns the [GameState] and the history.
final class GameController {
  /// [narrationLlm] tells the player what happened; it may be a different
  /// model than [llm] — one that is strong in language but needs no
  /// function calling.
  GameController({
    required this.machine,
    required LlmProvider llm,
    required LlmProvider narrationLlm,
    required PromptConfig prompts,
  }) : _decision = DecisionStage(
         llm,
         PromptBuilder(machine, builtins, prompts.decision),
         builtins,
       ),
       _executor = FunctionExecutor(machine, builtins),
       _narration = NarrationStage(
         narrationLlm,
         machine,
         prompts.narrationWithAction,
         prompts.narrationNoAction,
       );

  /// The built-in functions of every game.
  static const builtins = BuiltinRegistry.standard;

  /// The game's rules.
  final StateMachine machine;

  final DecisionStage _decision;
  final FunctionExecutor _executor;
  final NarrationStage _narration;

  /// Said when the model gave no usable answer (as in Python).
  static const fallbackAnswer =
      "Hm? Ich versteh nicht was du meinst. Versuch's nochmal.";

  /// The opening narration. Nothing is decided; starts the room ambience.
  Future<TurnResult> startGame(
    GameState state, {
    required bool personality,
  }) async {
    final narration = await _narration.welcome(state, personality: personality);
    return TurnResult(
      input: _narration.welcomeInput,
      narration: narration.isEmpty ? fallbackAnswer : narration,
      state: state,
      events: [AmbienceCue(machine.definition.room(state.roomId).ambience)],
      isWelcome: true,
    );
  }

  /// Processes the player's [input].
  Future<TurnResult> processInput(
    GameState state,
    List<Exchange> history,
    String input, {
    required bool personality,
  }) async {
    // Stage 1: which function.
    final chosen = await _decision.decide(state, history, input);

    // Run it.
    final outcome = _executor.run(state, chosen);

    // Stage 2: what the player is told.
    final narration = await _narration.tell(
      outcome.state,
      history,
      input,
      outcome.note,
      personality: personality,
      actionExecuted: outcome.firedAction != null,
    );

    return TurnResult(
      input: input,
      narration: narration.isEmpty ? fallbackAnswer : narration,
      state: outcome.state.copyWith(turn: state.turn + 1),
      events: outcome.events,
      calledFunction: outcome.function,
      firedAction: outcome.firedAction,
    );
  }
}

/// Outcome of a turn — everything UI, audio and persistence need.
@immutable
final class TurnResult {
  TurnResult({
    required this.input,
    required this.narration,
    required this.state,
    required List<GameEvent> events,
    this.calledFunction,
    this.firedAction,
    this.isWelcome = false,
  }) : events = List.unmodifiable(events);

  /// The player's words (for the welcome: the opening instruction).
  final String input;

  /// What the player is told.
  final String narration;

  /// The game state after the turn.
  final GameState state;

  /// Room change, sounds, inventory change, game over.
  final List<GameEvent> events;

  /// The function whose effect happened — a game action or a built-in one;
  /// `null` for the welcome.
  final String? calledFunction;

  /// The game action that fired, if any.
  final String? firedAction;

  /// Whether this was the game's opening.
  final bool isWelcome;

  /// Whether the game ended with this turn.
  bool get isGameOver => events.any((e) => e is GameOver);

  /// This turn as a history entry.
  Exchange get exchange => Exchange(
    playerInput: input,
    narration: narration,
    action: calledFunction,
    isWelcome: isWelcome,
  );
}
