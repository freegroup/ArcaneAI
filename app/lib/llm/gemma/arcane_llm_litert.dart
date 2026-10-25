/// On-device language model for ArcaneAI: Gemma 4 via LiteRT-LM.
///
/// [GemmaModelInstaller] downloads/manages the model; [GemmaLlm] is the
/// engine's `LlmProvider`, so the game runs fully offline.
library;

export 'gemma_catalog.dart';
export 'gemma_model_installer.dart';
export 'gemma_llm.dart';
export 'gemma_runtime.dart';
