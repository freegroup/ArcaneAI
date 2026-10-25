import 'dart:collection';
import 'dart:io';

import 'package:arcane_player/engine/arcane_engine.dart';
import 'package:yaml/yaml.dart';

/// One request the fake model received.
typedef Request = ({
  String stage,
  List<LlmMessage> messages,
  List<LlmFunction> functions,
  int? maxOutputTokens,
});

/// Language model that replays scripted answers: stage 1 takes its function
/// calls from one queue, stage 2 its narrations from another (by default it
/// echoes the first line of what it was given); the companion's questions
/// get [judgement].
final class FakeLlm implements LlmProvider {
  FakeLlm({this.judgement = ''});

  /// Answer to the companion's question (mood).
  String judgement;

  final _decisions = Queue<LlmResponse>();
  final _narrations = Queue<String>();

  /// Every request received, in order.
  final requests = <Request>[];

  /// The requests of [stage] ('Stufe 1', 'Stufe 2', 'Begleiter').
  List<Request> of(String stage) => [
    for (final request in requests)
      if (request.stage.startsWith(stage)) request,
  ];

  /// Queues a stage-1 answer calling [function] (or none for `null`).
  void enqueue(String? function, [String text = '']) =>
      _decisions.add(LlmResponse(content: text, functionCall: function));

  /// Queues a stage-2 narration.
  void narrate(String text) => _narrations.add(text);

  @override
  String get label => 'fake';

  @override
  Future<LlmResponse> chat(
    List<LlmMessage> messages, {
    List<LlmFunction> functions = const [],
    String stage = '',
    int? maxOutputTokens,
  }) async {
    requests.add((
      stage: stage,
      messages: messages,
      functions: functions,
      maxOutputTokens: maxOutputTokens,
    ));
    if (stage.startsWith('Begleiter')) return LlmResponse(content: judgement);
    if (stage.startsWith('Stufe 2')) {
      return LlmResponse(
        content: _narrations.isEmpty
            ? 'Erzählt: ${messages.last.content.split('\n').first}'
            : _narrations.removeFirst(),
      );
    }
    return _decisions.isEmpty
        ? const LlmResponse(content: '', functionCall: noAction)
        : _decisions.removeFirst();
  }
}

/// Loads a game from the repository's `maps/` folder.
GameDefinition loadMap(String id) => OverlayParser.parseJson(
  id: id,
  modelJson: File('../maps/$id/model.json').readAsStringSync(),
  configJson: File('../maps/$id/config.json').readAsStringSync(),
);

/// A small hand-written game covering triggers, transitions, conditions,
/// scripts, enums, sounds and an end room.
GameDefinition miniGame() => GameDefinition(
  id: 'mini',
  initialRoomId: 'hall',
  personality:
      '{% if companion_mood == "grob" %}Grob.{% else %}Nett.{% endif %}',
  gameTarget: 'Finde den Schlüssel und öffne die Tür.',
  rooms: {
    'hall': const Room(
      id: 'hall',
      description:
          'Eine Halle.{% if not has_key %} Ein Schlüssel liegt hier.{% endif %}',
      kind: RoomKind.start,
      ambience: SoundPlayback(SoundRef('map/wind.wav'), volume: 30),
    ),
    'garden': const Room(id: 'garden', description: 'Ein Garten.'),
    'exit': const Room(
      id: 'exit',
      description: 'Freiheit.',
      kind: RoomKind.end,
    ),
  },
  actions: const [
    GameAction(
      name: 'nimm_schluessel',
      from: 'hall',
      to: 'hall',
      description: 'Den Schlüssel nehmen',
      afterFire: 'Du hast ihn.',
      conditions: ['has_key == false'],
      scripts: ['has_key = true', 'coins = coins + 1'],
      effect: SoundPlayback(
        SoundRef('pickup.wav'),
        duration: Duration(seconds: 2),
      ),
    ),
    GameAction(
      name: 'gehe_garten',
      from: 'hall',
      to: 'garden',
      description: 'In den Garten',
    ),
    GameAction(
      name: 'gehe_halle',
      from: 'garden',
      to: 'hall',
      description: 'Zurück',
    ),
    GameAction(
      name: 'oeffne_tuer',
      from: 'hall',
      to: 'exit',
      description: 'Die Tür aufschließen',
      conditions: ['has_key == true'],
    ),
    GameAction(
      name: 'werde_boese',
      from: 'garden',
      to: 'garden',
      description: 'Ungültige Stimmung setzen',
      scripts: ['companion_mood = "wuetend"'],
    ),
  ],
  variables: const {
    'has_key': VariableDefinition(
      key: 'has_key',
      initialValue: false,
      type: VariableType.boolean,
    ),
    'coins': VariableDefinition(
      key: 'coins',
      initialValue: 0,
      type: VariableType.integer,
    ),
    'companion_mood': VariableDefinition(
      key: 'companion_mood',
      initialValue: 'neutral',
      type: VariableType.enumeration,
      allowedValues: ['freundlich', 'neutral', 'grob'],
    ),
  },
);

PromptConfig? _cachedPrompts;

/// The real stage prompts from `lib/config/prompts/`, so tests use the same
/// single source as the app. Cached across tests.
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
