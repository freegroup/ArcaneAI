import 'package:arcane_player/engine/arcane_engine.dart';
import 'package:flutter/foundation.dart';

import '../../utils/result.dart';
import '../services/file_store_service.dart';
import 'game_catalog_repository.dart';
import 'model_repository.dart';

/// Owns the running [GameSession] and makes saving invisible: progress is
/// stored after every turn and when the app is backgrounded, and opening a
/// game continues where it was left. The player never sees "save" or "load".
/// Counterpart of the Python `session.py` + `session_store.py`.
final class GameSessionRepository extends ChangeNotifier {
  GameSessionRepository({
    required GameCatalogRepository catalog,
    required LlmSource llm,
    required FileStoreService store,
    required PromptConfig prompts,
  }) : _catalog = catalog,
       _llm = llm,
       _store = store,
       _prompts = prompts;

  static const _activeKey = 'active_game';
  static const _snapshotPrefix = 'snapshot_';

  final GameCatalogRepository _catalog;
  final LlmSource _llm;
  final FileStoreService _store;
  final PromptConfig _prompts;

  GameSession? _session;
  LoadedGame? _loaded;

  /// The running session, or `null`.
  GameSession? get session => _session;

  /// The game of the running session (title, definition, sounds).
  LoadedGame? get loaded => _loaded;

  /// The game played last — resumed on launch — or `null`.
  Future<String?> lastPlayedGameId() async =>
      (await _store.readJson(_activeKey))?['gameId'] as String?;

  /// Opens game [gameId]: continues its saved progress if there is a valid
  /// one, otherwise starts it fresh.
  Future<Result<GameSession>> open(String gameId) =>
      _open(gameId, resume: true);

  /// Starts game [gameId] afresh, discarding its saved progress.
  Future<Result<GameSession>> restart(String gameId) async {
    await _store.delete('$_snapshotPrefix$gameId');
    return _open(gameId, resume: false);
  }

  Future<Result<GameSession>> _open(
    String gameId, {
    required bool resume,
  }) async {
    final llm = _llm.llm;
    if (llm == null) return Result.error(StateError('Model is not ready'));
    final LoadedGame loaded;
    switch (await _catalog.load(gameId)) {
      case Ok(:final value):
        loaded = value;
      case Error(:final error):
        return Result.error(error);
    }

    final session =
        (resume ? await _restore(loaded, llm) : null) ??
        GameSession(definition: loaded.definition, llm: llm, prompts: _prompts);

    await _session?.close();
    _session = session;
    _loaded = loaded;
    await _store.writeJson(_activeKey, {'gameId': gameId});
    notifyListeners();
    return Result.ok(session);
  }

  Future<GameSession?> _restore(LoadedGame loaded, LlmProvider llm) async {
    final saved = await _store.readJson(
      '$_snapshotPrefix${loaded.definition.id}',
    );
    if (saved == null) return null;
    try {
      return GameSession.tryRestore(
        definition: loaded.definition,
        llm: llm,
        prompts: _prompts,
        snapshot: SessionSnapshot.fromJson(saved),
      );
    } on FormatException {
      return null; // saved by an incompatible version — start fresh
    }
  }

  /// Stores the current progress. Called after every turn and whenever the
  /// app is backgrounded: mobile systems end background apps without
  /// warning. A finished game clears its save instead.
  Future<void> save() async {
    final session = _session;
    if (session == null) return;
    // The mood changes right after a turn: save the state with it.
    await session.settled;
    final key = '$_snapshotPrefix${session.definition.id}';
    if (session.isOver) {
      await _store.delete(key);
      await _store.delete(_activeKey);
    } else if (session.hasStarted) {
      await _store.writeJson(key, session.snapshot().toJson());
    }
  }

  /// Saves and closes the running session.
  Future<void> close() async {
    await save();
    await _session?.close();
    _session = null;
    _loaded = null;
  }
}
