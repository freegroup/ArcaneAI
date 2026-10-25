import 'builtin_function.dart';
import 'action_helfe_dem_spieler.dart';
import 'action_keine_aktion.dart';
import 'action_on_system_error.dart';

/// The built-in functions of every game.
final class BuiltinRegistry {
  const BuiltinRegistry({
    required this.functions,
    required this.fallback,
    required this.onError,
  });

  /// The built-in functions of every game.
  static const standard = BuiltinRegistry(
    functions: [ActionKeineAktion(), ActionHelfeDemSpieler()],
    fallback: ActionKeineAktion(),
    onError: ActionOnSystemError(),
  );

  /// The functions offered to stage 1 next to the game's actions, in this
  /// order.
  final List<BuiltinFunction> functions;

  /// What counts when stage 1 gives no usable answer: one of [functions].
  final BuiltinFunction fallback;

  /// What the engine chooses when something in the game fails. Never
  /// offered to stage 1.
  final BuiltinFunction onError;

  /// The offered built-in function called [name], or `null` if it is none.
  BuiltinFunction? byName(String name) =>
      functions.where((function) => function.name == name).firstOrNull;
}
