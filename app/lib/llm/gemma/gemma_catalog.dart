import 'package:meta/meta.dart';

/// A Gemma model that can run on device, with its download coordinates.
@immutable
final class GemmaModel {
  const GemmaModel({
    required this.id,
    required this.label,
    required this.url,
    required this.fileName,
    required this.sizeBytes,
  });

  /// Stable identifier used by flutter_gemma to track the installation.
  final String id;

  /// Human-readable name for the setup screen.
  final String label;

  /// Download URL of the `.litertlm` file.
  final Uri url;

  /// File name flutter_gemma stores it under.
  final String fileName;

  /// Approximate download size, for the setup screen.
  final int sizeBytes;

  /// Rounded size in gigabytes.
  double get sizeGb => sizeBytes / (1 << 30);
}

/// The model the app uses: Gemma 4 E4B, the best quality that still fits a
/// phone.
abstract final class GemmaCatalog {
  /// Gemma 4 E4B — ~3.7 GB, the recommended on-device model.
  static final e4b = GemmaModel(
    id: 'gemma-4-E4B-it',
    label: 'Gemma 4 E4B (empfohlen)',
    url: Uri.parse(
      'https://huggingface.co/litert-community/gemma-4-E4B-it-litert-lm/'
      'resolve/main/gemma-4-E4B-it.litertlm',
    ),
    fileName: 'gemma-4-E4B-it.litertlm',
    sizeBytes: 3659530240,
  );

  /// The default model.
  static final defaultModel = e4b;
}
