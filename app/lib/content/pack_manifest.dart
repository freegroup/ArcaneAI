import 'dart:convert';

import 'package:meta/meta.dart';

import 'content.dart';

/// Description of a game pack (`<gameId>/pack.json`), written by
/// `tool/build_game_pack.py`.
@immutable
final class PackManifest {
  PackManifest({
    required this.gameId,
    required this.title,
    required this.version,
    required this.model,
    required this.config,
    required Map<String, PackFile> sounds,
  }) : sounds = Map.unmodifiable(sounds);

  /// Parses `pack.json`. Throws [FormatException] if malformed.
  factory PackManifest.fromJson(String json) {
    try {
      final data = (jsonDecode(json) as Map).cast<String, Object?>();
      final gameId = data['id']! as String;
      PackFile file(Object? raw) =>
          PackFile.fromJson(gameId, (raw! as Map).cast());
      return PackManifest(
        gameId: gameId,
        title: data['title'] as String? ?? gameId,
        version: data['version'] as int? ?? 1,
        model: file(data['model']),
        config: file(data['config']),
        sounds: {
          for (final MapEntry(:key, :value)
              in (data['sounds'] as Map? ?? const {}).entries)
            key as String: file(value),
        },
      );
    } on TypeError catch (e) {
      throw FormatException('Malformed pack manifest: $e');
    }
  }

  /// Game identifier (folder name).
  final String gameId;

  /// Display title.
  final String title;

  /// Content version; bumped whenever the pack changes.
  final int version;

  /// The game's `model.json`.
  final PackFile model;

  /// The game's `config.json`.
  final PackFile config;

  /// Sound files by the reference used in the game definition
  /// (e.g. `map/wind.wav` → `sounds/map__wind.m4a`).
  final Map<String, PackFile> sounds;
}

/// A file of a pack.
@immutable
final class PackFile {
  const PackFile({
    required this.ref,
    required this.expected,
    this.bundled = true,
  });

  /// Parses a `{path, size, sha256, bundled}` entry of pack [gameId].
  factory PackFile.fromJson(String gameId, Map<String, Object?> json) =>
      PackFile(
        ref: ContentRef.inGame(gameId, json['path']! as String),
        expected: ExpectedFile(
          size: json['size']! as int,
          sha256: json['sha256']! as String,
        ),
        bundled: json['bundled'] as bool? ?? true,
      );

  /// Where the file lives in the content tree.
  final ContentRef ref;

  /// Size and checksum.
  final ExpectedFile expected;

  /// Whether the app ships the file; otherwise it has to be downloaded.
  final bool bundled;
}

/// An entry of `catalog.json`: the games available.
@immutable
final class CatalogEntry {
  const CatalogEntry({required this.gameId, required this.title});

  /// Game identifier.
  final String gameId;

  /// Display title.
  final String title;

  /// Parses `catalog.json` (`{"games": [{"id", "title"}]}`).
  static List<CatalogEntry> listFromJson(String json) {
    try {
      final games = (jsonDecode(json) as Map)['games'] as List;
      return [
        for (final game in games.cast<Map<String, Object?>>())
          CatalogEntry(
            gameId: game['id']! as String,
            title: game['title'] as String? ?? game['id']! as String,
          ),
      ];
    } on TypeError catch (e) {
      throw FormatException('Malformed catalog: $e');
    }
  }
}
