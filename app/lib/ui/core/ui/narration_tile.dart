import 'package:flutter/material.dart';

import '../../game/game_view_model.dart';

/// One exchange in the game log: the player's words (right, if any) and the
/// narration (left). The narration is a live region so a screen reader
/// announces new text.
class NarrationTile extends StatelessWidget {
  const NarrationTile({super.key, required this.line});

  /// The line to render.
  final GameLine line;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.only(bottom: 20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (line.playerInput != null)
            Align(
              alignment: Alignment.centerRight,
              child: Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 14,
                  vertical: 10,
                ),
                decoration: BoxDecoration(
                  color: theme.colorScheme.primaryContainer,
                  borderRadius: BorderRadius.circular(14),
                ),
                child: Text(line.playerInput!),
              ),
            ),
          if (line.playerInput != null) const SizedBox(height: 10),
          Semantics(
            liveRegion: true,
            child: Text(line.text, style: theme.textTheme.bodyLarge),
          ),
        ],
      ),
    );
  }
}
