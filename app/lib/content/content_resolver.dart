import 'dart:io';

import 'package:flutter/services.dart';

import 'content.dart';
import 'pack_manifest.dart';

/// Asks [sources] in order (typically bundled → cache → HTTP) and returns
/// the first hit.
final class ContentResolver {
  ContentResolver(List<ContentSource> sources, {AssetBundle? bundle})
    : _sources = List.unmodifiable(sources),
      _bundle = bundle ?? rootBundle;

  final List<ContentSource> _sources;
  final AssetBundle _bundle;

  /// Locates [ref], or `null` if no source has it.
  Future<ResolvedContent?> resolve(
    ContentRef ref, {
    ExpectedFile? expected,
  }) async {
    for (final source in _sources) {
      final content = await source.resolve(ref, expected: expected);
      if (content != null) return content;
    }
    return null;
  }

  /// Locates a [PackFile] (with checksum expectations).
  Future<ResolvedContent?> resolveFile(PackFile file) =>
      resolve(file.ref, expected: file.expected);

  /// Reads [ref] as UTF-8 text; throws [ContentNotFoundException].
  Future<String> readString(ContentRef ref, {ExpectedFile? expected}) async {
    final content = await resolve(ref, expected: expected);
    return switch (content) {
      AssetContent(:final key) => _bundle.loadString(key, cache: false),
      FileContent(:final path) => File(path).readAsString(),
      null => throw ContentNotFoundException(ref),
    };
  }
}

/// No source could provide the requested content.
final class ContentNotFoundException implements Exception {
  const ContentNotFoundException(this.ref);

  /// What was requested.
  final ContentRef ref;

  @override
  String toString() => 'ContentNotFoundException: $ref';
}
