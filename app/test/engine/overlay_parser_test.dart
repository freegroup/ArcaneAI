import 'package:arcane_player/engine/arcane_engine.dart';
import 'package:flutter_test/flutter_test.dart';

import 'support/fakes.dart';

void main() {
  group('real games from maps/', () {
    for (final id in ['TheTipsyQuest', 'DramaLlama']) {
      test('$id loads and every template, condition and script evaluates', () {
        final game = loadMap(id);
        final machine = StateMachine(game);
        final warnings = <String>[];

        expect(game.rooms[game.initialRoomId]?.kind, RoomKind.start);
        for (final room in game.rooms.values) {
          final state = GameState.initial(game).copyWith(roomId: room.id);
          machine.describeRoom(state, warnings: warnings);
          for (final action in machine.availableActions(
            state,
            warnings: warnings,
          )) {
            machine.apply(state, action.name, warnings: warnings);
          }
        }
        machine.render(
          game.personality,
          GameState.initial(game),
          warnings: warnings,
        );

        expect(warnings, isEmpty);
      });
    }

    test('the editor template has no START room and is not playable', () {
      expect(() => loadMap('template'), throwsFormatException);
    });

    test('TheTipsyQuest details survive parsing', () {
      final game = loadMap('TheTipsyQuest');
      expect(game.initialRoomId, 'WestOfHouse');
      expect(game.gameTarget, contains('goldene Eier'));
      expect(game.helpText, isNotEmpty);
      expect(game.variables['companion_mood']?.type, VariableType.enumeration);

      final walk = game
          .actionsFrom('WestOfHouse')
          .firstWhere((a) => a.name == 'gehe_zum_baum');
      expect(walk.isTransition, isTrue);
      expect(walk.effect?.sound, const SoundRef('laufen_waldweg.wav'));
      expect(game.room('WestOfHouse').ambience?.volume, 9);
    });
  });

  test('the editor\'s lenient types are tolerated', () {
    final game = OverlayParser.parse(
      id: 'lenient',
      model: {
        'states': {
          's1': {
            'name': 'A',
            'stateType': 'START',
            'userData': {
              'system_prompt': 'a',
              'ambient_sound': 'x.wav',
              'ambient_sound_volume': '40',
            },
            'trigger': [
              {
                'name': 't',
                'sound_effect': 'y.wav',
                'sound_effect_duration': '',
                'conditions': ['', 'x == 1'],
              },
            ],
          },
          's2': {'name': 'B', 'userData': <String, Object?>{}},
        },
        'connections': {
          'c1': {
            'name': 'go',
            'source': {'node': 's1'},
            'target': {'node': 's2'},
            'userData': {'sound_effect_volume': 250},
          },
          'c2': {
            'name': '',
            'source': {'node': 's1'},
            'target': {'node': 's2'},
          },
          'c3': {
            'name': 'dangling',
            'source': {'node': 's1'},
            'target': {'node': 'nope'},
          },
        },
      },
    );

    expect(game.room('A').ambience?.volume, 40);
    final trigger = game.actions.firstWhere((a) => a.name == 't');
    expect(trigger.effect?.duration, isNull);
    expect(trigger.conditions, ['x == 1']);
    expect(trigger.description, 't', reason: 'falls back to the name');
    expect(game.actions.map((a) => a.name), unorderedEquals(['go', 't']));
  });

  test('a game without START room is rejected', () {
    expect(
      () => OverlayParser.parse(
        id: 'x',
        model: {
          'states': {
            's': {'name': 'A'},
          },
        },
      ),
      throwsFormatException,
    );
  });

  test('the mini game used by the other tests is consistent', () {
    expect(miniGame().room('hall').kind, RoomKind.start);
  });
}
