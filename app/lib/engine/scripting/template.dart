import 'expression.dart';
import 'script_runtime.dart';

/// Minimal Jinja renderer: nestable `{% if %}`/`{% elif %}`/`{% else %}`/
/// `{% endif %}` and `{{ expr }}` — the subset room descriptions and
/// personalities use. Whitespace-control dashes (`{%-`) are accepted.
String renderTemplate(String source, Map<String, Object?> variables) {
  final out = StringBuffer();
  final blocks = <_Block>[];
  bool active() => blocks.isEmpty || blocks.last.active;

  var last = 0;
  for (final match in _tag.allMatches(source)) {
    if (active()) out.write(source.substring(last, match.start));
    last = match.end;

    final expression = match[2];
    if (expression != null) {
      if (active()) {
        out.write(
          evaluateExpression(expression, variables, mode: Truthiness.jinja) ??
              '',
        );
      }
      continue;
    }

    final tag = match[1]!;
    final keyword = tag.split(_whitespace).first;
    final argument = tag.substring(keyword.length).trim();
    bool holds() => isTruthy(
      evaluateExpression(argument, variables, mode: Truthiness.jinja),
      Truthiness.jinja,
    );

    switch (keyword) {
      case 'if':
        final parentActive = active();
        final taken = parentActive && holds();
        blocks.add(_Block(parentActive, active: taken, matched: taken));
      case 'elif':
        final block = _top(blocks, tag);
        final taken = block.parentActive && !block.matched && holds();
        block
          ..active = taken
          ..matched = block.matched || taken;
      case 'else':
        final block = _top(blocks, tag);
        block
          ..active = block.parentActive && !block.matched
          ..matched = true;
      case 'endif':
        _top(blocks, tag);
        blocks.removeLast();
      default:
        throw ScriptException('Unsupported template tag {% $tag %}');
    }
  }
  if (blocks.isNotEmpty) throw const ScriptException('Missing {% endif %}');
  out.write(source.substring(last));
  return out.toString();
}

final _tag = RegExp(
  r'\{%-?\s*(.*?)\s*-?%\}|\{\{-?\s*(.*?)\s*-?\}\}',
  dotAll: true,
);
final _whitespace = RegExp(r'\s+');

class _Block {
  _Block(this.parentActive, {required this.active, required this.matched});

  final bool parentActive;
  bool active;
  bool matched;
}

_Block _top(List<_Block> blocks, String tag) => blocks.isNotEmpty
    ? blocks.last
    : throw ScriptException('{% $tag %} without {% if %}');
