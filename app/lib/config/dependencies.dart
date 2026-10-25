import 'package:arcane_player/audio/arcane_audio.dart';
import 'package:arcane_player/content/arcane_content.dart';
import 'package:arcane_player/engine/arcane_engine.dart';
import 'package:flutter/services.dart' show rootBundle;
import 'package:flutter/widgets.dart';
import 'package:path_provider/path_provider.dart';
import 'package:provider/provider.dart';
import 'package:yaml/yaml.dart';

import '../data/repositories/game_catalog_repository.dart';
import '../data/repositories/game_session_repository.dart';
import '../data/repositories/model_repository.dart';
import '../llm/llm_trace.dart';
import '../data/repositories/settings_repository.dart';
import '../data/services/file_store_service.dart';
import '../data/services/prefs_service.dart';

/// The app's long-lived objects, built once at startup and handed to the
/// widget tree through [wrap].
final class AppDependencies {
  AppDependencies._({
    required this.settings,
    required this.models,
    required this.catalog,
    required this.sessions,
    required this.audio,
    required this.speech,
    required this.trace,
  });

  /// The player's setting (personality on/off).
  final SettingsRepository settings;

  /// The on-device language model.
  final ModelRepository models;

  /// Available games.
  final GameCatalogRepository catalog;

  /// The running game (invisible save/resume).
  final GameSessionRepository sessions;

  /// Shared audio output and microphone arbiter.
  final AudioCoordinator audio;

  /// The narration voice; follows the screen reader (`ScreenReaderSync`).
  final AdaptiveSpeechOutput speech;

  /// Every model call, exactly as sent and received (debug view).
  final LlmTrace trace;

  /// Builds everything. [localModelPath] registers a local `.litertlm`
  /// (development). With [googleTts] (development) Google Cloud speaks, as
  /// in the Python game; otherwise the device's own voice.
  static Future<AppDependencies> boot({
    String? localModelPath,
    ({String apiKey, String voice})? googleTts,
  }) async {
    final settings = SettingsRepository(await PrefsService.load());
    final support = await getApplicationSupportDirectory();
    final resolver = ContentResolver([BundledContentSource()]);
    final catalog = GameCatalogRepository(
      resolver: resolver,
      loader: GamePackLoader(resolver),
    );

    final trace = LlmTrace();
    final models = ModelRepository(
      trace: trace,
      localModelPath: localModelPath,
    );
    final sessions = GameSessionRepository(
      catalog: catalog,
      llm: models,
      store: FileStoreService(directory: Future.value(support)),
      prompts: await _loadPrompts(),
    );

    final systemVoice = SystemTtsSpeechOutput();
    final speech = AdaptiveSpeechOutput(
      voice: googleTts == null
          ? systemVoice
          : GoogleCloudSpeechOutput(
              apiKey: googleTts.apiKey,
              voiceName: googleTts.voice,
              fallback: systemVoice,
            ),
      screenReader: ScreenReaderSpeechOutput(),
    );
    final audio = AudioCoordinator(
      jukebox: AudioPlayersJukebox(),
      speech: speech,
      microphone: SystemSpeechInput(),
    );

    return AppDependencies._(
      settings: settings,
      models: models,
      catalog: catalog,
      sessions: sessions,
      audio: audio,
      speech: speech,
      trace: trace,
    );
  }

  /// [child] with the dependencies provided.
  Widget wrap(Widget child) => MultiProvider(
    providers: [
      ChangeNotifierProvider.value(value: settings),
      ChangeNotifierProvider.value(value: models),
      ChangeNotifierProvider.value(value: sessions),
      Provider.value(value: catalog),
      Provider.value(value: audio),
      Provider.value(value: speech),
      ChangeNotifierProvider.value(value: trace),
    ],
    child: child,
  );

  /// Saves the game and releases everything.
  Future<void> close() async {
    await sessions.close();
    await audio.dispose();
    await models.close();
  }
}

/// Loads the stage prompts and context-length settings from the
/// `prompt_rule_*.yaml` asset files. No prompt text lives in the code.
Future<PromptConfig> _loadPrompts() async {
  Future<Map<String, Object?>> read(String name) async {
    final yaml = loadYaml(
      await rootBundle.loadString('lib/config/prompts/$name'),
    );
    return Map<String, Object?>.from(yaml as Map);
  }

  return PromptConfig.fromMap(
    stage1: await read('prompt_rule_stage1.yaml'),
    stage2WithFunction: await read('prompt_rule_stage2_with_function.yaml'),
    stage2WithoutFunction: await read(
      'prompt_rule_stage2_without_function.yaml',
    ),
    companion: await read('prompt_rule_mood.yaml'),
  );
}
