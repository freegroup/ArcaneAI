import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:audioplayers/audioplayers.dart';
import 'package:logging/logging.dart';

import 'audio_ports.dart';

final _log = Logger('tts');

/// Speech through Google Cloud Text-to-Speech, as in the Python game
/// (`game/src/voice/google_provider.py`): the text goes to Google, the
/// audio comes back and is played. Needs the network and an API key; if a
/// request fails, [fallback] speaks instead.
final class GoogleCloudSpeechOutput implements SpeechOutput {
  GoogleCloudSpeechOutput({
    required String apiKey,
    required this.fallback,
    this.voiceName = 'de-DE-Chirp3-HD-Schedar',
    this.languageCode = 'de-DE',
    this.pitch = 0,
    this.speakingRate = 1,
  }) : _apiKey = apiKey {
    _subscriptions = [
      _player.onPlayerStateChanged.listen(
        (state) => _set(state == PlayerState.playing),
      ),
      fallback.onSpeakingChanged.listen(_set),
    ];
  }

  static final _endpoint = Uri.parse(
    'https://texttospeech.googleapis.com/v1/text:synthesize',
  );

  /// Speaks when Google cannot.
  final SpeechOutput fallback;

  /// Google voice, as in config.yaml (`voice_name`).
  final String voiceName;

  /// Language, as in config.yaml (`language_code`).
  final String languageCode;

  /// As in config.yaml (`pitch`).
  final double pitch;

  /// As in config.yaml (`speaking_rate`).
  final double speakingRate;

  final String _apiKey;
  final _client = HttpClient();
  final _player = AudioPlayer();
  final StreamController<bool> _changes = StreamController.broadcast();
  late final List<StreamSubscription<Object?>> _subscriptions;
  bool _speaking = false;
  int _request = 0;
  File? _audio;

  @override
  bool get isSpeaking => _speaking;

  @override
  Stream<bool> get onSpeakingChanged => _changes.stream;

  @override
  Future<void> speak(String text) async {
    var clean = text.replaceAll('\n', ' ').trim();
    if (clean.isEmpty) return;
    // Google takes at most 5000 bytes — cut at the last sentence before.
    if (utf8.encode(clean).length > 4800) {
      final cut = clean.substring(0, 4800);
      final end = cut.lastIndexOf('.');
      clean = '${end < 0 ? cut : cut.substring(0, end)}.';
    }
    await _player.stop();
    await fallback.stop();
    final request = ++_request;
    try {
      final audio = await _synthesize(clean);
      if (request != _request) return; // a newer speak or stop came first
      final previous = _audio;
      final file = _audio = File(
        '${Directory.systemTemp.path}/arcane_tts_$request.mp3',
      );
      await file.writeAsBytes(audio, flush: true);
      await _player.play(DeviceFileSource(file.path));
      if (previous != null && await previous.exists()) await previous.delete();
    } on Object catch (e) {
      _log.warning('Google TTS fehlgeschlagen, die Systemstimme spricht: $e');
      if (request == _request) await fallback.speak(clean);
    }
  }

  Future<List<int>> _synthesize(String text) async {
    final request = await _client.postUrl(_endpoint);
    request.headers
      ..contentType = ContentType.json
      ..set('X-Goog-Api-Key', _apiKey);
    request.add(
      utf8.encode(
        jsonEncode({
          'input': {'text': text},
          'voice': {'languageCode': languageCode, 'name': voiceName},
          'audioConfig': {
            'audioEncoding': 'MP3',
            'pitch': pitch,
            'speakingRate': speakingRate,
          },
        }),
      ),
    );
    final response = await request.close().timeout(const Duration(seconds: 20));
    final body = await response.transform(utf8.decoder).join();
    if (response.statusCode != HttpStatus.ok) {
      throw HttpException('HTTP ${response.statusCode}: $body');
    }
    final json = jsonDecode(body) as Map<String, Object?>;
    return base64Decode(json['audioContent']! as String);
  }

  @override
  Future<void> stop() async {
    _request++;
    await _player.stop();
    await fallback.stop();
    _set(false);
  }

  @override
  Future<void> dispose() async {
    _request++;
    for (final subscription in _subscriptions) {
      await subscription.cancel();
    }
    await _player.dispose();
    await fallback.dispose();
    _client.close();
    await _changes.close();
    if (_audio case final file? when await file.exists()) await file.delete();
  }

  void _set(bool speaking) {
    if (_speaking == speaking || _changes.isClosed) return;
    _speaking = speaking;
    _changes.add(speaking);
  }
}
