/// ArcaneAI game engine: game definitions, rules, the game loop
/// ([GameController] with its two stages) and the companion — pure Dart, no
/// Flutter, no I/O.
///
/// Typical use:
/// ```dart
/// final game = OverlayParser.parseJson(id: 'TheTipsyQuest', modelJson: m, configJson: c);
/// final session = GameSession(definition: game, llm: myLlm);
/// final opening = await session.start();
/// final turn = await session.send('ich schau mich um');
/// ```
library;

export 'builtin_functions/builtin_function.dart';
export 'builtin_functions/builtin_registry.dart';
export 'builtin_functions/action_helfe_dem_spieler.dart';
export 'builtin_functions/action_keine_aktion.dart';
export 'builtin_functions/action_on_system_error.dart';
export 'companion/mood_director.dart';
export 'definition/game_definition.dart';
export 'definition/overlay_parser.dart';
export 'events/game_event.dart';
export 'game/function_executor.dart';
export 'game/game_controller.dart';
export 'game/prompt_builder.dart';
export 'game/prompt_config.dart';
export 'game/stage_1_decision.dart';
export 'game/stage_2_narration.dart';
export 'history/exchange.dart';
export '../llm/llm_provider.dart';
export 'runtime/game_state.dart';
export 'runtime/state_machine.dart';
export 'scripting/mini_script_runtime.dart';
export 'scripting/script_runtime.dart';
export 'session/game_session.dart';
export 'session/session_snapshot.dart';
