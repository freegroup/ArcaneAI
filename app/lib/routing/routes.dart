/// The app's route locations.
abstract final class Routes {
  /// Decides where to start.
  static const startup = '/';

  /// Model download.
  static const setup = '/setup';

  /// Game list.
  static const home = '/home';

  /// The game [gameId] (resumes saved progress).
  static String game(String gameId) => '/game/${Uri.encodeComponent(gameId)}';
}
