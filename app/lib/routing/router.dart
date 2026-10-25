import 'package:flutter/foundation.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../ui/core/ui/view_model_host.dart';
import '../ui/game/game_screen.dart';
import '../ui/game/game_view_model.dart';
import '../ui/home/home_screen.dart';
import '../ui/home/home_view_model.dart';
import '../ui/model_setup/model_setup_screen.dart';
import '../ui/model_setup/model_setup_view_model.dart';
import '../ui/startup/startup_screen.dart';
import '../ui/startup/startup_view_model.dart';
import 'routes.dart';

/// Builds the app's router. Every route owns its view model through a
/// [ViewModelHost].
GoRouter buildRouter() => GoRouter(
  initialLocation: Routes.startup,
  routes: [
    GoRoute(
      path: Routes.startup,
      builder: (_, _) => ViewModelHost(
        create: (context) =>
            StartupViewModel(models: context.read(), sessions: context.read()),
        builder: (_, viewModel) => StartupScreen(viewModel: viewModel),
      ),
    ),
    GoRoute(
      path: Routes.setup,
      builder: (_, _) => ViewModelHost(
        create: (context) => ModelSetupViewModel(models: context.read()),
        builder: (_, viewModel) => ModelSetupScreen(viewModel: viewModel),
      ),
    ),
    GoRoute(
      path: Routes.home,
      builder: (_, _) => ViewModelHost(
        create: (context) => HomeViewModel(catalog: context.read()),
        builder: (_, viewModel) => HomeScreen(viewModel: viewModel),
      ),
    ),
    GoRoute(
      path: '/game/:gameId',
      builder: (_, state) {
        final gameId = state.pathParameters['gameId']!;
        return ViewModelHost(
          // A different game is a different page with its own view model.
          key: ValueKey(gameId),
          create: (context) => GameViewModel(
            sessions: context.read(),
            settings: context.read(),
            audio: context.read(),
            trace: context.read(),
            gameId: gameId,
          ),
          builder: (_, viewModel) => GameScreen(viewModel: viewModel),
        );
      },
    ),
  ],
);
