import 'package:arcane_player/audio/system_speech_output.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('prefers the highest quality installed offline voice', () {
    final voices = [
      {'name': 'Anna', 'locale': 'de-DE', 'quality': 'default'},
      {'name': 'Petra', 'locale': 'de-DE', 'quality': 'enhanced'},
      {'name': 'Markus', 'locale': 'de-DE', 'quality': 'premium'},
      {'name': 'Ava', 'locale': 'en-US', 'quality': 'premium'},
    ];
    expect(bestVoice(voices, 'de-DE')?['name'], 'Markus');
  });

  test('skips voices that need the network or are not installed', () {
    final voices = [
      {
        'name': 'net',
        'locale': 'de-DE',
        'quality': 'very high',
        'network_required': '1',
      },
      {
        'name': 'missing',
        'locale': 'de-DE',
        'quality': 'very high',
        'network_required': '0',
        'features': 'notInstalled',
      },
      {
        'name': 'local',
        'locale': 'de-DE',
        'quality': 'high',
        'network_required': '0',
        'features': '',
      },
    ];
    expect(bestVoice(voices, 'de-DE')?['name'], 'local');
  });

  test('keeps the default voice when nothing better is installed', () {
    final voices = [
      {'name': 'Anna', 'locale': 'de-DE', 'quality': 'default'},
      {'name': 'x', 'locale': 'de-DE', 'quality': 'normal'},
    ];
    expect(bestVoice(voices, 'de-DE'), isNull);
  });
}
