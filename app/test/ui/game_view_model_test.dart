import 'dart:async';
import 'dart:io';

import 'package:arcane_player/audio/arcane_audio.dart';
import 'package:arcane_player/content/arcane_content.dart';
import 'package:arcane_player/data/repositories/game_catalog_repository.dart';
import 'package:arcane_player/data/repositories/game_session_repository.dart';
import 'package:arcane_player/data/repositories/settings_repository.dart';
import 'package:arcane_player/data/services/file_store_service.dart';
import 'package:arcane_player/data/services/prefs_service.dart';
import 'package:arcane_player/llm/llm_trace.dart';
import 'package:arcane_player/ui/game/game_view_model.dart';
import 'package:arcane_player/utils/command.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../support/fakes.dart';

/// Waits for a command kicked off in a view model constructor to finish.
Future<void> settle(Command<Object?> command) async {
  if (!command.running && command.result != null) return;
  final done = Completer<void>();
  void listener() {
    if (!command.running && command.result != null && !done.isCompleted) {
      done.complete();
    }
  }

  command.addListener(listener);
  await done.future;
  command.removeListener(listener);
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late FakeLlm llm;
  late FakeJukebox jukebox;
  late FakeSpeech speech;
  late AudioCoordinator audio;
  late GameCatalogRepository catalog;
  late SettingsRepository settings;
  late Future<Directory> storeDir;

  GameSessionRepository newSessions() => GameSessionRepository(
    catalog: catalog,
    llm: llm,
    store: FileStoreService(directory: storeDir),
    prompts: testPrompts(),
  );

  late GameSessionRepository sessions;

  setUp(() async {
    SharedPreferences.setMockInitialValues({});
    llm = FakeLlm();
    jukebox = FakeJukebox();
    speech = FakeSpeech();
    audio = AudioCoordinator(jukebox: jukebox, speech: speech);
    final resolver = fakeResolver();
    catalog = GameCatalogRepository(
      resolver: resolver,
      loader: GamePackLoader(resolver),
    );
    settings = SettingsRepository(await PrefsService.load());
    storeDir = tempDir();
    sessions = newSessions();
  });

  final trace = LlmTrace();

  GameViewModel buildVm([GameSessionRepository? repository]) => GameViewModel(
    sessions: repository ?? sessions,
    settings: settings,
    audio: audio,
    trace: trace,
    gameId: 'mini',
  );

  test('opens the game, narrates the opening and plays its ambience', () async {
    llm.narrate('Willkommen in der Halle.');
    final vm = buildVm();
    await settle(vm.load);

    expect(vm.load.completed, isTrue);
    expect(vm.title, 'Mini');
    expect(vm.lines.single.text, 'Willkommen in der Halle.');
    expect(vm.lines.single.playerInput, isNull);
    expect(speech.spoken, ['Willkommen in der Halle.']);
    expect(jukebox.ambience, isNotNull, reason: 'the room has ambience');
    vm.dispose();
  });

  test('a turn appends the exchange, drives audio and saves', () async {
    llm
      ..narrate('Hallo.')
      ..decide('nimm_schluessel')
      ..narrate('Du hast den Schlüssel.');
    final vm = buildVm();
    await settle(vm.load);

    await vm.send.execute('nimm den schlüssel');

    expect(vm.lines, hasLength(2));
    expect(vm.lines.last.playerInput, 'nimm den schlüssel');
    expect(vm.lines.last.text, 'Du hast den Schlüssel.');
    expect(jukebox.effectsPlayed, 1, reason: 'the trigger has a sound effect');
    vm.dispose();

    // Saved: a fresh repository resumes silently into the same state.
    speech.spoken.clear();
    final resumed = buildVm(newSessions());
    await settle(resumed.load);
    expect(resumed.lines.map((l) => l.text), [
      'Hallo.',
      'Du hast den Schlüssel.',
    ]);
    expect(speech.spoken, isEmpty, reason: 'nothing is read again');
    expect(
      sessions.session!.state.variables['has_key'],
      isTrue,
      reason: 'the state is restored, not only the conversation',
    );
    expect(sessions.session!.state.turn, 1);
    expect(
      llm.requests.where((r) => r.stage.contains('Begrüßung')),
      hasLength(1),
      reason: 'no new opening',
    );
    resumed.dispose();
  });

  test('restart discards progress and starts afresh', () async {
    llm
      ..narrate('Hallo.')
      ..decide('nimm_schluessel')
      ..narrate('Genommen.')
      ..narrate('Neu hier.');
    final vm = buildVm();
    await settle(vm.load);
    await vm.send.execute('nimm ihn');
    trace.start(LlmTraceCall('Stufe 1', settings: '', messages: const []));
    expect(trace.calls, isNotEmpty);

    await vm.restart.execute();

    expect(vm.restart.completed, isTrue);
    expect(vm.lines.map((l) => l.text), ['Neu hier.']);
    expect(
      sessions.session!.state.variables['has_key'],
      isFalse,
      reason: 'the game state is fresh',
    );
    expect(trace.calls, isEmpty, reason: 'the debug trace is cleared too');
    vm.dispose();

    final resumed = buildVm(newSessions());
    await settle(resumed.load);
    expect(resumed.lines.map((l) => l.text), ['Neu hier.']);
    resumed.dispose();
  });

  test('the personality can be switched off and stays off', () async {
    final vm = buildVm();
    await settle(vm.load);
    String narrator() =>
        llm.requests.lastWhere((r) => r.stage.startsWith('Stufe 2')).system;
    expect(narrator(), startsWith('Knapp.'));

    await vm.setPersonality(false);
    await vm.send.execute('schau dich um');

    expect(vm.personality, isFalse);
    expect(
      narrator(),
      startsWith('Du bist der Begleiter des Spielers'),
      reason: 'stage 2 speaks neutrally',
    );
    expect(
      SettingsRepository(await PrefsService.load()).personality,
      isFalse,
      reason: 'persisted',
    );
    vm.dispose();
  });

  test('empty input does nothing', () async {
    final vm = buildVm();
    await settle(vm.load);
    await vm.send.execute('   ');
    expect(vm.lines, hasLength(1));
    vm.dispose();
  });
}
