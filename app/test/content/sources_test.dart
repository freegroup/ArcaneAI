import 'dart:convert';
import 'dart:io';

import 'package:arcane_player/content/arcane_content.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late Directory tempDir;
  late CacheContentSource cache;

  setUp(() async {
    tempDir = await Directory.systemTemp.createTemp('arcane_content_test');
    cache = CacheContentSource(Future.value(tempDir));
  });

  tearDown(() => tempDir.delete(recursive: true));

  ExpectedFile expect256(String body) =>
      ExpectedFile(size: utf8.encode(body).length, sha256: 'not-checked');

  group('CacheContentSource', () {
    test('resolves a stored file and rejects a wrong-sized one', () async {
      final file = File('${tempDir.path}/g/model.json');
      await file.parent.create(recursive: true);
      await file.writeAsString('hello');

      const ref = ContentRef('g/model.json');
      expect(await cache.resolve(ref), isA<FileContent>());
      expect(
        await cache.resolve(ref, expected: expect256('hello')),
        isA<FileContent>(),
      );
      expect(
        await cache.resolve(
          ref,
          expected: const ExpectedFile(size: 999, sha256: 'x'),
        ),
        isNull,
      );
    });

    test('misses cleanly for an absent file', () async {
      expect(await cache.resolve(const ContentRef('nope')), isNull);
    });
  });

  group('ContentResolver', () {
    test('asks sources in order and returns the first hit', () async {
      final log = <String>[];
      ContentSource stub(String name, ResolvedContent? result) =>
          _StubSource((ref) {
            log.add(name);
            return result;
          });
      final resolver = ContentResolver([
        stub('bundled', null),
        stub('cache', const FileContent('/tmp/x')),
        stub('http', const AssetContent('never')),
      ]);

      final resolved = await resolver.resolve(const ContentRef('x'));
      expect(resolved, const FileContent('/tmp/x'));
      expect(log, ['bundled', 'cache'], reason: 'stops at the first hit');
    });

    test('throws ContentNotFoundException when nothing has it', () {
      final resolver = ContentResolver([_StubSource((_) => null)]);
      expect(
        () => resolver.readString(const ContentRef('x')),
        throwsA(isA<ContentNotFoundException>()),
      );
    });
  });
}

class _StubSource implements ContentSource {
  _StubSource(this._resolve);

  final ResolvedContent? Function(ContentRef) _resolve;

  @override
  Future<ResolvedContent?> resolve(
    ContentRef ref, {
    ExpectedFile? expected,
  }) async => _resolve(ref);
}
