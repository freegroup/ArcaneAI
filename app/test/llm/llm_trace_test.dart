import 'package:arcane_player/llm/llm_trace.dart';
import 'package:flutter_test/flutter_test.dart';

LlmTraceCall _call(String stage, [String text = '']) => LlmTraceCall(
  stage,
  settings: '',
  messages: [LlmTraceMessage('user', text)],
);

void main() {
  test('records calls newest first, with their input and output', () {
    final trace = LlmTrace();
    final first = _call('Stufe 1', 'rein');
    trace
      ..start(first)
      ..finish(first, const Duration(milliseconds: 5), output: 'raus');
    final second = _call('Stufe 2');
    trace.start(second);

    expect(trace.calls, [second, first]);
    expect(first.inputChars, 4);
    expect(first.output, 'raus');
    expect(first.duration, const Duration(milliseconds: 5));
    expect(second.duration, isNull, reason: 'still running');
  });

  test('records a failed call', () {
    final trace = LlmTrace();
    final call = _call('Stufe 1');
    trace
      ..start(call)
      ..finish(call, Duration.zero, error: 'kaputt');
    expect(call.error, 'kaputt');
    expect(call.output, isNull);
  });

  test('keeps only the latest calls', () {
    final trace = LlmTrace();
    for (var i = 0; i <= LlmTrace.maxCalls; i++) {
      trace.start(_call('$i'));
    }
    expect(trace.calls, hasLength(LlmTrace.maxCalls));
    expect(trace.calls.last.stage, '1', reason: 'the oldest was dropped');
  });

  test('clear drops every recorded call and notifies once', () {
    final trace = LlmTrace();
    trace
      ..start(_call('Stufe 1'))
      ..start(_call('Stufe 2'));
    var notifications = 0;
    trace.addListener(() => notifications++);

    trace.clear();
    expect(trace.calls, isEmpty);
    expect(notifications, 1);

    trace.clear();
    expect(notifications, 1, reason: 'nothing to clear, no notification');
  });
}
