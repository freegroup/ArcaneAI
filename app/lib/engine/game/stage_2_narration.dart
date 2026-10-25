import '../../llm/llm_provider.dart';
import '../definition/game_definition.dart';
import '../history/exchange.dart';
import '../runtime/game_state.dart';
import '../runtime/state_machine.dart';
import 'prompt_config.dart';

/// Stage 2: tells the player what happened — in the game's personality
/// (pirate, drunkard, bore, …) and the companion's mood, or in a neutral
/// voice when the personality is switched off.
///
/// The engine, not the model, picks how to answer: [withAction] when a game
/// action ran (keep it short), [noAction] otherwise — keine_aktion, help,
/// error and the welcome — with more context and a stronger reference to the
/// room. Both come from `prompt_rule_stage2_*.yaml`. Stage 2 decides
/// nothing, so it can run on a different model than stage 1.
final class NarrationStage {
  const NarrationStage(this.llm, this.machine, this.withAction, this.noAction);

  final LlmProvider llm;

  /// The game's rules (personality, goal, rooms, actions).
  final StateMachine machine;

  /// Settings when a game action ran.
  final NarrationConfig withAction;

  /// Settings when no game action ran (and for the welcome).
  final NarrationConfig noAction;

  GameDefinition get _game => machine.definition;

  /// What opens the game.
  String get welcomeInput =>
      _game.welcomePrompt.isEmpty ? 'Das Spiel beginnt!' : _game.welcomePrompt;

  /// The opening narration — like "no action": the room is introduced.
  Future<String> welcome(GameState state, {required bool personality}) async {
    final response = await llm.chat(
      [
        LlmMessage.system(
          systemPrompt(state, noAction, personality: personality),
        ),
        LlmMessage.user(welcomeInput),
      ],
      stage: 'Stufe 2 · Erzählen (Begrüßung)',
      maxOutputTokens: noAction.maxOutputTokens,
    );
    return _tidy(response.content);
  }

  /// What the player is told after [input]; [note] says what the game did or
  /// how to answer, [state] is the state afterwards. [actionExecuted] picks
  /// the short case ([withAction]) or the richer one ([noAction]).
  Future<String> tell(
    GameState state,
    List<Exchange> history,
    String input,
    String note, {
    required bool personality,
    required bool actionExecuted,
  }) async {
    final config = actionExecuted ? withAction : noAction;
    final response = await llm.chat(
      [
        LlmMessage.system(
          systemPrompt(state, config, personality: personality),
        ),
        for (final exchange in recentExchanges(
          history,
          count: config.historyLength,
          chars: config.historyChars,
        )) ...[
          LlmMessage.user(exchange.playerInput),
          LlmMessage.assistant(exchange.narration),
        ],
        LlmMessage.user('$input\n\n(SPIEL:\n$note)'),
      ],
      stage: 'Stufe 2 · Erzählen',
      maxOutputTokens: config.maxOutputTokens,
    );
    return _tidy(response.content);
  }

  /// The system prompt: who speaks, the goal, the current room, what the
  /// player could do here (if [config] asks for it) and — last, next to the
  /// conversation — how to answer (from [config]).
  String systemPrompt(
    GameState state,
    NarrationConfig config, {
    required bool personality,
  }) {
    final prompt = StringBuffer()
      ..write(
        personality
            ? machine.render(_game.personality, state).trim()
            : config.role,
      )
      ..write('\n\n');
    if (_game.gameTarget.isNotEmpty) {
      prompt.write('SPIELZIEL:\n${_game.gameTarget}\n\n');
    }
    prompt.write('AKTUELLER RAUM:\n${machine.describeRoom(state)}\n\n');
    final actions = machine.availableActions(state);
    if (config.possibleActions != null && actions.isNotEmpty) {
      // Only the descriptions: the function names mean nothing to the player.
      prompt.write(
        '${config.possibleActionsFor(actions.map((a) => a.description.trim()))}\n\n',
      );
    }
    prompt.write(config.rules);
    return prompt.toString();
  }

  /// Trims the answer and collapses blank lines: the model likes to put a
  /// blank line between sentences, which shows as an extra empty line.
  static String _tidy(String text) =>
      text.trim().replaceAll(RegExp(r'\n\s*\n+'), '\n');
}
