import 'expression.dart';
import 'script_runtime.dart';
import 'template.dart';

/// [ScriptRuntime] for the Lua/Jinja subset the games use; pure Dart.
final class MiniScriptRuntime implements ScriptRuntime {
  const MiniScriptRuntime();

  @override
  bool evaluateCondition(String expression, Map<String, Object?> variables) {
    if (expression.trim().isEmpty) return true;
    return isTruthy(evaluateExpression(expression, variables), Truthiness.lua);
  }

  @override
  Map<String, Object?> execute(String script, Map<String, Object?> variables) =>
      executeStatements(script, variables);

  @override
  String render(String template, Map<String, Object?> variables) =>
      renderTemplate(template, variables);
}
