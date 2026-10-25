import 'dart:convert';

import 'package:arcane_player/content/arcane_content.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('PackManifest', () {
    test('parses files, checksums and the sound table', () {
      final manifest = PackManifest.fromJson(
        jsonEncode({
          'id': 'TheTipsyQuest',
          'title': 'The Tipsy Quest',
          'version': 3,
          'model': {'path': 'model.json', 'size': 10, 'sha256': 'aa'},
          'config': {'path': 'config.json', 'size': 5, 'sha256': 'bb'},
          'sounds': {
            'map/wind.wav': {
              'path': 'sounds/map__wind.m4a',
              'size': 200,
              'sha256': 'cc',
            },
            'birds.wav': {
              'path': 'sounds/birds.m4a',
              'size': 300,
              'sha256': 'dd',
              'bundled': false,
            },
          },
        }),
      );

      expect(manifest.gameId, 'TheTipsyQuest');
      expect(manifest.title, 'The Tipsy Quest');
      expect(manifest.version, 3);
      expect(manifest.model.ref, const ContentRef('TheTipsyQuest/model.json'));
      expect(manifest.model.expected.sha256, 'aa');
      expect(
        manifest.sounds['map/wind.wav']!.ref,
        const ContentRef('TheTipsyQuest/sounds/map__wind.m4a'),
      );
      expect(manifest.sounds['map/wind.wav']!.bundled, isTrue);
      expect(manifest.sounds['birds.wav']!.bundled, isFalse);
    });

    test('rejects malformed JSON', () {
      expect(() => PackManifest.fromJson('{"id": 3}'), throwsFormatException);
      expect(() => PackManifest.fromJson('not json'), throwsFormatException);
    });
  });

  group('CatalogEntry', () {
    test('parses the game list and falls back to id for the title', () {
      final games = CatalogEntry.listFromJson(
        jsonEncode({
          'games': [
            {'id': 'a', 'title': 'Game A'},
            {'id': 'b'},
          ],
        }),
      );
      expect(games.map((g) => g.gameId), ['a', 'b']);
      expect(games[0].title, 'Game A');
      expect(games[1].title, 'b');
    });

    test('rejects a malformed catalog', () {
      expect(
        () => CatalogEntry.listFromJson('{"games": 3}'),
        throwsFormatException,
      );
    });
  });
}
