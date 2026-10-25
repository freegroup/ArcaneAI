import 'dart:convert';

import 'game_definition.dart';

/// Reads the editor's "overlay" format — `model.json` (rooms + connections)
/// and `config.json` (personality, inventory, texts) — into a
/// [GameDefinition]. Mirrors `GameEngine._convert_overlay_data` of the
/// Python engine.
abstract final class OverlayParser {
  /// Parses already decoded JSON documents.
  static GameDefinition parse({
    required String id,
    required Map<String, Object?> model,
    Map<String, Object?> config = const {},
  }) {
    final variables = _variables(_list(config['inventory']));

    final idToName = <String, String>{};
    final rooms = <String, Room>{};
    String? initial;
    final stateObjects = _map(model['states']);
    for (final MapEntry(key: stateId, value: raw) in stateObjects.entries) {
      final state = _map(raw);
      final name = _string(state['name']);
      if (name.isEmpty) continue;
      final userData = _map(state['userData']);
      final kind = switch (state['stateType']) {
        'START' => RoomKind.start,
        'END' => RoomKind.end,
        _ => RoomKind.normal,
      };
      if (kind == RoomKind.start) initial = name;
      idToName[stateId] = name;
      rooms[name] = Room(
        id: name,
        description: _string(userData['system_prompt']),
        kind: kind,
        ambience: _sound(
          userData['ambient_sound'],
          userData['ambient_sound_volume'],
        ),
      );
    }
    if (initial == null) {
      throw const FormatException('No room is marked as START');
    }

    final actions = <GameAction>[];
    for (final raw in _map(model['connections']).values) {
      final connection = _map(raw);
      final name = _string(connection['name']);
      final from = idToName[_map(connection['source'])['node']];
      final to = idToName[_map(connection['target'])['node']];
      if (name.isEmpty || from == null || to == null) continue;
      actions.add(_action(name, from, to, _map(connection['userData'])));
    }
    for (final raw in stateObjects.values) {
      final state = _map(raw);
      final room = _string(state['name']);
      for (final trigger in _list(state['trigger']).map(_map)) {
        final name = _string(trigger['name']);
        if (name.isEmpty || room.isEmpty) continue;
        actions.add(_action(name, room, room, trigger));
      }
    }

    return GameDefinition(
      id: id,
      initialRoomId: initial,
      rooms: rooms,
      actions: actions,
      variables: variables,
      personality: _string(config['personality']),
      welcomePrompt: _string(config['welcome_prompt']),
      gameTarget: _string(config['game_target']),
      helpText: _string(config['help_text']),
    );
  }

  /// Parses the raw JSON text of `model.json` and `config.json`.
  static GameDefinition parseJson({
    required String id,
    required String modelJson,
    String? configJson,
  }) => parse(
    id: id,
    model: _map(jsonDecode(modelJson)),
    config: configJson == null ? const {} : _map(jsonDecode(configJson)),
  );

  static GameAction _action(
    String name,
    String from,
    String to,
    Map<String, Object?> data,
  ) {
    final description = _string(data['description']);
    return GameAction(
      name: name,
      from: from,
      to: to,
      description: description.isEmpty ? name : description,
      afterFire: _string(data['system_prompt']),
      conditions: _strings(data['conditions']),
      scripts: _strings(data['actions']),
      effect: _sound(
        data['sound_effect'],
        data['sound_effect_volume'],
        duration: data['sound_effect_duration'],
      ),
    );
  }

  static Map<String, VariableDefinition> _variables(List<Object?> items) {
    final result = <String, VariableDefinition>{};
    for (final item in items.map(_map)) {
      final key = _string(item['key']);
      if (key.isEmpty) continue;
      final type = switch (item['type']) {
        'integer' => VariableType.integer,
        'boolean' => VariableType.boolean,
        'enum' => VariableType.enumeration,
        _ => VariableType.string,
      };
      result[key] = VariableDefinition(
        key: key,
        initialValue: item['value'],
        type: type,
        allowedValues: _list(item['values']),
      );
    }
    return result;
  }

  static SoundPlayback? _sound(
    Object? path,
    Object? volume, {
    Object? duration,
  }) {
    final file = _string(path);
    if (file.isEmpty) return null;
    final seconds = _number(duration);
    return SoundPlayback(
      SoundRef(file),
      volume: (_number(volume) ?? 100).round().clamp(0, 100),
      duration: seconds == null || seconds <= 0
          ? null
          : Duration(milliseconds: (seconds * 1000).round()),
    );
  }

  // The editor is lenient with types: numbers may arrive as strings or empty.
  static num? _number(Object? v) => v is num ? v : num.tryParse(_string(v));

  static String _string(Object? v) => v is String ? v : (v?.toString() ?? '');

  static Map<String, Object?> _map(Object? v) =>
      v is Map ? v.cast<String, Object?>() : const {};

  static List<Object?> _list(Object? v) => v is List ? v : const [];

  static List<String> _strings(Object? v) =>
      _list(v).whereType<String>().where((s) => s.trim().isNotEmpty).toList();
}
