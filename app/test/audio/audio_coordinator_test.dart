import 'dart:async';

import 'package:arcane_player/audio/arcane_audio.dart';
import 'package:arcane_player/content/arcane_content.dart';
import 'package:arcane_player/engine/arcane_engine.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('SoundLibrary', () {
    final sounds = {
      'map/wind.wav': const PackFile(
        ref: ContentRef('g/sounds/map__wind.m4a'),
        expected: ExpectedFile(size: 10, sha256: 'aa'),
      ),
      'birds.wav': const PackFile(
        ref: ContentRef('g/sounds/birds.m4a'),
        expected: ExpectedFile(size: 20, sha256: 'bb'),
        bundled: false,
      ),
    };

    test('resolves a known sound through the resolver chain', () async {
      final library = SoundLibrary(
        resolver: ContentResolver([
          _FakeSource({'g/sounds/map__wind.m4a': const AssetContent('a')}),
        ]),
        sounds: sounds,
      );
      expect(
        await library.resolve(const SoundRef('map/wind.wav')),
        isA<AssetContent>(),
      );
    });

    test('unknown or unavailable sounds are silent, not errors', () async {
      final library = SoundLibrary(
        resolver: ContentResolver([_FakeSource({})]),
        sounds: sounds,
      );
      expect(await library.resolve(const SoundRef('nope.wav')), isNull);
      expect(await library.resolve(const SoundRef('map/wind.wav')), isNull);
    });
  });

  group('AudioCoordinator', () {
    late _FakeJukebox jukebox;
    late _FakeSpeech speech;
    late _FakeMic mic;
    late AudioCoordinator audio;

    setUp(() {
      jukebox = _FakeJukebox();
      speech = _FakeSpeech();
      mic = _FakeMic();
      audio =
          AudioCoordinator(jukebox: jukebox, speech: speech, microphone: mic)
            ..library = SoundLibrary(
              resolver: ContentResolver([
                _FakeSource({
                  'g/wind': const FileContent('/wind'),
                  'g/pick': const FileContent('/pick'),
                }),
              ]),
              sounds: {
                'map/wind.wav': const PackFile(
                  ref: ContentRef('g/wind'),
                  expected: ExpectedFile(size: 1, sha256: 'x'),
                ),
                'pick.wav': const PackFile(
                  ref: ContentRef('g/pick'),
                  expected: ExpectedFile(size: 1, sha256: 'x'),
                ),
              },
            );
    });

    tearDown(() => audio.dispose());

    Future<void> settle() => Future<void>.delayed(Duration.zero);

    test('a turn plays its cues and starts reading the narration', () async {
      await audio.handleTurn(const [
        EffectCue(SoundPlayback(SoundRef('pick.wav'), volume: 80)),
        RoomEntered('garden'),
        AmbienceCue(SoundPlayback(SoundRef('map/wind.wav'), volume: 40)),
      ], narration: 'Du gehst in den Garten.');

      expect(jukebox.effects, [80]);
      expect(jukebox.ambienceVolume, 40);
      expect(speech.spoken, ['Du gehst in den Garten.']);
      expect(
        speech.stops,
        1,
        reason: 'a new turn interrupts the previous voice',
      );
    });

    test(
      'the ambience ducks while speaking and recovers when speech ends',
      () async {
        await audio.handleTurn(const [], narration: 'Hallo.');
        await settle();
        expect(jukebox.gain, audio.duckedGain);
        speech.finish();
        await settle();
        expect(jukebox.gain, 1);
      },
    );

    test('an interrupted voice also ends the ducking', () async {
      await audio.handleTurn(const [], narration: 'Hallo.');
      await settle();
      await audio.handleTurn(const []); // next turn stops the voice
      await settle();
      expect(jukebox.gain, 1);
    });

    test('listening stops the voice, ducks, and blocks narration', () async {
      await audio.handleTurn(const [], narration: 'Erzählung.');
      expect(await audio.startListening((_) {}), isTrue);
      await settle();
      expect(speech.isSpeaking, isFalse);
      expect(jukebox.gain, audio.duckedGain);

      await audio.announce('Sollte stumm bleiben.');
      expect(speech.spoken, ['Erzählung.']);

      await audio.stopListening();
      await settle();
      expect(jukebox.gain, 1);
    });

    test('a missing microphone is reported, not thrown', () async {
      final deaf = AudioCoordinator(jukebox: _FakeJukebox());
      expect(deaf.hasMicrophone, isFalse);
      expect(await deaf.startListening((_) {}), isFalse);
      await deaf.dispose();
    });
  });

  group('AdaptiveSpeechOutput', () {
    test('switches to the screen reader and silences the voice', () async {
      final voice = _FakeSpeech();
      final reader = _FakeSpeech();
      final adaptive = AdaptiveSpeechOutput(voice: voice, screenReader: reader);

      await adaptive.speak('eins');
      adaptive.useScreenReader = true;
      await adaptive.speak('zwei');

      expect(voice.spoken, ['eins']);
      expect(voice.isSpeaking, isFalse);
      expect(reader.spoken, ['zwei']);
      await adaptive.dispose();
    });
  });
}

class _FakeSource implements ContentSource {
  _FakeSource(this._table);

  final Map<String, ResolvedContent> _table;
  final requested = <String>[];

  @override
  Future<ResolvedContent?> resolve(
    ContentRef ref, {
    ExpectedFile? expected,
  }) async {
    requested.add(ref.path);
    return _table[ref.path];
  }
}

class _FakeJukebox implements Jukebox {
  int? ambienceVolume;
  double gain = 1;
  final effects = <int>[];

  @override
  Future<void> playAmbience(
    ResolvedContent? content, {
    int volume = 100,
  }) async => ambienceVolume = content == null ? null : volume;

  @override
  Future<void> playEffect(
    ResolvedContent content, {
    int volume = 100,
    Duration? duration,
  }) async => effects.add(volume);

  @override
  Future<void> setAmbienceGain(double value) async => gain = value;

  @override
  Future<void> stopAll() async {}

  @override
  Future<void> dispose() async {}
}

class _FakeSpeech implements SpeechOutput {
  final spoken = <String>[];
  int stops = 0;
  bool _speaking = false;
  final _changes = StreamController<bool>.broadcast();

  void finish() => _set(false);

  void _set(bool value) {
    _speaking = value;
    _changes.add(value);
  }

  @override
  bool get isSpeaking => _speaking;

  @override
  Stream<bool> get onSpeakingChanged => _changes.stream;

  @override
  Future<void> speak(String text) async {
    spoken.add(text);
    _set(true);
  }

  @override
  Future<void> stop() async {
    stops++;
    if (_speaking) _set(false);
  }

  @override
  Future<void> dispose() => _changes.close();
}

class _FakeMic implements SpeechInput {
  bool _listening = false;
  final _changes = StreamController<bool>.broadcast();

  void _set(bool value) {
    _listening = value;
    _changes.add(value);
  }

  @override
  bool get isAvailable => true;

  @override
  bool get isListening => _listening;

  @override
  Stream<bool> get onListeningChanged => _changes.stream;

  @override
  Future<bool> initialize() async => true;

  @override
  Future<void> listen(void Function(SpeechResult result) onResult) async =>
      _set(true);

  @override
  Future<void> stop() async => _set(false);

  @override
  Future<void> dispose() => _changes.close();
}
