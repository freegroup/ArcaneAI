import 'package:arcane_player/content/arcane_content.dart';
import 'package:flutter/foundation.dart';

import '../../data/repositories/game_catalog_repository.dart';
import '../../utils/command.dart';
import '../../utils/result.dart';

/// View model for the home screen: the list of games to choose from.
final class HomeViewModel extends ChangeNotifier {
  HomeViewModel({required GameCatalogRepository catalog}) : _catalog = catalog {
    loadGames = Command0(_loadGames)..execute();
  }

  final GameCatalogRepository _catalog;

  /// Loads the catalog of games.
  late final Command0<List<CatalogEntry>> loadGames;

  List<CatalogEntry> _games = const [];

  /// The available games.
  List<CatalogEntry> get games => _games;

  Future<Result<List<CatalogEntry>>> _loadGames() async {
    final result = await _catalog.games();
    if (result case Ok(:final value)) {
      _games = value;
      notifyListeners();
    }
    return result;
  }

  @override
  void dispose() {
    loadGames.dispose();
    super.dispose();
  }
}
