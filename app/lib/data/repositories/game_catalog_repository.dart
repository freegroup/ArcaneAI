import 'package:arcane_player/content/arcane_content.dart';
import 'package:arcane_player/engine/arcane_engine.dart';

import '../../utils/result.dart';

/// Lists available games and loads a game's definition + sound table through
/// the content layer (bundle today, server later).
final class GameCatalogRepository {
  GameCatalogRepository({
    required ContentResolver resolver,
    required GamePackLoader loader,
  }) : _resolver = resolver,
       _loader = loader;

  final ContentResolver _resolver;
  final GamePackLoader _loader;

  /// The games the player can choose from.
  Future<Result<List<CatalogEntry>>> games() async {
    try {
      return Result.ok(await _loader.catalog());
    } on Object catch (e) {
      return Result.error(e);
    }
  }

  /// Loads game [gameId]: parsed definition plus its sound table.
  Future<Result<LoadedGame>> load(String gameId) async {
    try {
      final pack = await _loader.load(gameId);
      final definition = OverlayParser.parseJson(
        id: pack.manifest.gameId,
        modelJson: pack.modelJson,
        configJson: pack.configJson,
      );
      return Result.ok(
        LoadedGame(
          title: pack.manifest.title,
          definition: definition,
          sounds: pack.manifest.sounds,
          resolver: _resolver,
        ),
      );
    } on Object catch (e) {
      return Result.error(e);
    }
  }
}

/// A loaded game ready to play: its definition and everything needed to
/// resolve its sounds.
final class LoadedGame {
  const LoadedGame({
    required this.title,
    required this.definition,
    required this.sounds,
    required this.resolver,
  });

  /// Display title (from the pack manifest).
  final String title;

  /// The parsed game.
  final GameDefinition definition;

  /// Sound table (ref → pack file).
  final Map<String, PackFile> sounds;

  /// Resolver for the game's content.
  final ContentResolver resolver;
}
