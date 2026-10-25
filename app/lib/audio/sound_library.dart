import 'package:arcane_player/content/arcane_content.dart';
import 'package:arcane_player/engine/arcane_engine.dart';
import 'package:logging/logging.dart';

/// Resolves the [SoundRef]s of a game to playable content, using the pack's
/// sound table and a [ContentResolver]. A sound that
/// cannot be found yields `null` and a log line — never an error, so a
/// missing sound just stays silent.
final class SoundLibrary {
  SoundLibrary({
    required ContentResolver resolver,
    required Map<String, PackFile> sounds,
  }) : _resolver = resolver,
       _sounds = sounds;

  static final _log = Logger('arcane_audio.library');

  final ContentResolver _resolver;
  final Map<String, PackFile> _sounds;

  /// Locates the file for [sound], or `null` if it is unknown or unavailable.
  Future<ResolvedContent?> resolve(SoundRef sound) async {
    final file = _sounds[sound.path];
    if (file == null) {
      _log.warning('Unknown sound ${sound.path}');
      return null;
    }
    final content = await _resolver.resolveFile(file);
    if (content == null) _log.warning('Sound ${sound.path} is not available');
    return content;
  }
}
