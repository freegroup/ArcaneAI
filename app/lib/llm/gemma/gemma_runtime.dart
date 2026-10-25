import 'package:flutter_gemma/flutter_gemma.dart';
import 'package:flutter_gemma_litertlm/flutter_gemma_litertlm.dart';

/// One-time initialization of the on-device LLM runtime. Keeps flutter_gemma
/// setup out of the app, which only ever talks to [GemmaLlm] /
/// [GemmaModelInstaller].
abstract final class GemmaRuntime {
  /// Registers the LiteRT-LM engine. Call once in `main()` before use.
  static Future<void> initialize() =>
      FlutterGemma.initialize(inferenceEngines: const [LiteRtLmEngine()]);
}
