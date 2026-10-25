import 'package:flutter/material.dart';

/// App theme: dark, high-contrast and large text — the game is audio-first
/// and used with a screen reader, so legibility and big touch targets matter
/// more than decoration.
abstract final class AppTheme {
  /// The single dark theme the app uses.
  static ThemeData get dark {
    final scheme = ColorScheme.fromSeed(
      seedColor: Colors.deepPurple,
      brightness: Brightness.dark,
    );
    return ThemeData(
      useMaterial3: true,
      colorScheme: scheme,
      visualDensity: VisualDensity.comfortable,
      textTheme: const TextTheme(
        bodyLarge: TextStyle(fontSize: 20, height: 1.4),
        bodyMedium: TextStyle(fontSize: 16, height: 1.4),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          minimumSize: const Size(64, 56),
          textStyle: const TextStyle(fontSize: 18),
        ),
      ),
    );
  }
}
