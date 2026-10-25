import 'package:flutter/material.dart';

import '../routing/router.dart';
import 'core/ui/screen_reader_sync.dart';

/// Wraps the [MaterialApp.router] with the app's [GoRouter]. Kept separate so
/// the router is built once below the providers.
class ArcaneRoutingApp extends StatefulWidget {
  const ArcaneRoutingApp({super.key, required this.theme});

  /// The app theme.
  final ThemeData theme;

  @override
  State<ArcaneRoutingApp> createState() => _ArcaneRoutingAppState();
}

class _ArcaneRoutingAppState extends State<ArcaneRoutingApp> {
  late final _router = buildRouter();

  @override
  Widget build(BuildContext context) => MaterialApp.router(
    title: 'ArcaneAI',
    theme: widget.theme,
    debugShowCheckedModeBanner: false,
    routerConfig: _router,
    // Below MaterialApp so it sees the platform's accessibility features.
    builder: (context, child) => ScreenReaderSync(child: child!),
  );
}
