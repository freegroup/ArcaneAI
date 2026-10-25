import 'package:arcane_player/engine/arcane_engine.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  const scripts = MiniScriptRuntime();
  final vars = <String, Object?>{'coins': 0, 'has_key': false, 'mood': 'grob'};

  group('conditions (Lua semantics)', () {
    test('as written in the games', () {
      expect(scripts.evaluateCondition('coins>0', vars), isFalse);
      expect(scripts.evaluateCondition('has_key==false', vars), isTrue);
      expect(scripts.evaluateCondition('has_key == true', vars), isFalse);
      expect(
        scripts.evaluateCondition('not has_key and coins < 1', vars),
        isTrue,
      );
      expect(
        scripts.evaluateCondition('(coins + 2) >= 2 or has_key', vars),
        isTrue,
      );
      expect(scripts.evaluateCondition('', vars), isTrue);
    });

    test('unknown variables are nil, and nil is not false', () {
      expect(scripts.evaluateCondition('unknown == false', vars), isFalse);
      expect(scripts.evaluateCondition('unknown == nil', vars), isTrue);
    });

    test('0 is truthy in Lua', () {
      expect(scripts.evaluateCondition('coins', vars), isTrue);
    });

    test('unsupported syntax raises ScriptException', () {
      expect(
        () => scripts.evaluateCondition('coins * 2 > 1', vars),
        throwsA(isA<ScriptException>()),
      );
      expect(
        () => scripts.evaluateCondition('coins < "a"', vars),
        throwsA(isA<ScriptException>()),
      );
    });
  });

  group('statements', () {
    test('assignments return an updated copy', () {
      final result = scripts.execute(
        'coins = coins +1\nhas_key=true; mood = "nett"',
        vars,
      );
      expect(result, {'coins': 1, 'has_key': true, 'mood': 'nett'});
      expect(vars['coins'], 0, reason: 'input must not be mutated');
    });

    test('control flow is not supported', () {
      expect(
        () => scripts.execute('if x then y = 1 end', vars),
        throwsA(isA<ScriptException>()),
      );
    });
  });

  group('templates (Jinja semantics)', () {
    test('nested if/else as used in room descriptions', () {
      const t =
          "A{% if has_key %}B{% else %}C{% if mood == 'grob' %}D{% endif%}{% endif %}E";
      expect(scripts.render(t, vars), 'ACDE');
      expect(scripts.render(t, {...vars, 'has_key': true}), 'ABE');
    });

    test('elif, whitespace control and output tags', () {
      const t =
          '{%- if coins <1 -%}arm{% elif coins > 5 %}reich{% else %}ok{% endif %}: {{ coins }}';
      expect(scripts.render(t, vars), 'arm: 0');
      expect(scripts.render(t, {...vars, 'coins': 9}), 'reich: 9');
      expect(scripts.render(t, {...vars, 'coins': 3}), 'ok: 3');
    });

    test('0 and empty string are falsy in Jinja', () {
      expect(
        scripts.render('{% if coins %}x{% else %}y{% endif %}', vars),
        'y',
      );
    });

    test('unbalanced blocks raise ScriptException', () {
      expect(
        () => scripts.render('{% if x %}open', vars),
        throwsA(isA<ScriptException>()),
      );
      expect(
        () => scripts.render('{% endif %}', vars),
        throwsA(isA<ScriptException>()),
      );
      expect(
        () => scripts.render('{% for x in y %}', vars),
        throwsA(isA<ScriptException>()),
      );
    });
  });
}
