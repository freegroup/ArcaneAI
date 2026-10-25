import '../definition/game_definition.dart';
import '../runtime/game_state.dart';
import '../runtime/state_machine.dart';

/// A function every game offers next to its own actions (those of its
/// model.json). Stage 1 can choose it like a game action.
///
/// It never changes the game state — that is what game actions are for.
/// When it is chosen, [run] tells stage 2 how to answer the player.
///
/// A new built-in function is a subclass plus an entry in
/// `BuiltinRegistry.standard`.
abstract base class BuiltinFunction {
  const BuiltinFunction();

  /// The name stage 1 calls it by.
  String get name;

  /// What it is for — stage 1 matches the player's input against it.
  String get description;

  /// What stage 2 is told when this function was chosen in [context].
  String run(BuiltinContext context);
}

/// The game a built-in function runs in.
final class BuiltinContext {
  const BuiltinContext({
    required this.machine,
    required this.state,
    this.attempted,
  });

  /// The game's rules.
  final StateMachine machine;

  /// The game state when the function was chosen.
  final GameState state;

  /// The game action the player attempted, when this function stands in
  /// for it (it failed).
  final GameAction? attempted;
}
