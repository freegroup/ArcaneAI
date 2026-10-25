import 'dart:async';
import 'dart:io';

import 'package:flutter_gemma/flutter_gemma.dart';
import 'package:logging/logging.dart';
import 'package:meta/meta.dart';

import 'gemma_catalog.dart';

/// Where a model's installation stands.
@immutable
sealed class ModelStatus {
  const ModelStatus();
}

/// The model is not on the device.
final class ModelAbsent extends ModelStatus {
  const ModelAbsent();
}

/// The model is downloading; [progress] is 0..1.
final class ModelDownloading extends ModelStatus {
  const ModelDownloading(this.progress);

  /// Fraction downloaded, 0..1.
  final double progress;
}

/// The model is installed and ready.
final class ModelReady extends ModelStatus {
  const ModelReady();
}

/// Installing failed; [message] says why.
final class ModelFailed extends ModelStatus {
  const ModelFailed(this.message);

  /// Failure reason.
  final String message;
}

/// Installs and manages on-device Gemma models through flutter_gemma.
///
/// Download is resumable (flutter_gemma skips a file already on disk) and
/// reports progress on [statusStream]. For development a local `.litertlm`
/// file can be registered directly, bypassing the download.
final class GemmaModelInstaller {
  GemmaModelInstaller({GemmaModel? model})
    : model = model ?? GemmaCatalog.defaultModel;

  static final _log = Logger('arcane_llm_litert.installer');

  /// The model this installer manages.
  final GemmaModel model;

  final StreamController<ModelStatus> _status = StreamController.broadcast();
  CancelToken? _cancel;

  /// Live installation status (download progress, ready, failed).
  Stream<ModelStatus> get statusStream => _status.stream;

  /// Whether the downloaded model is installed and valid.
  Future<bool> isInstalled() =>
      _isValid(ModelSource.network(model.url.toString()));

  /// Registers a local `.litertlm` file as the model (development only).
  /// The file is used in place, not copied. Placed where downloads go, the
  /// same file also counts as the downloaded model — one copy for all.
  Future<void> useLocalFile(String path) async {
    // Checked first: a missing file must not cost a valid installation.
    if (!await File(path).exists()) {
      throw ArgumentError.value(path, 'path', 'Model file not found');
    }
    final fileName = path.split(Platform.pathSeparator).last;
    if (await FlutterGemma.isModelInstalled(fileName)) {
      final registered = await FlutterGemma.getModelPath(fileName);
      if (registered != path) {
        // flutter_gemma skips files it has a record for, so a record for
        // another place must go — but only if its file is gone.
        if (await File(registered).exists()) {
          throw StateError('$fileName is already installed at $registered');
        }
        await _forget(fileName);
      }
    }
    await _builder().fromFile(path).install();
  }

  /// Ensures the model is installed (downloading it if needed) and active.
  /// Returns whether it is ready afterwards. Safe to call on every launch:
  /// an installed model is only activated, not downloaded again.
  Future<bool> ensureInstalled() async {
    final source = ModelSource.network(model.url.toString());
    _cancel = CancelToken();
    try {
      if (!await _dropInvalidRecord(source)) {
        _status.add(const ModelDownloading(0));
      }
      await _builder()
          .fromNetwork(model.url.toString())
          .withProgress((percent) {
            _status.add(ModelDownloading((percent / 100).clamp(0, 1)));
          })
          .withCancelToken(_cancel!)
          .install();
      _status.add(const ModelReady());
      return true;
    } on Object catch (e) {
      _log.warning('Model install failed: $e');
      _status.add(ModelFailed('$e'));
      return false;
    } finally {
      _cancel = null;
    }
  }

  InferenceInstallationBuilder _builder() => FlutterGemma.installModel(
    modelType: ModelType.gemma4,
    fileType: ModelFileType.litertlm,
  );

  /// flutter_gemma's own check (the one model loading uses): a record for
  /// the file, and the file valid where [source] puts it.
  Future<bool> _isValid(ModelSource source) =>
      FlutterGemmaPlugin.instance.modelManager.isModelInstalled(
        InferenceModelSpec(
          name: model.id,
          modelSource: source,
          modelType: ModelType.gemma4,
          fileType: ModelFileType.litertlm,
        ),
      );

  /// Removes the record of [fileName].
  Future<void> _forget(String fileName) async {
    _log.info('Removing stale model record: $fileName');
    await FlutterGemma.uninstallModel(fileName);
  }

  /// Returns whether the model is valid for [source]. Otherwise removes a
  /// leftover record of its file name — installation skips files it has a
  /// record for, so the model could never be installed again. Such a record
  /// is stale (file moved or deleted) or was made for another source (a
  /// development build registering a local file); removing it deletes no
  /// usable file.
  Future<bool> _dropInvalidRecord(ModelSource source) async {
    if (await _isValid(source)) return true;
    final fileName = InferenceModelSpec(
      name: model.id,
      modelSource: source,
      modelType: ModelType.gemma4,
      fileType: ModelFileType.litertlm,
    ).files.first.filename;
    if (await FlutterGemma.isModelInstalled(fileName)) await _forget(fileName);
    return false;
  }

  /// Cancels an in-progress download.
  void cancel() => _cancel?.cancel('cancelled by user');

  /// Removes the installed model files.
  Future<void> uninstall() => FlutterGemma.uninstallModel(model.fileName);

  /// Releases resources.
  Future<void> dispose() => _status.close();
}
