import 'package:flutter/material.dart';

/// Renders the game's help text, which uses a tiny HTML subset (`<b>`, `<i>`,
/// `•`, line breaks). Not a full HTML renderer — just enough for the authored
/// help, with no external dependency.
class HtmlText extends StatelessWidget {
  const HtmlText(this.html, {super.key});

  /// The help markup.
  final String html;

  @override
  Widget build(BuildContext context) {
    final base = Theme.of(context).textTheme.bodyMedium;
    return Text.rich(
      TextSpan(children: _spans(html, base)),
      semanticsLabel: _plain(html),
    );
  }

  static List<InlineSpan> _spans(String html, TextStyle? base) {
    final spans = <InlineSpan>[];
    final pattern = RegExp(r'<(/?)(b|i)>|<br\s*/?>', caseSensitive: false);
    var bold = false;
    var italic = false;
    var last = 0;

    void text(String raw) {
      if (raw.isEmpty) return;
      spans.add(
        TextSpan(
          text: raw,
          style: base?.copyWith(
            fontWeight: bold ? FontWeight.bold : null,
            fontStyle: italic ? FontStyle.italic : null,
          ),
        ),
      );
    }

    for (final m in pattern.allMatches(html)) {
      text(html.substring(last, m.start));
      last = m.end;
      final tag = m.group(2)?.toLowerCase();
      final closing = m.group(1) == '/';
      if (tag == 'b') {
        bold = !closing;
      } else if (tag == 'i') {
        italic = !closing;
      } else {
        text('\n'); // <br>
      }
    }
    text(html.substring(last));
    return spans;
  }

  static String _plain(String html) =>
      html.replaceAll(RegExp(r'<[^>]+>'), '').trim();
}
