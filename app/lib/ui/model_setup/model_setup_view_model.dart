import 'package:arcane_player/llm/gemma/arcane_llm_litert.dart';
import 'package:flutter/foundation.dart';

import '../../data/repositories/model_repository.dart';
import '../../utils/command.dart';
import '../../utils/result.dart';

/// View model for the model setup screen: triggers the (resumable) download
/// and exposes progress.
final class ModelSetupViewModel extends ChangeNotifier {
  ModelSetupViewModel({required ModelRepository models}) : _models = models {
    download = Command0(_download);
    _models.addListener(notifyListeners);
  }

  final ModelRepository _models;

  /// Downloads/loads the model.
  late final Command0<void> download;

  /// The model being installed (name, size).
  GemmaModel get model => _models.model;

  /// Current install status.
  ModelStatus get status => _models.status;

  Future<Result<void>> _download() async {
    final result = await _models.prepare();
    return switch (result) {
      Ok() => const Result.ok(null),
      Error(:final error) => Result.error(error),
    };
  }

  /// Cancels an in-progress download.
  void cancel() => _models.cancelDownload();

  @override
  void dispose() {
    _models.removeListener(notifyListeners);
    download.dispose();
    super.dispose();
  }
}
