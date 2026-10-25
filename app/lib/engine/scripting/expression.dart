import 'script_runtime.dart';

/// Expression subset shared by Lua conditions/scripts and Jinja tags:
///
///   literals:   123, 1.5, "text", 'text', true, false, nil, none
///   operators:  or, and, not, == ~= != < > <= >=, + -, ( )
///   statements: `name = expr` (separated by newlines or `;`)
///
/// Truthiness differs between the two languages, see [Truthiness].
enum Truthiness {
  /// Only `false` and `nil` are falsy.
  lua,

  /// Additionally `0` and `''` are falsy (Python semantics).
  jinja,
}

/// Whether [value] counts as true under [mode].
bool isTruthy(Object? value, Truthiness mode) {
  if (value == null || value == false) return false;
  if (mode == Truthiness.jinja && (value == 0 || value == '')) return false;
  return true;
}

/// Evaluates [source] against [variables]; unknown names are `nil`.
Object? evaluateExpression(
  String source,
  Map<String, Object?> variables, {
  Truthiness mode = Truthiness.lua,
}) {
  final parser = _Parser(_tokenize(source), variables, mode);
  final result = parser.expression();
  parser.expectEnd();
  return result;
}

/// Runs `name = expr` statements and returns the updated variables.
Map<String, Object?> executeStatements(
  String source,
  Map<String, Object?> variables,
) {
  final result = Map.of(variables);
  for (final raw in source.split(RegExp(r'[;\n]'))) {
    final statement = raw.trim();
    if (statement.isEmpty) continue;
    final match = _assignment.firstMatch(statement);
    if (match == null) {
      throw ScriptException('Unsupported statement: "$statement"');
    }
    result[match.group(1)!] = evaluateExpression(match.group(2)!, result);
  }
  return result;
}

final _assignment = RegExp(r'^([A-Za-z_]\w*)\s*=(?!=)\s*(.+)$');

enum _Kind { number, string, identifier, operator, open, close, end }

typedef _Token = ({_Kind kind, Object? value});

const _comparisons = {'==', '~=', '!=', '<', '>', '<=', '>='};

List<_Token> _tokenize(String source) {
  final tokens = <_Token>[];
  var i = 0;
  while (i < source.length) {
    final c = source[i];
    if (c.trim().isEmpty) {
      i++;
    } else if (_digit.hasMatch(c)) {
      final m = _numberLiteral.matchAsPrefix(source, i)!;
      tokens.add((kind: _Kind.number, value: num.parse(m[0]!)));
      i = m.end;
    } else if (c == '"' || c == "'") {
      final end = source.indexOf(c, i + 1);
      if (end < 0) throw ScriptException('Unterminated string in "$source"');
      tokens.add((kind: _Kind.string, value: source.substring(i + 1, end)));
      i = end + 1;
    } else if (_identStart.hasMatch(c)) {
      final m = _identifier.matchAsPrefix(source, i)!;
      tokens.add((kind: _Kind.identifier, value: m[0]));
      i = m.end;
    } else if (c == '(' || c == ')') {
      tokens.add((kind: c == '(' ? _Kind.open : _Kind.close, value: c));
      i++;
    } else {
      final two = source.length > i + 1 ? source.substring(i, i + 2) : '';
      final op = _comparisons.contains(two)
          ? two
          : '<>+-'.contains(c)
          ? c
          : throw ScriptException('Unexpected "$c" in "$source"');
      tokens.add((kind: _Kind.operator, value: op));
      i += op.length;
    }
  }
  return tokens..add((kind: _Kind.end, value: null));
}

final _digit = RegExp('[0-9]');
final _numberLiteral = RegExp(r'[0-9]+(\.[0-9]+)?');
final _identStart = RegExp('[A-Za-z_]');
final _identifier = RegExp(r'[A-Za-z_]\w*');

/// Recursive-descent parser that evaluates while parsing.
class _Parser {
  _Parser(this._tokens, this._variables, this._mode);

  final List<_Token> _tokens;
  final Map<String, Object?> _variables;
  final Truthiness _mode;
  var _pos = 0;

  _Token get _peek => _tokens[_pos];
  _Token _next() => _tokens[_pos++];

  bool _atKeyword(String word) =>
      _peek.kind == _Kind.identifier && _peek.value == word;

  bool _atOperator(Set<String> ops) =>
      _peek.kind == _Kind.operator && ops.contains(_peek.value);

  void expectEnd() {
    if (_peek.kind != _Kind.end) {
      throw ScriptException('Unexpected "${_peek.value}"');
    }
  }

  Object? expression() => _or();

  Object? _or() {
    var left = _and();
    while (_atKeyword('or')) {
      _next();
      final right = _and();
      left = isTruthy(left, _mode) ? left : right;
    }
    return left;
  }

  Object? _and() {
    var left = _not();
    while (_atKeyword('and')) {
      _next();
      final right = _not();
      left = isTruthy(left, _mode) ? right : left;
    }
    return left;
  }

  Object? _not() {
    if (!_atKeyword('not')) return _comparison();
    _next();
    return !isTruthy(_not(), _mode);
  }

  Object? _comparison() {
    final left = _additive();
    if (!_atOperator(_comparisons)) return left;
    final op = _next().value! as String;
    final right = _additive();
    if (op == '==') return left == right;
    if (op == '~=' || op == '!=') return left != right;
    if (left is! num || right is! num) {
      throw ScriptException('Cannot compare $left $op $right');
    }
    return switch (op) {
      '<' => left < right,
      '>' => left > right,
      '<=' => left <= right,
      _ => left >= right,
    };
  }

  Object? _additive() {
    var left = _unary();
    while (_atOperator(const {'+', '-'})) {
      final op = _next().value;
      final right = _unary();
      if (left is! num || right is! num) {
        throw ScriptException('Arithmetic on non-numbers: $left $op $right');
      }
      left = op == '+' ? left + right : left - right;
    }
    return left;
  }

  Object? _unary() {
    if (!_atOperator(const {'-'})) return _primary();
    _next();
    final value = _unary();
    if (value is! num) throw ScriptException('Cannot negate $value');
    return -value;
  }

  Object? _primary() {
    final token = _next();
    switch (token.kind) {
      case _Kind.number || _Kind.string:
        return token.value;
      case _Kind.open:
        final value = expression();
        if (_next().kind != _Kind.close) {
          throw const ScriptException('Missing ")"');
        }
        return value;
      case _Kind.identifier:
        return switch (token.value) {
          'true' || 'True' => true,
          'false' || 'False' => false,
          'nil' || 'none' || 'None' => null,
          final name => _variables[name],
        };
      case _Kind.close || _Kind.operator || _Kind.end:
        throw ScriptException('Unexpected "${token.value}"');
    }
  }
}
