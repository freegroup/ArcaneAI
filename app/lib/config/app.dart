import 'dart:ui';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

import 'package:arcane_player/llm/gemma/arcane_llm_litert.dart';
import 'package:logging/logging.dart';

import '../config/dependencies.dart';
import '../ui/core/themes/app_theme.dart';
import '../ui/routing_app.dart';

/// Boots the dependencies and runs the app. [localModelPath] registers a
/// local `.litertlm` instead of downloading, [googleTts] lets Google Cloud
/// speak (both development).
Future<void> runArcanePlayer({
  String? localModelPath,
  ({String apiKey, String voice})? googleTts,
}) async {
  WidgetsFlutterBinding.ensureInitialized();
  // The packages log through package:logging; without a listener nothing
  // would show. Debug builds show everything — including, word for word,
  // every prompt sent to the model and every answer (logger `llm`);
  // release builds only problems.
  Logger.root.level = kDebugMode ? Level.ALL : Level.WARNING;
  Logger.root.onRecord.listen((record) {
    debugPrint(
      '[${record.loggerName}] ${record.message}'
      '${record.error == null ? '' : ' — ${record.error}'}',
    );
  });
  await GemmaRuntime.initialize();
  final dependencies = await AppDependencies.boot(
    localModelPath: localModelPath,
    googleTts: googleTts,
  );
  runApp(dependencies.wrap(ArcanePlayerApp(dependencies: dependencies)));
}

/// The root widget: applies the theme, installs the router, saves the game
/// whenever the app is backgrounded and releases everything on exit.
class ArcanePlayerApp extends StatefulWidget {
  const ArcanePlayerApp({super.key, required this.dependencies});

  /// The wired-up dependencies.
  final AppDependencies dependencies;

  @override
  State<ArcanePlayerApp> createState() => _ArcanePlayerAppState();
}

class _ArcanePlayerAppState extends State<ArcanePlayerApp> {
  late final AppLifecycleListener _lifecycle;

  @override
  void initState() {
    super.initState();
    // Mobile OSes kill backgrounded apps without warning; save on every
    // pause/hide/exit so progress is never lost.
    _lifecycle = AppLifecycleListener(
      onPause: _save,
      onHide: _save,
      onExitRequested: () async {
        await widget.dependencies.close(); // saves first
        return AppExitResponse.exit;
      },
    );
  }

  Future<void> _save() => widget.dependencies.sessions.save();

  @override
  void dispose() {
    _lifecycle.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => ArcaneRoutingApp(theme: AppTheme.dark);
}
