import 'package:meta/meta.dart';

/// Prompt and context-length settings of stage 1 (the function choice).
///
/// Loaded from `prompt_rule_stage1.yaml`. No prompt text
/// is hard-coded in the engine; it all lives in that file.
@immutable
final class DecisionConfig {
  const DecisionConfig({
    required this.role,
    required this.decisionRules,
    required this.historyLength,
    required this.historyChars,
    required this.maxOutputTokens,
    required this.maxAttempts,
  });

  factory DecisionConfig.fromMap(Map<String, Object?> json) => DecisionConfig(
    role: json['role']! as String,
    decisionRules: json['decisionRules']! as String,
    historyLength: (json['historyLength']! as num).toInt(),
    historyChars: (json['historyChars']! as num).toInt(),
    maxOutputTokens: (json['maxOutputTokens']! as num).toInt(),
    maxAttempts: (json['maxAttempts']! as num).toInt(),
  );

  /// The opening line of the system prompt.
  final String role;

  /// How to choose a function. `{fallback}` stands for the fallback
  /// function's name.
  final String decisionRules;

  /// How many of the latest exchanges the model sees.
  final int historyLength;

  /// The character budget of that history (the phone's context is small).
  final int historyChars;

  /// A function call needs only a few tokens.
  final int maxOutputTokens;

  /// How often the model is asked per turn before the fallback counts.
  final int maxAttempts;

  /// The decision rules with the fallback function's name filled in.
  String rulesFor(String fallback) =>
      decisionRules.replaceAll('{fallback}', fallback);
}

/// Prompt and context-length settings of stage 2 (the narration), for one
/// case: a game action ran, or none did.
///
/// Loaded from `prompt_rule_stage2_with_function.yaml` and
/// `prompt_rule_stage2_without_function.yaml`.
@immutable
final class NarrationConfig {
  const NarrationConfig({
    required this.role,
    required this.rules,
    required this.historyLength,
    required this.historyChars,
    required this.maxOutputTokens,
    this.possibleActions,
  });

  factory NarrationConfig.fromMap(Map<String, Object?> json) => NarrationConfig(
    role: json['role']! as String,
    rules: json['rules']! as String,
    historyLength: (json['historyLength']! as num).toInt(),
    historyChars: (json['historyChars']! as num).toInt(),
    maxOutputTokens: (json['maxOutputTokens']! as num).toInt(),
    possibleActions: json['possibleActions'] as String?,
  );

  /// The companion when the personality is switched off (same idea as
  /// stage 1's role: who speaks).
  final String role;

  /// How to answer.
  final String rules;

  /// How many of the latest exchanges the model sees.
  final int historyLength;

  /// The character budget of that history.
  final int historyChars;

  /// How long the answer may be.
  final int maxOutputTokens;

  /// What the player could do here, as background knowledge for hints;
  /// `{actions}` stands for the descriptions of the available actions.
  /// `null`: stage 2 gets no such list.
  final String? possibleActions;

  /// [possibleActions] with the [descriptions] filled in, one line each.
  String possibleActionsFor(Iterable<String> descriptions) => possibleActions!
      .replaceAll('{actions}', descriptions.map((d) => '- $d').join('\n'));
}

/// Prompt and context-length settings of the companion mood step (the mood
/// detector), loaded from `prompt_rule_mood.yaml`.
@immutable
final class MoodConfig {
  const MoodConfig({
    required this.rules,
    required this.question,
    required this.window,
    required this.historyChars,
    required this.maxOutputTokens,
  });

  factory MoodConfig.fromMap(Map<String, Object?> json) => MoodConfig(
    rules: json['rules']! as String,
    question: json['question']! as String,
    window: (json['window']! as num).toInt(),
    historyChars: (json['historyChars']! as num).toInt(),
    maxOutputTokens: (json['maxOutputTokens']! as num).toInt(),
  );

  /// The system prompt. `{scale}` stands for the mood scale, `{current}` for
  /// the current mood.
  final String rules;

  /// The closing question. `{scale}` stands for the mood scale.
  final String question;

  /// How many of the latest exchanges are judged.
  final int window;

  /// The character budget of that history.
  final int historyChars;

  /// A single mood word needs only a few tokens.
  final int maxOutputTokens;

  /// [rules] with the mood [scale] and [current] mood filled in.
  String rulesFor(String scale, String current) =>
      rules.replaceAll('{scale}', scale).replaceAll('{current}', current);

  /// [question] with the mood [scale] filled in.
  String questionFor(String scale) => question.replaceAll('{scale}', scale);
}

/// All prompt and context-length settings of the two stages. The engine
/// decides which stage-2 case applies — a game action ran
/// ([narrationWithAction]) or not ([narrationNoAction]) — not the model.
@immutable
final class PromptConfig {
  const PromptConfig({
    required this.decision,
    required this.narrationWithAction,
    required this.narrationNoAction,
    required this.mood,
  });

  factory PromptConfig.fromMap({
    required Map<String, Object?> stage1,
    required Map<String, Object?> stage2WithFunction,
    required Map<String, Object?> stage2WithoutFunction,
    required Map<String, Object?> companion,
  }) => PromptConfig(
    decision: DecisionConfig.fromMap(stage1),
    narrationWithAction: NarrationConfig.fromMap(stage2WithFunction),
    narrationNoAction: NarrationConfig.fromMap(stage2WithoutFunction),
    mood: MoodConfig.fromMap(companion),
  );

  /// Stage 1 (function choice).
  final DecisionConfig decision;

  /// Stage 2 when a game action ran: keep it short.
  final NarrationConfig narrationWithAction;

  /// Stage 2 when no game action ran (keine_aktion, help, error, welcome):
  /// more context, stronger reference to the room.
  final NarrationConfig narrationNoAction;

  /// The companion mood step.
  final MoodConfig mood;
}
