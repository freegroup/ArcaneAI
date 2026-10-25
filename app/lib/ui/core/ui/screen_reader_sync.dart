import 'package:arcane_player/audio/arcane_audio.dart';
import 'package:flutter/widgets.dart';
import 'package:provider/provider.dart';

/// Routes narration to the screen reader while VoiceOver/TalkBack is active,
/// so a blind player hears one voice — their own reader — not two.
class ScreenReaderSync extends StatefulWidget {
  const ScreenReaderSync({super.key, required this.child});

  /// The app below.
  final Widget child;

  @override
  State<ScreenReaderSync> createState() => _ScreenReaderSyncState();
}

class _ScreenReaderSyncState extends State<ScreenReaderSync> {
  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    context.read<AdaptiveSpeechOutput>().useScreenReader =
        MediaQuery.accessibleNavigationOf(context);
  }

  @override
  Widget build(BuildContext context) => widget.child;
}
