import 'package:meta/meta.dart';

/// One round of conversation: what the player said, the action that fired
/// and what the player was told. The welcome is an exchange whose input is
/// the opening instruction.
@immutable
final class Exchange {
  const Exchange({
    required this.playerInput,
    required this.narration,
    this.action,
    this.isWelcome = false,
  });

  /// Restores an exchange written by [toJson].
  factory Exchange.fromJson(Map<String, Object?> json) => Exchange(
    playerInput: json['input'] as String? ?? '',
    narration: json['narration'] as String? ?? '',
    action: json['action'] as String?,
    isWelcome: json['welcome'] as bool? ?? false,
  );

  /// The player's words (for the welcome: the opening instruction).
  final String playerInput;

  /// What the player was told.
  final String narration;

  /// The function that ran in this turn — a game action or a built-in one
  /// (`null` for the welcome, and in saves of older versions).
  final String? action;

  /// Whether this is the game's opening.
  final bool isWelcome;

  /// JSON representation.
  Map<String, Object?> toJson() => {
    'input': playerInput,
    'narration': narration,
    if (action != null) 'action': action,
    if (isWelcome) 'welcome': true,
  };
}

/// The latest of [history] — at most [count] exchanges and [chars]
/// characters of input and narration, since a model's context is limited.
List<Exchange> recentExchanges(
  List<Exchange> history, {
  required int count,
  required int chars,
}) {
  final recent = <Exchange>[];
  var used = 0;
  for (final exchange in history.reversed.take(count)) {
    used += exchange.playerInput.length + exchange.narration.length;
    if (used > chars) break;
    recent.insert(0, exchange);
  }
  return recent;
}
