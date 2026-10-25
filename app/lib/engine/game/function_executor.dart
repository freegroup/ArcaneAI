import 'package:logging/logging.dart';
import 'package:meta/meta.dart';

import '../builtin_functions/builtin_function.dart';
import '../builtin_functions/builtin_registry.dart';
import '../definition/game_definition.dart';
import '../events/game_event.dart';
import '../runtime/game_state.dart';
import '../runtime/state_machine.dart';

final _log = Logger('game');

/// The step between the two stages: runs the function stage 1 chose.
///
/// A game action fires on the [StateMachine] and changes the world; a
/// built-in function changes nothing and only tells stage 2 how to answer.
/// Either way stage 2 gets a [FunctionOutcome.note].
final class FunctionExecutor {
  const FunctionExecutor(this.machine, this.builtins);

  /// The game's rules.
  final StateMachine machine;

  /// The built-in functions.
  final BuiltinRegistry builtins;

  /// Runs the function called [name] in [state].
  FunctionOutcome run(GameState state, String name) {
    if (builtins.byName(name) case final builtin?) {
      return _builtin(builtin, state);
    }
    final warnings = <String>[];
    switch (machine.apply(state, name, warnings: warnings)) {
      case final ActionApplied applied:
        return FunctionOutcome(
          function: name,
          state: applied.state,
          events: applied.events,
          firedAction: name,
          note: _actionNote(applied.action, applied.state),
        );
      case ActionRejected(:final reason):
        // Unavailable actions are never offered, so the game itself failed
        // (a broken script).
        _log.warning('$reason ${warnings.join(' · ')}');
        return _builtin(
          builtins.onError,
          state,
          attempted: machine.definition.actions
              .where((action) => action.name == name)
              .firstOrNull,
        );
    }
  }

  FunctionOutcome _builtin(
    BuiltinFunction function,
    GameState state, {
    GameAction? attempted,
  }) => FunctionOutcome(
    function: function.name,
    state: state,
    note: function.run(
      BuiltinContext(machine: machine, state: state, attempted: attempted),
    ),
  );

  /// What stage 2 is told about the game action [action] that fired: its
  /// name, what the player does with it (its description — this is the only
  /// place that says to describe a room), and what follows from it in the
  /// game (its hint, rendered against [state], the state afterwards).
  String _actionNote(GameAction action, GameState state) {
    final result = machine.render(action.afterFire, state).trim();
    return [
      'Ausgeführte Aktion: ${action.name}',
      'Was der Spieler damit tut: ${action.description.trim()}',
      if (result.isNotEmpty) 'Folge im Spiel: $result',
      if (action.isTransition)
        'Neuer Raum: Der Spieler ist jetzt im AKTUELLEN RAUM.',
    ].join('\n');
  }
}

/// What running the chosen function produced.
@immutable
final class FunctionOutcome {
  const FunctionOutcome({
    required this.function,
    required this.state,
    required this.note,
    this.events = const [],
    this.firedAction,
  });

  /// The function whose effect happened: a game action or a built-in one.
  final String function;

  /// The game state afterwards.
  final GameState state;

  /// Room change, sounds, inventory change, game over.
  final List<GameEvent> events;

  /// The game action that fired, if any.
  final String? firedAction;

  /// What stage 2 is told: what happened, or how to answer.
  final String note;
}
