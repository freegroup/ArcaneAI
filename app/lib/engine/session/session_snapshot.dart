import 'package:meta/meta.dart';

import '../history/exchange.dart';
import '../runtime/game_state.dart';

/// Everything needed to continue a play-through later. Plain data,
/// versioned JSON; storage is the app's business.
@immutable
final class SessionSnapshot {
  SessionSnapshot({
    required this.gameId,
    required this.state,
    required List<Exchange> history,
    required this.savedAt,
  }) : history = List.unmodifiable(history);

  /// Restores a snapshot written by [toJson].
  ///
  /// Throws a [FormatException] for unknown versions or malformed data.
  factory SessionSnapshot.fromJson(Map<String, Object?> json) {
    final version = json['version'];
    if (version != formatVersion) {
      throw FormatException('Unsupported snapshot version $version');
    }
    try {
      return SessionSnapshot(
        gameId: json['game'] as String,
        state: GameState.fromJson((json['state'] as Map).cast()),
        history: [
          for (final e in json['history'] as List)
            Exchange.fromJson((e as Map).cast()),
        ],
        savedAt: DateTime.parse(json['savedAt'] as String),
      );
    } on TypeError catch (e) {
      throw FormatException('Malformed snapshot: $e');
    }
  }

  /// Current format; bump when the structure changes incompatibly.
  static const formatVersion = 1;

  /// The game this snapshot belongs to.
  final String gameId;

  /// Room, inventory and turn counter.
  final GameState state;

  /// The conversation so far.
  final List<Exchange> history;

  /// When the snapshot was taken.
  final DateTime savedAt;

  /// JSON representation.
  Map<String, Object?> toJson() => {
    'version': formatVersion,
    'game': gameId,
    'state': state.toJson(),
    'history': [for (final e in history) e.toJson()],
    'savedAt': savedAt.toUtc().toIso8601String(),
  };
}
