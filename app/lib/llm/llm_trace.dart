import 'package:flutter/foundation.dart';

/// One message as it was handed to the model: its role and its exact text.
@immutable
final class LlmTraceMessage {
  const LlmTraceMessage(this.role, this.text);

  /// system, user or assistant.
  final String role;

  /// The exact text of the message.
  final String text;
}

/// One chat call: what went into the model and what came out.
final class LlmTraceCall {
  LlmTraceCall(
    this.stage, {
    required this.settings,
    required this.messages,
    this.functions = const [],
  }) : started = DateTime.now();

  /// Who called (e.g. "Stufe 1 · Funktionswahl · Versuch 1").
  final String stage;

  /// The sampling settings — configuration, not text for the model.
  final String settings;

  /// The messages, in order, exactly as handed to the model.
  final List<LlmTraceMessage> messages;

  /// The callable functions (`name: description`), handed over as tools.
  final List<String> functions;

  /// When the call started.
  final DateTime started;

  /// Everything the model generated; `null` while it runs.
  String? output;

  /// Why the call failed, if it did.
  String? error;

  /// How long the call took; `null` while it runs.
  Duration? duration;

  /// Characters handed to the model (messages and functions).
  int get inputChars =>
      messages.fold(0, (sum, message) => sum + message.text.length) +
      functions.fold(0, (sum, function) => sum + function.length);
}

/// Records every model call of this run, newest first, so it can be shown
/// while playing.
final class LlmTrace extends ChangeNotifier {
  /// Older calls are dropped beyond this many.
  static const maxCalls = 100;

  final List<LlmTraceCall> _calls = [];

  /// The calls, newest first.
  List<LlmTraceCall> get calls => List.unmodifiable(_calls);

  /// Records that a call starts.
  void start(LlmTraceCall call) {
    _calls.insert(0, call);
    if (_calls.length > maxCalls) _calls.removeLast();
    notifyListeners();
  }

  /// Drops every recorded call — used when the game is restarted.
  void clear() {
    if (_calls.isEmpty) return;
    _calls.clear();
    notifyListeners();
  }

  /// Records how [call] ended: the model's [output], or an [error].
  void finish(
    LlmTraceCall call,
    Duration duration, {
    String? output,
    String? error,
  }) {
    call
      ..duration = duration
      ..output = output
      ..error = error;
    notifyListeners();
  }
}
