import 'package:flutter/material.dart';

import '../../llm/llm_trace.dart';

/// Debug view of every model call as a chat: what went into the model (IN,
/// right) and what it generated (OUT, left). The newest call is at the
/// bottom and always in view; the oldest drop out at the top.
class LlmTracePanel extends StatefulWidget {
  const LlmTracePanel({super.key, required this.trace});

  /// The recorded calls.
  final LlmTrace trace;

  @override
  State<LlmTracePanel> createState() => _LlmTracePanelState();
}

class _LlmTracePanelState extends State<LlmTracePanel> {
  final _scroll = ScrollController();

  @override
  void initState() {
    super.initState();
    widget.trace.addListener(_toBottom);
  }

  @override
  void dispose() {
    widget.trace.removeListener(_toBottom);
    _scroll.dispose();
    super.dispose();
  }

  // The list is reversed: offset 0 is its bottom.
  void _toBottom() => WidgetsBinding.instance.addPostFrameCallback((_) {
    if (_scroll.hasClients) _scroll.jumpTo(0);
  });

  @override
  Widget build(BuildContext context) => ListenableBuilder(
    listenable: widget.trace,
    builder: (context, _) {
      final calls = widget.trace.calls; // newest first
      return Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Padding(
            padding: const EdgeInsets.all(12),
            child: Text(
              'LLM-Aufrufe (${calls.length})',
              style: Theme.of(context).textTheme.titleMedium,
            ),
          ),
          const Divider(height: 1),
          Expanded(
            child: calls.isEmpty
                ? const Center(child: Text('Noch kein Aufruf.'))
                : ListView.builder(
                    controller: _scroll,
                    reverse: true,
                    padding: const EdgeInsets.all(12),
                    itemCount: calls.length,
                    itemBuilder: (_, i) => _Call(calls[i]),
                  ),
          ),
        ],
      );
    },
  );
}

/// One call: a header line, then IN and OUT as chat bubbles.
class _Call extends StatelessWidget {
  const _Call(this.call);

  final LlmTraceCall call;

  @override
  Widget build(BuildContext context) {
    final time = call.started.toIso8601String().substring(11, 19);
    final duration = switch (call.duration) {
      null => 'läuft …',
      final duration => '${duration.inMilliseconds} ms',
    };
    final error = call.error;
    final label = Theme.of(context).textTheme.labelMedium;
    return Padding(
      padding: const EdgeInsets.only(bottom: 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(
            '$time · $duration\n${call.settings}',
            textAlign: TextAlign.center,
            style: label,
          ),
          const SizedBox(height: 8),
          _Bubble(
            title: 'IN · ${call.stage} · ${call.inputChars} Zeichen',
            color: Colors.lightBlueAccent,
            right: true,
            children: [
              for (final message in call.messages)
                _Part(role: message.role, text: message.text),
              // Last, so it is in view next to the answer.
              if (call.functions.isNotEmpty)
                _Part(
                  role: 'angebotene Funktionen (als Tools übergeben)',
                  text: call.functions.join('\n'),
                ),
            ],
          ),
          const SizedBox(height: 8),
          if (error != null)
            _Bubble(
              title: 'FEHLER',
              color: Colors.redAccent,
              children: [_Part(text: error)],
            )
          else
            _Bubble(
              title: 'OUT · ${call.output?.length ?? 0} Zeichen',
              color: Colors.lightGreenAccent,
              children: [_Part(text: call.output ?? 'läuft …')],
            ),
        ],
      ),
    );
  }
}

class _Bubble extends StatelessWidget {
  const _Bubble({
    required this.title,
    required this.color,
    required this.children,
    this.right = false,
  });

  final String title;
  final Color color;
  final List<Widget> children;
  final bool right;

  @override
  Widget build(BuildContext context) => FractionallySizedBox(
    alignment: right ? Alignment.centerRight : Alignment.centerLeft,
    widthFactor: 0.92,
    child: Container(
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.08),
        border: Border.all(color: color.withValues(alpha: 0.5)),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: TextStyle(color: color, fontWeight: FontWeight.bold),
          ),
          ...children,
        ],
      ),
    ),
  );
}

/// One part of a bubble: an optional role label (not sent as text), then
/// the exact text.
class _Part extends StatelessWidget {
  const _Part({required this.text, this.role});

  final String? role;
  final String text;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(top: 8),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (role case final role?)
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
            decoration: BoxDecoration(
              color: Colors.white12,
              borderRadius: BorderRadius.circular(4),
            ),
            child: Text(
              role.toUpperCase(),
              style: Theme.of(context).textTheme.labelSmall,
            ),
          ),
        if (text.isNotEmpty) ...[
          const SizedBox(height: 4),
          SelectableText(
            text,
            style: const TextStyle(
              fontFamily: 'Menlo',
              fontFamilyFallback: ['monospace', 'Courier New'],
              fontSize: 12,
            ),
          ),
        ],
      ],
    ),
  );
}
