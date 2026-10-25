import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../llm/llm_trace.dart';

import '../../routing/routes.dart';
import '../core/ui/html_text.dart';
import '../core/ui/mic_button.dart';
import '../core/ui/narration_tile.dart';
import '../llm_trace/llm_trace_panel.dart';
import 'game_view_model.dart';

/// The game screen: the conversation log, a large microphone and a text
/// field that keeps focus. At the top: back to the game list, help, the
/// personality switch and restart. In a wide window (desktop) every model
/// call is shown on the left ([LlmTracePanel]).
class GameScreen extends StatefulWidget {
  const GameScreen({super.key, required this.viewModel});

  /// The screen's view model.
  final GameViewModel viewModel;

  @override
  State<GameScreen> createState() => _GameScreenState();
}

class _GameScreenState extends State<GameScreen> {
  final _input = TextEditingController();
  final _inputFocus = FocusNode();
  final _scroll = ScrollController();
  int _shownLines = 0;

  GameViewModel get _vm => widget.viewModel;

  @override
  void initState() {
    super.initState();
    _vm.addListener(_onChange);
    _inputFocus.addListener(_keepFocus);
  }

  @override
  void dispose() {
    _vm.removeListener(_onChange);
    _input.dispose();
    _inputFocus.dispose();
    _scroll.dispose();
    super.dispose();
  }

