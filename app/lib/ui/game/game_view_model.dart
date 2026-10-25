import 'dart:async';

import 'package:arcane_player/audio/arcane_audio.dart';
import 'package:arcane_player/engine/arcane_engine.dart';
import 'package:flutter/foundation.dart';

import '../../data/repositories/game_session_repository.dart';
import '../../data/repositories/settings_repository.dart';
import '../../llm/llm_trace.dart';
import '../../utils/command.dart';
import '../../utils/result.dart';

/// One entry of the game log as shown to the player.
@immutable
final class GameLine {
  const GameLine({required this.text, this.playerInput});

  /// What the player was told.
  final String text;

  /// What the player said (`null` for the opening).
  final String? playerInput;
}

/// View model of the game screen: opens or resumes the game, runs turns,
/// drives audio, keeps the log and saves after every turn.
final class GameViewModel extends ChangeNotifier {
  GameViewModel({
    required GameSessionRepository sessions,
    required SettingsRepository settings,
    required AudioCoordinator audio,
    required LlmTrace trace,
    required this.gameId,
  }) : _sessions = sessions,
       _settings = settings,
       _audio = audio,
       _trace = trace {
    load = Command0(() => _open(restart: false))..execute();
    restart = Command0(() => _open(restart: true));
    send = Command1(_send);
    _settings.addListener(_followSettings);
    _listeningSubscription = _audio.onListeningChanged.listen((_) {
      notifyListeners();
    });
  }

  /// The game this screen plays.
  final String gameId;

  final GameSessionRepository _sessions;
  final SettingsRepository _settings;
  final AudioCoordinator _audio;
  final LlmTrace _trace;
  late final StreamSubscription<bool> _listeningSubscription;

  /// Opens the game, resuming saved progress.
  late final Command0<void> load;

  /// Starts the game afresh.
  late final Command0<void> restart;

  /// Runs the player's input as a turn.
  late final Command1<void, String> send;

  final List<GameLine> _lines = [];
  String _partialInput = '';

  /// The game log, oldest first.
  List<GameLine> get lines => List.unmodifiable(_lines);

  /// Display title of the game.
  String get title => _sessions.loaded?.title ?? '';

  /// The game's help text (simple HTML), or `''`.
  String get helpText => _sessions.loaded?.definition.helpText ?? '';

  /// Whether the game reached its end.
  bool get isOver => _sessions.session?.isOver ?? false;

  /// Whether the microphone listens.
  bool get listening => _audio.isListening;

  /// Whether speech input exists on this device.
  bool get canListen => _audio.hasMicrophone;

  /// Live transcription while listening.
  String get partialInput => _partialInput;

  /// Whether answers are reworded in the game's personality.
  bool get personality => _settings.personality;

  Future<Result<void>> _open({required bool restart}) async {
    // A fresh start also clears the debug trace of recorded model calls.
    if (restart) _trace.clear();
    final opened = restart
        ? await _sessions.restart(gameId)
        : await _sessions.open(gameId);
    final GameSession session;
    switch (opened) {
      case Ok(:final value):
        session = value..personality = personality;
      case Error(:final error):
        return Result.error(error);
    }

    final loaded = _sessions.loaded!;
    _audio.library = SoundLibrary(
      resolver: loaded.resolver,
      sounds: loaded.sounds,
    );

    _lines
      ..clear()
      ..addAll([
        for (final exchange in session.history)
          GameLine(
            text: exchange.narration,
            playerInput: exchange.isWelcome ? null : exchange.playerInput,
          ),
      ]);
    notifyListeners();

    if (session.hasStarted) {
      // Resumed: ambience on, nothing read again.
      await _audio.resumeAmbience(session.currentAmbience);
      return const Result.ok(null);
    }
    try {
      final opening = await session.start();
      _record(opening);
      await _audio.handleTurn(opening.events, narration: opening.narration);
      await _sessions.save();
      return const Result.ok(null);
    } on Object catch (e) {
      return Result.error(e);
    }
  }

  Future<Result<void>> _send(String input) async {
    final text = input.trim();
    final session = _sessions.session;
    if (text.isEmpty || session == null || session.isBusy || isOver) {
      return const Result.ok(null);
    }
    _partialInput = '';
    try {
      final turn = await session.send(text);
      _record(turn);
      await _audio.handleTurn(turn.events, narration: turn.narration);
      await _sessions.save();
      return const Result.ok(null);
    } on Object catch (e) {
      return Result.error(e);
    }
  }

  /// Starts or stops listening; a final transcription is sent as a turn.
  /// Returns `false` if speech input is not available.
  Future<bool> toggleListening() async {
    if (listening) {
      await _audio.stopListening();
      return true;
    }
    return _audio.startListening((result) {
      _partialInput = result.text;
      notifyListeners();
      if (result.isFinal) unawaited(send.execute(result.text));
    });
  }

  /// Switches the personality on or off (persisted); applies from the next
  /// turn.
  Future<void> setPersonality(bool value) => _settings.setPersonality(value);

  void _record(TurnResult turn) {
    _lines.add(
      GameLine(
        text: turn.narration,
        playerInput: turn.isWelcome ? null : turn.input,
      ),
    );
    notifyListeners();
  }

  void _followSettings() {
    _sessions.session?.personality = personality;
    notifyListeners();
  }

  @override
  void dispose() {
    _settings.removeListener(_followSettings);
    unawaited(_listeningSubscription.cancel());
    load.dispose();
    restart.dispose();
    send.dispose();
    super.dispose();
  }
}
