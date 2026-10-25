import '../../llm/llm_provider.dart';
import '../history/exchange.dart';
import '../runtime/game_state.dart';
import '../builtin_functions/builtin_registry.dart';
import 'prompt_builder.dart';

/// Stage 1: maps the player's input to one of the functions possible right
/// now — nothing else, no text.
///
/// The model gets the dialogue so far like any chat model, as in Python:
/// what the player said and what was answered, the welcome included. An answer that calls no function, or one that was
/// not offered, is discarded and the model is asked again — told
/// emphatically that the fallback (`keine_aktion`) is fine. If that fails
/// too, the fallback counts.
final class DecisionStage {
  const DecisionStage(this.llm, this.prompts, this.builtins);

  final LlmProvider llm;
  final PromptBuilder prompts;

  /// The built-in functions; their fallback counts when no answer is usable.
  final BuiltinRegistry builtins;

  /// The function the player's [input] asks for — a game action or a
  /// built-in one.
  Future<String> decide(
    GameState state,
    List<Exchange> history,
    String input,
  ) async {
    final config = prompts.config;
    final functions = prompts.functions(state);
    final conversation = [
      LlmMessage.system(prompts.systemPrompt(state)),
      for (final exchange in recentExchanges(
        history,
        count: config.historyLength,
        chars: config.historyChars,
      )) ...[
        LlmMessage.user(exchange.playerInput),
        LlmMessage.assistant(
          exchange.narration,
          // A failed turn counts as the fallback: on_system_error was
          // never offered.
          functionCall:
              exchange.action == null ||
                  exchange.action == builtins.onError.name
              ? builtins.fallback.name
              : exchange.action,
        ),
      ],
    ];

    var question = input;
    for (var attempt = 1; attempt <= config.maxAttempts; attempt++) {
      final response = await llm.chat(
        [...conversation, LlmMessage.user(question)],
        functions: functions,
        stage: 'Stufe 1 · Funktionswahl · Versuch $attempt',
        maxOutputTokens: config.maxOutputTokens,
      );
      final called = response.functionCall;
      final problem = _problem(called, functions);
      if (problem == null) return called!;
      question = prompts.retryInput(input, problem, functions);
    }
    return builtins.fallback.name;
  }

  /// Why an answer is discarded, or `null` if it is fine.
  String? _problem(String? called, List<LlmFunction> offered) {
    if (called == null) return 'Du hast keine Funktion aufgerufen.';
    if (!offered.any((function) => function.name == called)) {
      return "Die Funktion '$called' gibt es hier nicht.";
    }
    return null;
  }
}
