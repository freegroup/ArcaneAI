import 'dart:convert';

import 'package:arcane_player/engine/arcane_engine.dart';
import 'package:flutter_test/flutter_test.dart';

import 'support/fakes.dart';

void main() {
  late FakeLlm llm;
  late GameSession session;

  setUp(() {
    llm = FakeLlm(judgement: 'neutral');
    session = GameSession(
      definition: miniGame(),
      llm: llm,
      prompts: testPrompts(),
    );
  });

  tearDown(() => session.close());

  String system(Request request) => request.messages.first.content;
  String last(Request request) => request.messages.last.content;

  group('start', () {
    test('only stage 2 speaks the opening; nothing is decided', () async {
      llm.narrate('Willkommen.');
      final opening = await session.start();

      expect(opening.isWelcome, isTrue);
      expect(opening.narration, 'Willkommen.');
      expect(llm.of('Stufe 1'), isEmpty);
      final request = llm.of('Stufe 2').single;
      expect(system(request), startsWith('Nett.'));
      expect(system(request), contains('SPIELZIEL:\nFinde den Schlüssel'));
      expect(last(request), 'Das Spiel beginnt!');
      expect(opening.events.single, isA<AmbienceCue>());
      expect(session.state.turn, 0);
    });

    test('cannot start twice', () async {
      await session.start();
      expect(session.start, throwsStateError);
    });
  });

  group('stage 1', () {
    test('gets the rules, the goal and the room — no personality', () async {
      await session.send('hallo');
      final request = llm.of('Stufe 1').single;
      final prompt = system(request);
      expect(prompt, startsWith('Du bist ein Schritt in einem Textadventure'));
      expect(
        prompt,
        isNot(contains('Nett.')),
        reason: "the voice is stage 2's",
      );
      expect(prompt, contains('SPIELZIEL:\nFinde den Schlüssel'));
      expect(prompt, contains('AKTUELLER RAUM'));
      expect(prompt, contains('Eine Halle. Ein Schlüssel liegt hier.'));
      expect(prompt, contains('SO ENTSCHEIDEST DU:'));
      expect(prompt, endsWith('Erfinde keine.'));
      expect(
        prompt,
        isNot(contains('EINGEBAUTE FUNKTIONEN')),
        reason: 'stage 1 sees one flat list of functions, handed as tools',
      );
      expect(
        prompt,
        isNot(contains('SO ANTWORTEST DU')),
        reason: "stage 2's rules",
      );
      expect(request.maxOutputTokens, testPrompts().decision.maxOutputTokens);
    });

    test(
      'is offered the game actions possible right now + the built-in ones',
      () async {
        await session.send('hallo');
        final functions = llm.of('Stufe 1').single.functions;
        expect(
          functions.map((f) => f.name),
          ['nimm_schluessel', 'gehe_garten', noAction, 'helfe_dem_spieler'],
          reason: 'oeffne_tuer needs the key; on_system_error is never offered',
        );
        expect(functions.first.description, 'Den Schlüssel nehmen');
      },
    );

    test(
      'gets the dialogue as in Python: input, answer, …, new input',
      () async {
        llm
          ..narrate('Willkommen.')
          ..enqueue('nimm_schluessel')
          ..narrate('Du hast ihn.');
        await session.start();
        await session.send('nimm ihn');
        await session.send('und jetzt');

        final messages = llm.of('Stufe 1').last.messages;
        expect(messages.map((m) => m.role), [
          LlmRole.system,
          LlmRole.user,
          LlmRole.assistant,
          LlmRole.user,
          LlmRole.assistant,
          LlmRole.user,
        ]);
        expect(messages.map((m) => m.content).skip(1), [
          'Das Spiel beginnt!',
          'Willkommen.',
          'nimm ihn',
          'Du hast ihn.',
          'und jetzt',
        ]);
      },
    );

    test('sees only as much dialogue as fits its context', () async {
      llm.narrate('x' * testPrompts().decision.historyChars);
      await session.send('eins');
      await session.send('zwei');

      final contents = llm.of('Stufe 1').last.messages.map((m) => m.content);
      expect(contents.skip(1), [
        'zwei',
      ], reason: 'the long exchange no longer fits');
    });

    test('a called action fires', () async {
      llm.enqueue('nimm_schluessel');
      final turn = await session.send('nimm den schlüssel');

      expect(turn.firedAction, 'nimm_schluessel');
      expect(session.state.variables['has_key'], isTrue);
      expect(session.state.variables['coins'], 1);
      expect(turn.events.whereType<EffectCue>(), hasLength(1));
      expect(session.state.turn, 1);
    });

    test('keine_aktion leaves the world untouched', () async {
      llm.enqueue(noAction);
      final turn = await session.send('flieg');

      expect(turn.firedAction, isNull);
      expect(turn.calledFunction, noAction);
      expect(session.state.variables['has_key'], isFalse);
    });

    test('collapses blank lines the model puts between sentences', () async {
      llm
        ..enqueue(noAction)
        ..narrate('Erste Zeile.\n\nZweite Zeile.\n \nDritte.');
      final turn = await session.send('etwas');

      expect(turn.narration, 'Erste Zeile.\nZweite Zeile.\nDritte.');
    });

    test('a function that was not offered is discarded and asked again, '
        'pointing to keine_aktion', () async {
      llm
        ..enqueue('oeffne_tuer') // needs the key
        ..enqueue(noAction);
      final turn = await session.send('tür auf');

      expect(llm.of('Stufe 1'), hasLength(2));
      expect(turn.firedAction, isNull);
      expect(session.state.roomId, 'hall');
      final retry = last(llm.of('Stufe 1').last);
      expect(retry, startsWith('tür auf\n\n'));
      expect(retry, contains("Die Funktion 'oeffne_tuer' gibt es hier nicht."));
      expect(retry, contains('Passt keine, dann rufe keine_aktion auf.'));
    });

    test('an answer without a function call is asked again', () async {
      llm
        ..enqueue(null, 'Du gehst in den Garten.')
        ..enqueue('gehe_garten');
      final turn = await session.send('garten');

      expect(llm.of('Stufe 1'), hasLength(2));
      expect(turn.firedAction, 'gehe_garten');
      expect(session.state.roomId, 'garden');
    });

    test('if every answer is discarded, nothing happens', () async {
      llm
        ..enqueue('erfunden')
        ..enqueue('erfunden');
      final turn = await session.send('flieg');

      expect(llm.of('Stufe 1'), hasLength(testPrompts().decision.maxAttempts));
      expect(turn.firedAction, isNull);
      expect(session.state.roomId, 'hall');
      expect(
        last(llm.of('Stufe 2').single),
        contains('keine Aktion ausgeführt'),
      );
    });

    test('reaching the end finishes the game', () async {
      llm
        ..enqueue('nimm_schluessel')
        ..enqueue('oeffne_tuer');
      await session.send('schlüssel');
      final last = await session.send('tür');
      expect(last.isGameOver, isTrue);
      expect(session.isOver, isTrue);
      expect(() => session.send('weiter'), throwsStateError);
    });

    test('turns are exclusive', () async {
      final first = session.send('a');
      expect(() => session.send('b'), throwsStateError);
      await first;
    });
  });

  group('stage 2', () {
    test('tells what happened, from the result the game decided', () async {
      llm.enqueue('nimm_schluessel');
      final turn = await session.send('nimm den schlüssel');

      final request = llm.of('Stufe 2').single;
      expect(system(request), startsWith('Nett.'));
      expect(system(request), contains('SO ANTWORTEST DU:'));
      expect(
        system(request),
        isNot(contains('Ein Schlüssel liegt hier.')),
        reason: 'the room as it is after the action',
      );
      expect(
        last(request),
        'nimm den schlüssel\n\n'
        '(SPIEL:\n'
        'Ausgeführte Aktion: nimm_schluessel\n'
        'Was der Spieler damit tut: Den Schlüssel nehmen\n'
        'Folge im Spiel: Du hast ihn.)',
      );
      expect(request.functions, isEmpty);
      expect(turn.narration, 'Erzählt: nimm den schlüssel');
    });

    test(
      'helfe_dem_spieler changes nothing and asks for a subtle hint',
      () async {
        llm.enqueue('helfe_dem_spieler');
        final turn = await session.send('was kann ich tun?');

        expect(turn.firedAction, isNull);
        expect(turn.calledFunction, 'helfe_dem_spieler');
        expect(session.state.variables['has_key'], isFalse);
        final message = last(llm.of('Stufe 2').single);
        expect(
          message,
          startsWith(
            'was kann ich tun?\n\n(SPIEL:\nDer Spieler bittet um Hilfe.',
          ),
        );
        expect(message, contains('- Den Schlüssel nehmen\n- In den Garten'));

        await session.send('danke');
        expect(
          llm.of('Stufe 1').last.messages[2].functionCall,
          'helfe_dem_spieler',
          reason: 'stage 1 sees which function it chose',
        );
      },
    );

    test('after a transition it gets the new room', () async {
      llm.enqueue('gehe_garten');
      await session.send('garten');

      final request = llm.of('Stufe 2').single;
      expect(system(request), contains('Ein Garten.'));
      expect(
        last(request),
        endsWith('Der Spieler ist jetzt im AKTUELLEN RAUM.)'),
      );
    });

    test('no action is reported as such', () async {
      await session.send('flieg');
      expect(
        last(llm.of('Stufe 2').single),
        'flieg\n\n(SPIEL:\nEs wurde keine Aktion ausgeführt. Antworte dem '
        'Spieler im Rahmen deiner Rolle und gib ihm Kontext aus dem '
        'AKTUELLEN RAUM.)',
      );
    });

    test('gets the earlier exchanges as conversation', () async {
      llm
        ..narrate('Willkommen.')
        ..enqueue('nimm_schluessel')
        ..narrate('Genommen.');
      await session.start();
      await session.send('nimm ihn');
      await session.send('weiter');

      final messages = llm.of('Stufe 2').last.messages;
      expect(messages.map((m) => m.content).skip(1), [
        'Das Spiel beginnt!',
        'Willkommen.',
        'nimm ihn',
        'Genommen.',
        'weiter\n\n(SPIEL:\nEs wurde keine Aktion ausgeführt. Antworte dem '
            'Spieler im Rahmen deiner Rolle und gib ihm Kontext aus dem '
            'AKTUELLEN RAUM.)',
      ]);
    });

    test('uses the mood after the action', () async {
      llm.judgement = 'grob';
      await session.send('du idiot');
      await session.send('schau');
      expect(system(llm.of('Stufe 2').last), startsWith('Grob.'));
    });

    test('can run on a model of its own', () async {
      final voice = FakeLlm();
      final own = GameSession(
        definition: miniGame(),
        llm: llm,
        prompts: testPrompts(),
        narrationLlm: voice,
      );
      await own.send('schau');

      expect(voice.of('Stufe 2'), hasLength(1));
      expect(llm.of('Stufe 2'), isEmpty);
      await own.close();
    });

    test(
      'without personality it speaks neutrally, also between turns',
      () async {
        session.personality = false;
        await session.send('schau');

        final prompt = system(llm.of('Stufe 2').single);
        expect(prompt, startsWith('Du bist der Begleiter des Spielers'));
        expect(prompt, isNot(contains('Nett.')));
      },
    );

    test('an empty narration gets a fallback', () async {
      llm.narrate('');
      final turn = await session.send('schau');
      expect(turn.narration, GameController.fallbackAnswer);
    });
  });

  group('companion', () {
    test(
      'mood shifts at most one step and applies before the next turn',
      () async {
        final moods = <MoodChanged>[];
        session.sideEvents.listen((e) {
          if (e is MoodChanged) moods.add(e);
        });
        llm.judgement = 'grob';
        await session.send('du idiot');
        await session.send('schau dich um');
        expect(moods.first.to, 'grob');
        expect(session.state.variables['companion_mood'], 'grob');
        final mood = llm.of('Begleiter').first;
        expect(mood.maxOutputTokens, 8);
        expect(
          mood.messages.map((m) => m.role),
          [LlmRole.system, LlmRole.user, LlmRole.assistant, LlmRole.user],
          reason: 'the dialogue with both sides, then the question',
        );
        expect(mood.messages[1].content, 'du idiot');
        expect(
          mood.messages.last.content,
          startsWith('Wie geht der Spieler mit dem Begleiter um'),
        );
      },
    );

    test(
      'the state is settled for saving only after the mood changed',
      () async {
        llm.judgement = 'grob';
        await session.send('du idiot');
        await session.settled;
        expect(session.snapshot().state.variables['companion_mood'], 'grob');
      },
    );

    test('a mood answer outside the scale is ignored', () async {
      llm.judgement = 'euphorisch';
      await session.send('a');
      await session.send('b');
      expect(session.state.variables['companion_mood'], 'neutral');
    });
  });

  group('persistence', () {
    test('a snapshot survives JSON and continues where it left off', () async {
      llm
        ..narrate('Hallo.')
        ..enqueue('nimm_schluessel')
        ..narrate('Du nimmst ihn.');
      await session.start();
      await session.send('schlüssel');

      final json = jsonEncode(session.snapshot().toJson());
      final restored = GameSession.tryRestore(
        definition: miniGame(),
        llm: llm,
        prompts: testPrompts(),
        snapshot: SessionSnapshot.fromJson((jsonDecode(json) as Map).cast()),
      )!;

      expect(restored.state.variables, session.state.variables);
      expect(restored.state.turn, 1);
      expect(restored.history.map((e) => e.narration), [
        'Hallo.',
        'Du nimmst ihn.',
      ]);
      expect(restored.history.map((e) => e.action), [null, 'nimm_schluessel']);
      expect(restored.history.first.isWelcome, isTrue);
      expect(
        restored.currentAmbience.playback?.sound,
        const SoundRef('map/wind.wav'),
      );
      await restored.close();
    });

    test('a snapshot that no longer fits the game is not restored', () {
      final snapshot = session.snapshot();
      SessionSnapshot moved(String game, String room) => SessionSnapshot(
        gameId: game,
        state: snapshot.state.copyWith(roomId: room),
        history: const [],
        savedAt: DateTime.now(),
      );
      expect(
        GameSession.tryRestore(
          definition: miniGame(),
          llm: llm,
          prompts: testPrompts(),
          snapshot: moved('mini', 'gone'),
        ),
        isNull,
      );
      expect(
        GameSession.tryRestore(
          definition: miniGame(),
          llm: llm,
          prompts: testPrompts(),
          snapshot: moved('other', 'hall'),
        ),
        isNull,
      );
    });

    test('variables added to the game since the save get their default', () {
      final old = SessionSnapshot(
        gameId: 'mini',
        state: GameState(roomId: 'hall', variables: {'has_key': true}),
        history: const [],
        savedAt: DateTime.now(),
      );
      final restored = GameSession.tryRestore(
        definition: miniGame(),
        llm: llm,
        prompts: testPrompts(),
        snapshot: old,
      )!;
      expect(restored.state.variables, {
        'has_key': true,
        'coins': 0,
        'companion_mood': 'neutral',
      });
    });

    test('unknown snapshot versions are refused', () {
      expect(
        () => SessionSnapshot.fromJson({'version': 99}),
        throwsFormatException,
      );
      expect(
        () => SessionSnapshot.fromJson({'version': 1, 'game': 3}),
        throwsFormatException,
      );
    });
  });
}
