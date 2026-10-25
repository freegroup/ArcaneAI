import 'package:meta/meta.dart';

import '../definition/game_definition.dart';
import '../events/game_event.dart';
import '../scripting/mini_script_runtime.dart';
import '../scripting/script_runtime.dart';
import 'game_state.dart';

/// Rules of a game: which actions are available and what firing one does.
/// Port of the Python `StateEngine` + `Inventory`, but functional: it never
/// mutates, it maps a [GameState] to the next one.
///
/// Script failures never crash the game — like in Python they make a
/// condition false, an action fail, or a template stay raw — and are
/// reported through the optional `warnings` sink of each call.
final class StateMachine {
  const StateMachine(
    this.definition, {
    this.scripts = const MiniScriptRuntime(),
  });

  /// The game.
  final GameDefinition definition;

  /// Evaluates conditions, scripts and templates.
  final ScriptRuntime scripts;

  /// Actions of the current room whose conditions all hold.
  List<GameAction> availableActions(
    GameState state, {
    List<String>? warnings,
  }) => [
    for (final action in definition.actionsFrom(state.roomId))
      if (_conditionsHold(action, state, warnings)) action,
  ];

  /// Fires the available action [name] in [state].
  ActionOutcome apply(GameState state, String name, {List<String>? warnings}) {
    final action = availableActions(
      state,
      warnings: warnings,
    ).where((a) => a.name == name).firstOrNull;
    if (action == null) {
      return ActionRejected("Aktion '$name' ist hier nicht verfügbar.");
    }

    var variables = state.variables;
    for (final script in action.scripts) {
      try {
        variables = _enforceTypes(
          scripts.execute(script, variables),
          variables,
          warnings,
        );
      } on ScriptException catch (e) {
        warnings?.add('Script "$script" (${action.name}): ${e.message}');
        return ActionRejected("Aktion '$name' konnte nicht ausgeführt werden.");
      }
    }

    final next = state.copyWith(roomId: action.to, variables: variables);
    final changed = {
      for (final key in {...state.variables.keys, ...variables.keys})
        if (state.variables[key] != variables[key]) key,
    };
    final room = definition.room(action.to);
    return ActionApplied(
      action: action,
      state: next,
      events: [
        if (action.effect case final effect?) EffectCue(effect),
        if (action.isTransition) ...[
          RoomEntered(room.id),
          AmbienceCue(room.ambience),
        ],
        if (changed.isNotEmpty)
          InventoryChanged(next.variables, changedKeys: changed),
        if (action.isTransition && room.isEnd) GameOver(room.id),
      ],
    );
  }

  /// Renders [template] against the inventory of [state].
  String render(String template, GameState state, {List<String>? warnings}) {
    try {
      return scripts.render(template, state.variables);
    } on ScriptException catch (e) {
      warnings?.add('Template: ${e.message}');
      return template;
    }
  }

  /// Description of the current room, rendered.
  String describeRoom(GameState state, {List<String>? warnings}) => render(
    definition.room(state.roomId).description,
    state,
    warnings: warnings,
  ).trim();

  bool _conditionsHold(
    GameAction action,
    GameState state,
    List<String>? warnings,
  ) {
    for (final condition in action.conditions) {
      try {
        if (!scripts.evaluateCondition(condition, state.variables)) {
          return false;
        }
      } on ScriptException catch (e) {
        warnings?.add('Condition "$condition" (${action.name}): ${e.message}');
        return false;
      }
    }
    return true;
  }

  /// Enumerations only accept their declared values; an invalid assignment
  /// is reverted (as `Inventory._sync_from_lua` does in Python).
  Map<String, Object?> _enforceTypes(
    Map<String, Object?> updated,
    Map<String, Object?> previous,
    List<String>? warnings,
  ) {
    final result = Map.of(updated);
    for (final MapEntry(:key, :value) in updated.entries) {
      final definition = this.definition.variables[key];
      if (definition != null && !definition.accepts(value)) {
        warnings?.add("Invalid value '$value' for '$key' reverted.");
        result[key] = previous[key];
      }
    }
    return result;
  }
}

/// Result of [StateMachine.apply].
@immutable
sealed class ActionOutcome {
  const ActionOutcome();
}

/// The action fired.
final class ActionApplied extends ActionOutcome {
  const ActionApplied({
    required this.action,
    required this.state,
    required this.events,
  });

  /// The action that fired.
  final GameAction action;

  /// The state afterwards.
  final GameState state;

  /// Sounds, room change, inventory change, game over — in that order.
  final List<GameEvent> events;
}

/// The action could not fire (not available, or a script failed).
final class ActionRejected extends ActionOutcome {
  const ActionRejected(this.reason);

  /// Human-readable reason.
  final String reason;
}
