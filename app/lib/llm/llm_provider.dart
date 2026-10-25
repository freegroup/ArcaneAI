import 'package:meta/meta.dart';

/// Who wrote a message.
enum LlmRole { system, user, assistant }

/// One message of a conversation. Port of the Python `LLMMessage`.
@immutable
final class LlmMessage {
  const LlmMessage.system(this.content)
    : role = LlmRole.system,
      functionCall = null;
  const LlmMessage.user(this.content)
    : role = LlmRole.user,
      functionCall = null;
  const LlmMessage.assistant(this.content, {this.functionCall})
    : role = LlmRole.assistant;

  final LlmRole role;
  final String content;

  /// The function this earlier answer called, if any.
  final String? functionCall;
}

/// A function the model may call. Port of the Python `LLMFunction`.
@immutable
final class LlmFunction {
  const LlmFunction(this.name, this.description);

  final String name;

  /// What it does — the model matches the player's intent against it.
  final String description;
}

/// What the model answered: its text and the function it called, if any.
/// Port of the Python `LLMResponse`.
@immutable
final class LlmResponse {
  const LlmResponse({required this.content, this.functionCall});

  /// The answer in text.
  final String content;

  /// Name of the called function, or `null` if the model called none.
  final String? functionCall;
}

/// A language model, used like any chat API: every call is complete in
/// itself. Port of the Python `BaseLLMProvider`.
abstract interface class LlmProvider {
  /// Human-readable description (model, runtime).
  String get label;

  /// Answers the last of [messages]. They start with the system message,
  /// followed by the conversation so far (user and assistant in turn) and
  /// end with the user message to answer. [functions] are offered for
  /// calling; [stage] names the caller in the prompt log. At most
  /// [maxOutputTokens] are generated (`null`: the provider's default).
  Future<LlmResponse> chat(
    List<LlmMessage> messages, {
    List<LlmFunction> functions = const [],
    String stage = '',
    int? maxOutputTokens,
  });
}
