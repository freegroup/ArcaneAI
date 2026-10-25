import 'package:flutter/foundation.dart';

import '../../data/repositories/game_session_repository.dart';
import '../../data/repositories/model_repository.dart';
import '../../routing/routes.dart';
import '../../utils/command.dart';
import '../../utils/result.dart';

/// Decides where the app starts: model setup if the model is missing,
/// straight back into the last game if there is one, otherwise the game
/// list. There is never a "continue?" prompt — a game in progress resumes.
final class StartupViewModel extends ChangeNotifier {
  StartupViewModel({
    required ModelRepository models,
    required GameSessionRepository sessions,
  }) : _models = models,
       _sessions = sessions {
    resolve = Command0(_resolve)..execute();
  }

  final ModelRepository _models;
  final GameSessionRepository _sessions;

  /// Resolves the start location.
  late final Command0<String> resolve;

  Future<Result<String>> _resolve() async {
    if (!await _models.isAvailable()) return const Result.ok(Routes.setup);
    if (await _models.prepare() case Error()) {
      return const Result.ok(Routes.setup); // shows what went wrong
    }
    final lastGame = await _sessions.lastPlayedGameId();
    return Result.ok(lastGame == null ? Routes.home : Routes.game(lastGame));
  }

  @override
  void dispose() {
    resolve.dispose();
    super.dispose();
  }
}
