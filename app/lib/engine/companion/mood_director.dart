import '../definition/game_definition.dart';
import '../game/prompt_config.dart';
import '../history/exchange.dart';
import '../../llm/llm_provider.dart';

/// Shifts the companion's mood by at most one step per evaluation, based on
/// how the player talks. Port of `CompanionDirector._update_mood`.
///
/// The mood is an enum inventory variable (default `companion_mood`); its
/// declared values form the scale from positive to negative. The personality
/// template reacts to it. Games without that variable have no mood. The
/// prompt and context length come from [config] (`prompt_rule_mood.yaml`).
final class MoodDirector {
  const MoodDirector({
    required this.definition,
    required this.llm,
    required this.config,
    this.variable = defaultVariable,
  });

  /// The game.
  final GameDefinition definition;

  /// The inventory variable that holds the mood in the games.
  static const defaultVariable = 'companion_mood';

  /// Judges the player's tone.
  final LlmProvider llm;

  /// The prompt and context-length settings.
  final MoodConfig config;

  /// Inventory variable holding the mood.
  final String variable;

  /// Mood scale from positive to negative; empty if the game has no mood.
  List<String> get scale {
    final declared = definition.variables[variable];
    if (declared == null || declared.type != VariableType.enumeration) {
      return const [];
    }
    return [for (final v in declared.allowedValues) '$v'];
  }

  /// The mood after [history], or `null` if it stays [current].
  /// Never throws: the mood is flavour, not game logic.
  ///
  /// The model gets the latest dialogue with both sides — what the
  /// companion said and how the player reacted — and is asked which mood the
  /// player's behaviour should lead to.
  Future<String?> nextMood({
    required String current,
    required List<Exchange> history,
  }) async {
    final scale = this.scale;
    if (scale.isEmpty || !history.any((e) => !e.isWelcome)) return null;

    final scaleText = scale.join(', ');
    final messages = [
      LlmMessage.system(config.rulesFor(scaleText, current)),
      for (final exchange in recentExchanges(
        history,
        count: config.window,
        chars: config.historyChars,
      )) ...[
        LlmMessage.user(exchange.playerInput),
        LlmMessage.assistant(exchange.narration),
      ],
      LlmMessage.user(config.questionFor(scaleText)),
    ];

    try {
      final response = await llm.chat(
        messages,
        stage: 'Begleiter · Stimmung',
        maxOutputTokens: config.maxOutputTokens,
      );
      final answer = response.content;
      final word = answer
          .trim()
          .toLowerCase()
          .split(RegExp(r'\s+'))
          .first
          .replaceAll(RegExp(r'[^\wäöüß]'), '');
      final detected = scale.indexOf(word);
      if (detected < 0) return null;
      final from = scale.indexOf(current).clamp(0, scale.length - 1);
      final next = scale[detected.clamp(from - 1, from + 1)];
      return next == current ? null : next;
    } on Object {
      return null;
    }
  }
}
