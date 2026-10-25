import 'dart:io';

import 'package:flutter/services.dart';
import 'package:logging/logging.dart';

import 'content.dart';

final _log = Logger('arcane_content');

/// Content shipped inside the app as Flutter assets below [root].
final class BundledContentSource implements ContentSource {
  BundledContentSource({AssetBundle? bundle, this.root = 'assets/games'})
    : _bundle = bundle ?? rootBundle;

  final AssetBundle _bundle;

  /// Asset folder that corresponds to the content root.
  final String root;

  late final Future<Set<String>> _assets = AssetManifest.loadFromAssetBundle(
    _bundle,
  ).then((manifest) => manifest.listAssets().toSet());

  @override
  Future<ResolvedContent?> resolve(
    ContentRef ref, {
    ExpectedFile? expected,
  }) async {
    final key = '$root/${ref.path}';
    return (await _assets).contains(key) ? AssetContent(key) : null;
  }
}

/// Content stored on the device below a directory (`<directory>/<path>`).
final class CacheContentSource implements ContentSource {
  CacheContentSource(this._directory);

  final Future<Directory> _directory;

  /// Where [ref] is (or would be) stored.
  Future<File> fileFor(ContentRef ref) async =>
      File('${(await _directory).path}/${ref.path}');

  @override
  Future<ResolvedContent?> resolve(
    ContentRef ref, {
    ExpectedFile? expected,
  }) async {
    final file = await fileFor(ref);
    if (!await file.exists()) return null;
    if (expected != null && await file.length() != expected.size) {
      _log.warning('Cached $ref has the wrong size — ignoring it');
      return null;
    }
    return FileContent(file.path);
  }
}
