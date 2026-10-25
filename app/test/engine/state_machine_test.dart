import 'package:arcane_player/engine/arcane_engine.dart';
import 'package:flutter_test/flutter_test.dart';

import 'support/fakes.dart';

void main() {
  final game = miniGame();
  final machine = StateMachine(game);
  final start = GameState.initial(game);

  List<String> available(GameState s) => [
    for (final a in machine.availableActions(s)) a.name,
  ];

  test('conditions decide what is available', () {
    expect(available(start), ['nimm_schluessel', 'gehe_garten']);
    final withKey = start.copyWith(
      variables: {...start.variables, 'has_key': true},
    );
    expect(available(withKey), ['gehe_garten', 'oeffne_tuer']);
  });

  test(
    'a trigger runs its scripts, plays its effect and stays in the room',
    () {
      final outcome = machine.apply(start, 'nimm_schluessel') as ActionApplied;

      expect(outcome.state.roomId, 'hall');
      expect(outcome.state.variables, containsPair('has_key', true));
      expect(outcome.state.variables, containsPair('coins', 1));
      expect(
        start.variables['has_key'],
        isFalse,
        reason: 'states are immutable',
      );

      expect(outcome.events, hasLength(2));
      final effect = outcome.events[0] as EffectCue;
      expect(effect.playback.sound, const SoundRef('pickup.wav'));
      expect(effect.playback.duration, const Duration(seconds: 2));
      final inventory = outcome.events[1] as InventoryChanged;
      expect(inventory.changedKeys, {'has_key', 'coins'});
    },
  );

  test('a transition enters the room and replaces the ambience', () {
    final outcome = machine.apply(start, 'gehe_garten') as ActionApplied;
    expect(outcome.state.roomId, 'garden');
    expect(outcome.events, [
      isA<RoomEntered>().having((e) => e.roomId, 'roomId', 'garden'),
      isA<AmbienceCue>().having((e) => e.playback, 'playback', isNull),
    ]);
  });

  test('reaching an end room ends the game', () {
    final withKey = start.copyWith(
      variables: {...start.variables, 'has_key': true},
    );
    final outcome = machine.apply(withKey, 'oeffne_tuer') as ActionApplied;
    expect(outcome.events.last, isA<GameOver>());
  });

  test('unavailable actions are rejected', () {
    expect(machine.apply(start, 'oeffne_tuer'), isA<ActionRejected>());
    expect(machine.apply(start, 'fliege_zum_mond'), isA<ActionRejected>());
  });

  test('invalid enum values are reverted', () {
    final garden = start.copyWith(roomId: 'garden');
    final warnings = <String>[];
    final outcome =
        machine.apply(garden, 'werde_boese', warnings: warnings)
            as ActionApplied;
    expect(outcome.state.variables['companion_mood'], 'neutral');
    expect(warnings.single, contains('wuetend'));
  });

  test('broken templates stay raw and are reported', () {
    final warnings = <String>[];
    expect(
      machine.render('{% if x %}', start, warnings: warnings),
      '{% if x %}',
    );
    expect(warnings, hasLength(1));
  });

  test('room descriptions render against the inventory', () {
    expect(
      machine.describeRoom(start),
      'Eine Halle. Ein Schlüssel liegt hier.',
    );
  });
}
