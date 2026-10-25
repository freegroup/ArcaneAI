import 'package:arcane_player/engine/arcane_engine.dart';
import 'package:flutter_test/flutter_test.dart';

import 'support/fakes.dart';

/// A game whose only action has a script the runtime cannot execute.
GameDefinition brokenGame() => GameDefinition(
  id: 'broken',
  initialRoomId: 'hall',
  personality: '',
  gameTarget: '',
  rooms: const {
    'hall': Room(id: 'hall', description: 'Eine Halle.', kind: RoomKind.start),
  },
  actions: const [
    GameAction(
      name: 'zaubere',
      from: 'hall',
      to: 'hall',
      description: 'Einen Zauber wirken',
      scripts: ['coins = coins * 2'],
    ),
  ],
  variables: const {
    'coins': VariableDefinition(
      key: 'coins',
      initialValue: 0,
      type: VariableType.integer,
    ),
  },
);

void main() {
  const builtins = BuiltinRegistry.standard;
  final machine = StateMachine(miniGame());
  final start = GameState.initial(miniGame());

  group('registry', () {
    test('offers keine_aktion and helfe_dem_spieler; keine_aktion is the '
        'fallback', () {
      expect(builtins.functions.map((f) => f.name), [
        noAction,
        'helfe_dem_spieler',
      ]);
      expect(builtins.fallback.name, noAction);
      expect(builtins.byName(noAction), isA<ActionKeineAktion>());
    });

    test('on_system_error is the engine\'s, never offered', () {
      expect(builtins.onError.name, 'on_system_error');
      expect(builtins.byName('on_system_error'), isNull);
    });
  });

  group('actions', () {
    final context = BuiltinContext(machine: machine, state: start);

    test('keine_aktion: nothing was executed, answer in the role', () {
      expect(
        const ActionKeineAktion().run(context),
        'Es wurde keine Aktion ausgeführt. Antworte dem Spieler im Rahmen '
        'deiner Rolle und gib ihm Kontext aus dem AKTUELLEN RAUM.',
      );
    });

    test('helfe_dem_spieler: a subtle hint on what is possible right now', () {
      final note = const ActionHelfeDemSpieler().run(context);
      expect(note, startsWith('Der Spieler bittet um Hilfe.'));
      expect(note, endsWith('- Den Schlüssel nehmen\n- In den Garten'));
    });

    test('on_system_error: names what the player was about to do', () {
      final note = const ActionOnSystemError().run(
        BuiltinContext(
          machine: machine,
          state: start,
          attempted: miniGame().actions.first,
        ),
      );
      expect(
        note,
        startsWith('Der Spieler wollte etwas tun (Den Schlüssel nehmen)'),
      );
      expect(note, contains('noch einmal versuchen'));
    });
  });

  group('running the chosen function', () {
    final executor = FunctionExecutor(machine, builtins);

    test('a built-in one changes nothing and gives its note', () {
      final outcome = executor.run(start, 'helfe_dem_spieler');
      expect(outcome.function, 'helfe_dem_spieler');
      expect(outcome.state, same(start));
      expect(outcome.events, isEmpty);
      expect(outcome.firedAction, isNull);
      expect(outcome.note, startsWith('Der Spieler bittet um Hilfe.'));
    });

    test('a game action fires and says what happened', () {
      final outcome = executor.run(start, 'nimm_schluessel');
      expect(outcome.firedAction, 'nimm_schluessel');
      expect(outcome.state.variables['has_key'], isTrue);
      expect(
        outcome.note,
        'Ausgeführte Aktion: nimm_schluessel\n'
        'Was der Spieler damit tut: Den Schlüssel nehmen\n'
        'Folge im Spiel: Du hast ihn.',
      );
    });

    test('a game action whose script fails becomes on_system_error', () {
      final broken = StateMachine(brokenGame());
      final state = GameState.initial(brokenGame());
      final outcome = FunctionExecutor(broken, builtins).run(state, 'zaubere');

      expect(outcome.function, 'on_system_error');
      expect(outcome.firedAction, isNull);
      expect(outcome.state, same(state));
      expect(outcome.note, contains('(Einen Zauber wirken)'));
    });
  });
}
