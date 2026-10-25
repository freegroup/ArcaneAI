import 'dart:async';

import 'package:arcane_player/engine/arcane_engine.dart';
import 'package:arcane_player/llm/gemma/arcane_llm_litert.dart';
import 'package:arcane_player/llm/llm_trace.dart';
import 'package:flutter/foundation.dart';

import '../../utils/result.dart';

/// Supplies the language model to whoever needs it (the session repository)
/// without coupling them to the on-device model.
abstract interface class LlmSource {
  /// The loaded model, or `null` until it is ready.
  LlmProvider? get llm;
}

/// Owns the on-device model: install status and the loaded model. Wraps
/// [GemmaModelInstaller] and [GemmaLlm], so view models never touch
/// flutter_gemma.
final class ModelRepository extends ChangeNotifier implements LlmSource {
  ModelRepository({
    required LlmTrace trace,
    GemmaModelInstaller? installer,
    String? localModelPath,
  }) : _trace = trace,
       _installer = installer ?? GemmaModelInstaller(),
       _localModelPath = localModelPath {
    _statusSubscription = _installer.statusStream.listen((status) {
      _status = status;
      notifyListeners();
    });
  }

  final GemmaModelInstaller _installer;

  /// Where the model records every call.
  final LlmTrace _trace;

  /// A local `.litertlm` registered instead of downloading (development).
  final String? _localModelPath;

  late final StreamSubscription<ModelStatus> _statusSubscription;
  ModelStatus _status = const ModelAbsent();
  GemmaLlm? _llm;

  /// Current install status.
  ModelStatus get status => _status;

  @override
  LlmProvider? get llm => _llm;

  /// The model offered for download.
  GemmaModel get model => _installer.model;

  /// Whether the model can be loaded without a download: a local file
  /// (development) or an installation from an earlier launch.
  Future<bool> isAvailable() async =>
      _localModelPath != null || await _installer.isInstalled();

  /// Makes the model available (registers the local file in development,
  /// otherwise downloads it if needed) and loads it.
  Future<Result<LlmProvider>> prepare() async {
    try {
      if (_llm case final llm?) return Result.ok(llm);
      final local = _localModelPath;
      if (local != null) {
        // A local file is registered, not downloaded: the download path
        // would validate it as a download and reject it.
        await _installer.useLocalFile(local);
        _setStatus(const ModelReady());
      } else if (!await _installer.ensureInstalled()) {
        return Result.error(StateError('Modell konnte nicht geladen werden'));
      }
      return Result.ok(
        _llm = await GemmaLlm.load(model: _installer.model, trace: _trace),
      );
    } on Object catch (e) {
      _setStatus(ModelFailed('$e'));
      return Result.error(e);
    }
  }

  /// Cancels an in-progress download.
  void cancelDownload() => _installer.cancel();

  /// Releases the model and the installer.
  Future<void> close() async {
    await _statusSubscription.cancel();
    await _llm?.close();
    await _installer.dispose();
  }

  void _setStatus(ModelStatus status) {
    _status = status;
    notifyListeners();
  }
}