  void _onChange() {
    // Live transcription shows in the field while listening.
    if (_vm.listening && _vm.partialInput.isNotEmpty) {
      _input.text = _vm.partialInput;
    }
    if (_vm.lines.length == _shownLines) return;
    _shownLines = _vm.lines.length;
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scroll.hasClients) {
        _scroll.animateTo(
          _scroll.position.maxScrollExtent,
          duration: const Duration(milliseconds: 250),
          curve: Curves.easeOut,
        );
      }
    });
  }

  // The input field keeps focus except while a dialog or sheet is on top.
  void _keepFocus() {
    if (_inputFocus.hasFocus) return;
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted &&
          !_inputFocus.hasFocus &&
          (ModalRoute.of(context)?.isCurrent ?? true)) {
        _inputFocus.requestFocus();
      }
    });
  }

  void _submit(String text) {
    if (text.trim().isEmpty) return;
    _input.clear();
    _vm.send.execute(text);
  }

  Future<void> _toggleListening() async {
    if (await _vm.toggleListening() || !mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Spracheingabe ist nicht verfügbar.')),
    );
  }

  /// From this window width on, the model calls are shown on the left.
  static const _traceMinWidth = 1100.0;

  @override
  Widget build(BuildContext context) {
    final game = _game(context);
    if (MediaQuery.sizeOf(context).width < _traceMinWidth) return game;
    return Row(
      children: [
        Expanded(
          child: Material(
            child: LlmTracePanel(trace: context.read<LlmTrace>()),
          ),
        ),
        const VerticalDivider(width: 1),
        Expanded(child: game),
      ],
    );
  }

  Widget _game(BuildContext context) {
    return ListenableBuilder(
      listenable: Listenable.merge([_vm, _vm.send, _vm.restart]),
      builder: (context, _) => Scaffold(
        appBar: AppBar(
          leading: IconButton(
            tooltip: 'Spiel wechseln',
            icon: const Icon(Icons.arrow_back),
            onPressed: () => context.go(Routes.home),
          ),
          title: Text(_vm.title),
          actions: [
            if (_vm.helpText.isNotEmpty)
              IconButton(
                tooltip: 'Hilfe',
                icon: const Icon(Icons.help_outline),
                onPressed: _showHelp,
              ),
            IconButton(
              tooltip: _vm.personality
                  ? 'Persönlichkeit ausschalten'
                  : 'Persönlichkeit einschalten',
              isSelected: _vm.personality,
              icon: const Icon(Icons.theater_comedy_outlined),
              selectedIcon: const Icon(Icons.theater_comedy),
              onPressed: () => _vm.setPersonality(!_vm.personality),
            ),
            IconButton(
              tooltip: 'Neu starten',
              icon: const Icon(Icons.restart_alt),
              onPressed: _vm.send.running || _vm.restart.running
                  ? null
                  : _confirmRestart,
            ),
          ],
        ),
        body: ListenableBuilder(
          listenable: _vm.load,
          builder: (context, child) {
            final loading = _vm.load.running || _vm.restart.running;
            if (loading && _vm.lines.isEmpty) {
              return Center(
                child: Semantics(
                  label: 'Spiel wird geladen',
                  child: const CircularProgressIndicator(),
                ),
              );
            }
            if (_vm.load.error || _vm.restart.error) {
              return _ErrorView(onRetry: _vm.load.execute);
            }
            return child!;
          },
          child: _body(context),
        ),
      ),
    );
  }

  Widget _body(BuildContext context) {
    final busy = _vm.send.running || _vm.restart.running;
    return Column(
      children: [
        Expanded(
          child: ListView.builder(
            controller: _scroll,
            padding: const EdgeInsets.all(16),
            itemCount: _vm.lines.length,
            itemBuilder: (_, i) => NarrationTile(line: _vm.lines[i]),
          ),
        ),
        if (busy)
          const LinearProgressIndicator()
        else
          const SizedBox(height: 4),
        if (_vm.send.error)
          Padding(
            padding: const EdgeInsets.all(8),
            child: Semantics(
              liveRegion: true,
              child: Text(
                'Das hat nicht geklappt. Versuch es noch einmal.',
                style: TextStyle(color: Theme.of(context).colorScheme.error),
              ),
            ),
          ),
        if (_vm.isOver)
          Padding(
            padding: const EdgeInsets.all(8),
            child: Text(
              '✦ Ende ✦',
              style: Theme.of(context).textTheme.titleLarge,
            ),
          ),
        _inputBar(busy: busy),
      ],
    );
  }

  Widget _inputBar({required bool busy}) {
    return SafeArea(
      top: false,
      child: Padding(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
        child: Row(
          children: [
            MicButton(
              listening: _vm.listening,
              enabled: !busy && !_vm.isOver && _vm.canListen,
              onPressed: _toggleListening,
            ),
            const SizedBox(width: 16),
            Expanded(
              child: TextField(
                controller: _input,
                focusNode: _inputFocus,
                autofocus: true,
                enabled: !_vm.isOver,
                onSubmitted: _submit,
                onEditingComplete: () {}, // keep focus after Enter
                decoration: InputDecoration(
                  hintText: _vm.listening
                      ? 'Ich höre zu…'
                      : (busy ? 'Moment…' : 'Was tust du?'),
                  border: const OutlineInputBorder(),
                  suffixIcon: IconButton(
                    tooltip: 'Senden',
                    icon: const Icon(Icons.send),
                    onPressed: () => _submit(_input.text),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _showHelp() => showDialog<void>(
    context: context,
    builder: (context) => AlertDialog(
      title: const Text('Hilfe'),
      content: SingleChildScrollView(child: HtmlText(_vm.helpText)),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('Schließen'),
        ),
      ],
    ),
  );

  Future<void> _confirmRestart() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Neu starten?'),
        content: const Text('Der aktuelle Fortschritt geht verloren.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('Abbrechen'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text('Neu starten'),
          ),
        ],
      ),
    );
    if (confirmed ?? false) {
      _input.clear();
      await _vm.restart.execute();
    }
  }
}

class _ErrorView extends StatelessWidget {
  const _ErrorView({required this.onRetry});

  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) => Center(
    child: Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        const Text('Das Spiel konnte nicht geladen werden.'),
        const SizedBox(height: 16),
        FilledButton(onPressed: onRetry, child: const Text('Erneut versuchen')),
      ],
    ),
  );
}
