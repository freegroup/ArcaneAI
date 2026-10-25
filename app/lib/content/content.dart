import 'package:meta/meta.dart';

/// A file in the content tree, addressed relative to the content root, e.g.
/// `catalog.json` or `TheTipsyQuest/sounds/wind.m4a`.
@immutable
final class ContentRef {
  const ContentRef(this.path);

  /// A file inside the pack of game [gameId].
  const ContentRef.inGame(String gameId, String path) : this('$gameId/$path');

  /// Path relative to the content root, `/`-separated.
  final String path;

  @override
  bool operator ==(Object other) => other is ContentRef && other.path == path;

  @override
  int get hashCode => path.hashCode;

  @override
  String toString() => path;
}

/// Where a file can be read from — all a consumer (e.g. an audio player)
/// needs to know.
@immutable
sealed class ResolvedContent {
  const ResolvedContent();
}

/// A file shipped with the app (Flutter asset key).
final class AssetContent extends ResolvedContent {
  const AssetContent(this.key);

  /// Asset key, e.g. `assets/games/TheTipsyQuest/model.json`.
  final String key;

  @override
  String toString() => 'asset:$key';
}

/// A file on the device (cache or download).
final class FileContent extends ResolvedContent {
  const FileContent(this.path);

  /// Absolute file path.
  final String path;

  @override
  String toString() => 'file:$path';
}

/// What a file is expected to look like (from the pack manifest).
@immutable
final class ExpectedFile {
  const ExpectedFile({required this.size, required this.sha256});

  /// Size in bytes.
  final int size;

  /// Lower-case hex SHA-256 of the content.
  final String sha256;
}

/// One way to obtain content. Returns `null` if it cannot provide [ref];
/// never throws for "not available".
abstract interface class ContentSource {
  /// Locates [ref]; [expected] lets sources validate what they deliver.
  Future<ResolvedContent?> resolve(ContentRef ref, {ExpectedFile? expected});
}
