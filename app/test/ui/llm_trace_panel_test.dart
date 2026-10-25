import 'package:arcane_player/llm/llm_trace.dart';
import 'package:arcane_player/ui/llm_trace/llm_trace_panel.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('shows each call as IN and OUT, newest at the bottom', (
    tester,
  ) async {
    final trace = LlmTrace();
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(body: LlmTracePanel(trace: trace)),
      ),
    );
    expect(find.text('Noch kein Aufruf.'), findsOneWidget);

    final call = LlmTraceCall(
      'Stufe 1 · Funktionswahl · Versuch 1',
      settings: 'temperature=0.3',
      messages: const [
        LlmTraceMessage('system', 'Du ordnest zu.'),
        LlmTraceMessage('user', 'nimm den stock'),
      ],
      functions: const ['nimm_den_stock: Den Stock nehmen'],
    );
    trace.start(call);
    await tester.pump();
    expect(find.text('LLM-Aufrufe (1)'), findsOneWidget);
    expect(find.text('SYSTEM'), findsOneWidget, reason: 'role as a label');
    expect(
      find.textContaining('IN · Stufe 1 · Funktionswahl'),
      findsOneWidget,
      reason: 'the phase is named at the input',
    );
    expect(find.text('Du ordnest zu.'), findsOneWidget);
    expect(find.text('nimm den stock'), findsOneWidget);
    expect(
      tester.getTopLeft(find.text('nimm_den_stock: Den Stock nehmen')).dy,
      greaterThan(tester.getTopLeft(find.text('nimm den stock')).dy),
      reason: 'the offered functions come last, next to the answer',
    );
    expect(find.text('läuft …'), findsOneWidget, reason: 'no output yet');

    trace.finish(call, const Duration(milliseconds: 1234), output: 'Antwort');
    await tester.pump();
    expect(find.text('Antwort'), findsOneWidget);
    expect(find.textContaining('1234 ms'), findsOneWidget);

    trace.start(
      LlmTraceCall(
        'Stufe 2 · Erzählen',
        settings: '',
        messages: const [LlmTraceMessage('user', 'neu')],
      ),
    );
    await tester.pump();
    final older = tester.getTopLeft(find.text('nimm den stock')).dy;
    final newer = tester.getTopLeft(find.text('neu')).dy;
    expect(
      newer,
      greaterThan(older),
      reason: 'the newest call is at the bottom',
    );
  });
}
