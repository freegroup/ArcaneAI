import '../../llm/llm_provider.dart';
import '../builtin_functions/builtin_registry.dart';
import '../definition/game_definition.dart';
import '../runtime/game_state.dart';
import '../runtime/state_machine.dart';
import 'prompt_config.dart';

/// Builds the prompts of stage 1 from [config] (the `prompt_rule_stage1.yaml`
/// file) and the game: the role, the decision rules, the goal and the
/// current room. Stage 1 only chooses the function, so it gets the rules
/// about choosing — not the personality (that is stage 2's).
final class PromptBuilder {
  const PromptBuilder(this.machine, this.builtins, this.config);

  /// The game's rules.
  final StateMachine machine;

  /// The built-in functions, offered next to the game's actions.
  final BuiltinRegistry builtins;

  /// The stage-1 prompt and context-length settings.
  final DecisionConfig config;

  GameDefinition get _game => machine.definition;

  /// The system prompt: the role, the goal, the current room and — last,
  /// next to the conversation — how to decide. Without the personality:
  /// stage 1 only chooses. The functions themselves (game actions and the
  /// built-in ones) are handed over as tools, not listed here.
  String systemPrompt(GameState state) {
    final prompt = StringBuffer()
      ..write(config.role)
      ..write('\n\n');
    if (_game.gameTarget.isNotEmpty) {
      prompt.write('SPIELZIEL:\n${_game.gameTarget}\n\n');
    }
    prompt
      ..write('AKTUELLER RAUM:\n${machine.describeRoom(state)}\n\n')
      ..write(config.rulesFor(builtins.fallback.name));
    return prompt.toString();
  }

  /// The functions offered: the game's actions possible right now (their
  /// conditions hold), then the built-in ones — they win a name clash. The
  /// `after_fire` hint of an action is about the answer: it goes to stage 2.
  List<LlmFunction> functions(GameState state) => [
    for (final action in machine.availableActions(state))
      if (builtins.byName(action.name) == null)
        LlmFunction(action.name, action.description),
    for (final builtin in builtins.functions)
      LlmFunction(builtin.name, builtin.description),
  ];

  /// The player's [input] once more, after an answer was discarded for
  /// [reason].
  String retryInput(String input, String reason, List<LlmFunction> functions) =>
      '$input\n\n'
      '(HINWEIS: Deine letzte Antwort war ungültig. $reason '
      'Rufe genau eine dieser Funktionen auf: '
      '${functions.map((f) => f.name).join(', ')}. '
      'Passt keine, dann rufe ${builtins.fallback.name} auf.)';
}
