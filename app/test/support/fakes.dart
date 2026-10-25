import 'dart:collection';
import 'dart:convert';
import 'dart:io';

import 'package:arcane_player/audio/arcane_audio.dart';
import 'package:arcane_player/content/arcane_content.dart';
import 'package:arcane_player/engine/arcane_engine.dart';
import 'package:yaml/yaml.dart';
import 'package:arcane_player/data/repositories/model_repository.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';

/// Language model that replays scripted answers: stage 1 takes its function
/// calls from one queue, stage 2 its narrations from another; the companion
/// gets no opinion.
final class FakeLlm implements LlmProvider, LlmSource {
  final _decisions = Queue<String>();
  final _narrations = Queue<String>();

  /// Stage and system prompt of every request received, in order.
  final requests = <({String stage, String system})>[];

  /// Queues a stage-1 call of [function].
  void decide(String function) => _decisions.add(function);

  /// Queues a stage-2 narration.
  void narrate(String text) => _narrations.add(text);

  @override
  LlmProvider get llm => this;

  @override
  String get label => 'fake';

  @override
  Future<LlmResponse> chat(
    List<LlmMessage> messages, {
    List<LlmFunction> functions = const [],
    String stage = '',
    int? maxOutputTokens,
  }) async {
    requests.add((stage: stage, system: messages.first.content));
    if (stage.startsWith('Begleiter')) return const LlmResponse(content: '');
    if (stage.startsWith('Stufe 2')) {
      return LlmResponse(
        content: _narrations.isEmpty ? 'Erzählt.' : _narrations.removeFirst(),
      );
    }
    return LlmResponse(
      content: '',
      functionCall: _decisions.isEmpty ? noAction : _decisions.removeFirst(),
    );
  }
}

/// Records what is played.
final class FakeJukebox implements Jukebox {
  ResolvedContent? ambience;
  int effectsPlayed = 0;
  @override
  Future<void> playAmbience(
    ResolvedContent? content, {
    int volume = 100,
  }) async => ambience = content;
  @override
  Future<void> playEffect(
    ResolvedContent content, {
    int volume = 100,
    Duration? duration,
  }) async => effectsPlayed++;
  @override
  Future<void> setAmbienceGain(double gain) async {}
  @override
  Future<void> stopAll() async {}
  @override
  Future<void> dispose() async {}
}

/// Records what is spoken.
final class FakeSpeech implements SpeechOutput {
  final spoken = <String>[];

  @override
  bool get isSpeaking => false;
  @override
  Stream<bool> get onSpeakingChanged => const Stream.empty();
  @override
  Future<void> speak(String text) async => spoken.add(text);
  @override
  Future<void> stop() async {}
  @override
  Future<void> dispose() async {}
}

/// Serves assets from memory.
final class FakeAssetBundle extends CachingAssetBundle {
  FakeAssetBundle(this._assets);

  final Map<String, String> _assets;

  @override
  Future<ByteData> load(String key) async {
    final text = _assets[key];
    if (text == null) throw FlutterError('Asset $key not found');
    return ByteData.sublistView(utf8.encode(text));
  }
}

Directory? _contentDir;

/// A unique temp directory for a file store.
Future<Directory> tempDir() =>
    Directory.systemTemp.createTemp('arcane_app_test');

/// A resolver backed by a temp directory holding a tiny "mini" game pack
/// (pack.json, model.json, config.json and dummy sound files), with correct
/// sizes/checksums so the real content pipeline is exercised.
ContentResolver fakeResolver() {
  final dir = _contentDir ??= _writeMiniPack();
  return ContentResolver([CacheContentSource(Future.value(dir))]);
}

Directory _writeMiniPack() {
  final dir = Directory.systemTemp.createTempSync('arcane_app_content');
  final gameDir = Directory('${dir.path}/mini/sounds')
    ..createSync(recursive: true);

  Map<String, Object?> file(String path, String contents) {
    final f = File('${dir.path}/mini/$path')..writeAsStringSync(contents);
    return {
      'path': path,
      'size': f.lengthSync(),
      'sha256': 'unchecked-by-cache-source',
      'bundled': true,
    };
  }

  const model = '''
{
  "states": {
    "s1": {"name": "hall", "stateType": "START",
      "userData": {"system_prompt": "Eine Halle.", "ambient_sound": "map/wind.wav", "ambient_sound_volume": 30},
      "trigger": [{"name": "nimm_schluessel", "description": "Den Schlüssel nehmen",
        "sound_effect": "pick.wav", "actions": ["has_key = true"]}]},
    "s2": {"name": "exit", "stateType": "END", "userData": {"system_prompt": "Frei."}}
  },
  "connections": {
    "c1": {"name": "oeffne_tuer", "source": {"node": "s1"}, "target": {"node": "s2"},
      "userData": {"description": "Tür öffnen", "conditions": ["has_key == true"]}}
  }
}''';
  const config = '''
{
  "personality": "Knapp.",
  "welcome_prompt": "Begrüße den Spieler.",
  "game_target": "Finde den Schlüssel.",
  "inventory": [{"key": "has_key", "value": false, "type": "boolean"}]
}''';

  // Dummy sound files; the loader only verifies model/config, but the audio
  // layer resolves these by size.
  final sounds = <String, Object?>{
    'pick.wav': _dummySound(gameDir, 'pick.m4a'),
    'map/wind.wav': _dummySound(gameDir, 'map__wind.m4a'),
  };

  File('${dir.path}/mini/pack.json').writeAsStringSync(
    jsonEncode({
      'id': 'mini',
      'title': 'Mini',
      'version': 1,
      'model': file('model.json', model),
      'config': file('config.json', config),
      'sounds': sounds,
    }),
  );
  File('${dir.path}/catalog.json').writeAsStringSync(
    jsonEncode({
      'games': [
        {'id': 'mini', 'title': 'Mini'},
      ],
    }),
  );
  return dir;
}

Map<String, Object?> _dummySound(Directory soundsDir, String name) {
  const bytes = 'sound';
  File('${soundsDir.path}/$name').writeAsStringSync(bytes);
  return {
    'path': 'sounds/$name',
    'size': bytes.length,
    'sha256': 'unchecked-by-cache-source',
    'bundled': true,
  };
}

PromptConfig? _cachedPrompts;

/// The real stage prompts from `lib/config/prompts/`, same single source as
/// the app. Cached across tests.
PromptConfig testPrompts() => _cachedPrompts ??= PromptConfig.fromMap(
  stage1: _readPrompt('prompt_rule_stage1.yaml'),
  stage2WithFunction: _readPrompt('prompt_rule_stage2_with_function.yaml'),
  stage2WithoutFunction: _readPrompt(
    'prompt_rule_stage2_without_function.yaml',
  ),
  companion: _readPrompt('prompt_rule_mood.yaml'),
);

Map<String, Object?> _readPrompt(String name) => Map<String, Object?>.from(
  loadYaml(File('lib/config/prompts/$name').readAsStringSync()) as Map,
);
