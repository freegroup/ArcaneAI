import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

/// The large microphone button that dominates the game screen — one big
/// target for an audio-first, screen-reader-friendly UI.
class MicButton extends StatelessWidget {
  const MicButton({
    super.key,
    required this.listening,
    required this.enabled,
    required this.onPressed,
  });

  /// Whether the microphone is currently listening.
  final bool listening;

  /// Whether the button is enabled.
  final bool enabled;

  /// Called on tap.
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Semantics(
      button: true,
      enabled: enabled,
      label: listening ? 'Zuhören beenden' : 'Sprechen',
      child: SizedBox(
        width: 96,
        height: 96,
        child: FloatingActionButton.large(
          heroTag: 'mic',
          backgroundColor: listening ? scheme.error : scheme.primaryContainer,
          onPressed: enabled
              ? () {
                  HapticFeedback.mediumImpact();
                  onPressed();
                }
              : null,
          child: Icon(listening ? Icons.stop : Icons.mic, size: 44),
        ),
      ),
    );
  }
}
