import 'package:arcane_player/llm/gemma/arcane_llm_litert.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../routing/routes.dart';
import 'model_setup_view_model.dart';

/// Prompts for and shows the model download. On success it continues to the
/// game (resuming a saved one) or the home screen.
class ModelSetupScreen extends StatefulWidget {
  const ModelSetupScreen({super.key, required this.viewModel});

  /// The screen's view model.
  final ModelSetupViewModel viewModel;

  @override
  State<ModelSetupScreen> createState() => _ModelSetupScreenState();
}

class _ModelSetupScreenState extends State<ModelSetupScreen> {
  @override
  void initState() {
    super.initState();
    widget.viewModel.download.addListener(_onDownload);
  }

  @override
  void dispose() {
    widget.viewModel.download.removeListener(_onDownload);
    super.dispose();
  }

  void _onDownload() {
    if (widget.viewModel.download.completed && mounted) {
      context.go(Routes.startup);
    }
  }

  @override
  Widget build(BuildContext context) {
    final vm = widget.viewModel;
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(title: const Text('Sprachmodell einrichten')),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: ListenableBuilder(
            listenable: vm,
            builder: (context, _) => Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Text(
                  vm.model.label,
                  style: theme.textTheme.titleLarge,
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 12),
                Text(
                  'Das Spiel läuft vollständig offline auf deinem Gerät. '
                  'Dafür wird einmalig das Sprachmodell '
                  '(${vm.model.sizeGb.toStringAsFixed(1)} GB) geladen — '
                  'am besten über WLAN.',
                  textAlign: TextAlign.center,
                  style: theme.textTheme.bodyMedium,
                ),
                const SizedBox(height: 32),
                _statusView(context, vm),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _statusView(BuildContext context, ModelSetupViewModel vm) {
    switch (vm.status) {
      case ModelDownloading(:final progress):
        return Column(
          children: [
            LinearProgressIndicator(value: progress > 0 ? progress : null),
            const SizedBox(height: 12),
            Text('${(progress * 100).round()} %'),
            const SizedBox(height: 12),
            TextButton(onPressed: vm.cancel, child: const Text('Abbrechen')),
          ],
        );
      case ModelFailed(:final message):
        return Column(
          children: [
            Text(
              'Fehler: $message',
              style: TextStyle(color: Theme.of(context).colorScheme.error),
            ),
            const SizedBox(height: 16),
            FilledButton(
              onPressed: vm.download.execute,
              child: const Text('Erneut versuchen'),
            ),
          ],
        );
      case ModelReady():
        return const Center(child: CircularProgressIndicator());
      case ModelAbsent():
        return FilledButton.icon(
          onPressed: vm.download.execute,
          icon: const Icon(Icons.download),
          label: const Text('Herunterladen und starten'),
        );
    }
  }
}
