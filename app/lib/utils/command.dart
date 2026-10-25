import 'package:flutter/foundation.dart';

import 'result.dart';

/// Wraps an asynchronous action and exposes its running/completed/error state
/// as a [Listenable], so the UI can render it with a [ListenableBuilder].
/// Straight from the Flutter architecture guide's Command pattern.
abstract class Command<T> extends ChangeNotifier {
  bool _running = false;

  /// Whether the action is in progress.
  bool get running => _running;

  Result<T>? _result;

  /// Whether the last run failed.
  bool get error => _result is Error;

  /// Whether the last run succeeded.
  bool get completed => _result is Ok;

  /// The most recent result (`null` while running or after [clearResult]).
  Result<T>? get result => _result;

  /// Clears the last result.
  void clearResult() {
    _result = null;
    notifyListeners();
  }

  Future<void> _execute(Future<Result<T>> Function() action) async {
    if (_running) return;
    _running = true;
    _result = null;
    notifyListeners();
    try {
      _result = await action();
    } finally {
      _running = false;
      notifyListeners();
    }
  }
}

/// A [Command] with no arguments.
final class Command0<T> extends Command<T> {
  Command0(this._action);

  final Future<Result<T>> Function() _action;

  /// Runs the action.
  Future<void> execute() => _execute(_action);
}

/// A [Command] with one argument.
final class Command1<T, A> extends Command<T> {
  Command1(this._action);

  final Future<Result<T>> Function(A) _action;

  /// Runs the action with [argument].
  Future<void> execute(A argument) => _execute(() => _action(argument));
}
