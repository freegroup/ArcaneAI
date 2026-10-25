/// Evaluates the small scripts a game definition contains: action
/// conditions, inventory updates and text templates.
///
/// The Python engine uses Lua and Jinja2; [MiniScriptRuntime] implements the
/// subset the games actually use. A full Lua VM could be plugged in here
/// without touching the rest of the engine.
abstract interface class ScriptRuntime {
  /// Whether [expression] holds for [variables] (an empty expression holds).
  bool evaluateCondition(String expression, Map<String, Object?> variables);

  /// Runs the statements in [script]; returns the updated variables.
  Map<String, Object?> execute(String script, Map<String, Object?> variables);

  /// Renders [template] (Jinja `{% if %}` / `{{ }}`) with [variables].
  String render(String template, Map<String, Object?> variables);
}

/// A script could not be evaluated (syntax outside the supported subset,
/// type mismatch, …). Callers treat it like a failed Lua call in Python:
/// the condition is false, the action does not fire, the template stays raw.
final class ScriptException implements Exception {
  const ScriptException(this.message);

  /// What went wrong.
  final String message;

  @override
  String toString() => 'ScriptException: $message';
}
