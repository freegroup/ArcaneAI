import 'builtin_function.dart';

/// Name of [ActionKeineAktion].
const noAction = 'keine_aktion';

/// None of the game's actions fits: nothing happens, the companion just
/// answers. Also what counts when stage 1 gives no usable answer.
final class ActionKeineAktion extends BuiltinFunction {
  const ActionKeineAktion();

  @override
  String get name => noAction;

  @override
  String get description => 'Keine der Aktionen passt zur Eingabe des Spielers';

  @override
  String run(BuiltinContext context) =>
      'Es wurde keine Aktion ausgeführt. Antworte dem Spieler im Rahmen '
      'deiner Rolle und gib ihm Kontext aus dem AKTUELLEN RAUM.';
}
