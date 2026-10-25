import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../utils/result.dart';
import 'startup_view_model.dart';

/// Shown while the start location is resolved, then navigates there.
class StartupScreen extends StatefulWidget {
  const StartupScreen({super.key, required this.viewModel});

  /// The screen's view model.
  final StartupViewModel viewModel;

  @override
  State<StartupScreen> createState() => _StartupScreenState();
}

class _StartupScreenState extends State<StartupScreen> {
  @override
  void initState() {
    super.initState();
    widget.viewModel.resolve.addListener(_onResolved);
  }

  @override
  void dispose() {
    widget.viewModel.resolve.removeListener(_onResolved);
    super.dispose();
  }

  void _onResolved() {
    if (widget.viewModel.resolve.result case Ok(:final value) when mounted) {
      context.go(value);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    body: Center(
      child: Semantics(
        label: 'Spiel wird geladen',
        child: const CircularProgressIndicator(),
      ),
    ),
  );
}
