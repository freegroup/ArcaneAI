import 'builtin_function.dart';

/// Something in the game failed (e.g. a game action's script): nothing
/// happens, and the companion says so, fitting what the player was about to
/// do. Never offered to stage 1 — the engine chooses it.
final class ActionOnSystemError extends BuiltinFunction {
  const ActionOnSystemError();

  @override
  String get name => 'on_system_error';

  @override
  String get description => 'Im Spiel ist ein Fehler aufgetreten';

  @override
  String run(BuiltinContext context) {
    final attempted = context.attempted;
    final wanted = attempted == null
        ? 'Der Spieler wollte etwas tun'
        : 'Der Spieler wollte etwas tun (${attempted.description.trim()})';
    return '$wanted, aber dabei ist im Spiel ein Fehler aufgetreten — es ist '
        'nichts passiert. Sag ihm das im Rahmen deiner Rolle, passend zu dem, '
        'was er vorhatte, und dass er es noch einmal versuchen kann.';
  }
}
