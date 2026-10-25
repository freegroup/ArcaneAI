import 'package:meta/meta.dart';

import 'content.dart';
import 'content_resolver.dart';
import 'pack_manifest.dart';

/// Reads the catalog and game packs through a [ContentResolver] — so packs
/// can come from the app bundle today and from a server tomorrow.
final class GamePackLoader {
  const GamePackLoader(this._resolver);

  final ContentResolver _resolver;

  /// The games listed in `catalog.json`.
  Future<List<CatalogEntry>> catalog() async => CatalogEntry.listFromJson(
    await _resolver.readString(const ContentRef('catalog.json')),
  );

  /// The manifest and definition files of game [gameId].
  Future<GamePack> load(String gameId) async {
    final manifest = PackManifest.fromJson(
      await _resolver.readString(ContentRef.inGame(gameId, 'pack.json')),
    );
    final model = await _resolver.readString(
      manifest.model.ref,
      expected: manifest.model.expected,
    );
    final config = await _resolver.readString(
      manifest.config.ref,
      expected: manifest.config.expected,
    );
    return GamePack(manifest: manifest, modelJson: model, configJson: config);
  }
}

/// A loaded game pack: manifest plus the raw definition files.
@immutable
final class GamePack {
  const GamePack({
    required this.manifest,
    required this.modelJson,
    required this.configJson,
  });

  /// Pack description incl. the sound table.
  final PackManifest manifest;

  /// Raw `model.json`.
  final String modelJson;

  /// Raw `config.json`.
  final String configJson;
}
