import 'config/app.dart';

/// Development entry point: registers a local `.litertlm`, so no download
/// is needed. Pass the model path with
/// `--dart-define=MODEL_PATH=/abs/path/to/model.litertlm`.
///
/// With `--dart-define=GOOGLE_TTS_API_KEY=…` (and optionally
/// `GOOGLE_TTS_VOICE`) Google Cloud speaks, as in the Python game;
/// `start.sh --dev` takes both from config.yaml.
Future<void> main() => runArcanePlayer(
  localModelPath: _modelPath.isEmpty ? null : _modelPath,
  googleTts: _googleTtsApiKey.isEmpty
      ? null
      : (apiKey: _googleTtsApiKey, voice: _googleTtsVoice),
);

const _modelPath = String.fromEnvironment('MODEL_PATH');
const _googleTtsApiKey = String.fromEnvironment('GOOGLE_TTS_API_KEY');
const _googleTtsVoice = String.fromEnvironment(
  'GOOGLE_TTS_VOICE',
  defaultValue: 'de-DE-Chirp3-HD-Schedar',
);
