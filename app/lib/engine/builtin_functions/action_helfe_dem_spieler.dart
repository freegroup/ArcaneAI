import 'builtin_function.dart';

/// The player asks what he can do: stage 2 gets what is possible right now
/// and gives a subtle hint. Nothing happens in the game.
final class ActionHelfeDemSpieler extends BuiltinFunction {
  const ActionHelfeDemSpieler();

  @override
  String get name => 'helfe_dem_spieler';

  @override
  String get description =>
      'Hilfe: Der Spieler fragt, was er tun kann oder soll, wie es '
      'weitergeht, oder bittet um Hilfe oder einen Tipp — z. B. '
      '"was kann ich tun?", "was soll ich machen?", "hilf mir", '
      '"wie geht es weiter?", "hast du einen Tipp?". Dann IMMER diese '
      'Funktion aufrufen, auch wenn es eine Frage ist — nicht keine_aktion.';

  @override
  String run(BuiltinContext context) {
    final possible = context.machine.availableActions(context.state);
    if (possible.isEmpty) {
      return 'Der Spieler bittet um Hilfe, aber hier ist gerade nichts zu '
          'tun. Sag ihm das im Rahmen deiner Rolle.';
    }
    return 'Der Spieler bittet um Hilfe. Gib ihm im Rahmen deiner Rolle '
        'einen hilfreichen, subtilen Hinweis auf eine der folgenden '
        'Möglichkeiten — verrate nicht alles, keine Liste:\n'
        '${possible.map((action) => '- ${action.description}').join('\n')}';
  }
}
