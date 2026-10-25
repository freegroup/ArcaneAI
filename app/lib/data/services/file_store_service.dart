import 'dart:convert';
import 'dart:io';

import 'package:path_provider/path_provider.dart';

/// Stores small JSON documents (session snapshots) as files in the app's
/// support directory, written atomically.
final class FileStoreService {
  FileStoreService({Future<Directory>? directory})
    : _directory = directory ?? getApplicationSupportDirectory();

  final Future<Directory> _directory;

  Future<File> _file(String name) async =>
      File('${(await _directory).path}/$name');

  /// Reads and decodes `<name>.json`, or `null` if absent or unreadable.
  Future<Map<String, Object?>?> readJson(String name) async {
    final file = await _file('$name.json');
    if (!await file.exists()) return null;
    try {
      return jsonDecode(await file.readAsString()) as Map<String, Object?>;
    } on Object {
      return null;
    }
  }

  /// Writes [data] to `<name>.json` atomically (temp file + rename).
  Future<void> writeJson(String name, Map<String, Object?> data) async {
    final file = await _file('$name.json');
    final tmp = File('${file.path}.tmp');
    await tmp.parent.create(recursive: true);
    await tmp.writeAsString(jsonEncode(data), flush: true);
    await tmp.rename(file.path);
  }

  /// Deletes `<name>.json` if it exists.
  Future<void> delete(String name) async {
    final file = await _file('$name.json');
    if (await file.exists()) await file.delete();
  }
}
