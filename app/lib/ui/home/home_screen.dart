import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../routing/routes.dart';
import 'home_view_model.dart';

/// Lets the player pick a game. Shown on first launch and via the menu; a
/// game in progress is resumed automatically without passing through here.
class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key, required this.viewModel});

  /// The screen's view model.
  final HomeViewModel viewModel;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('ArcaneAI')),
      body: ListenableBuilder(
        listenable: viewModel.loadGames,
        builder: (context, _) {
          if (viewModel.loadGames.running) {
            return const Center(child: CircularProgressIndicator());
          }
          if (viewModel.loadGames.error) {
            return Center(
              child: FilledButton(
                onPressed: viewModel.loadGames.execute,
                child: const Text('Erneut versuchen'),
              ),
            );
          }
          return ListenableBuilder(
            listenable: viewModel,
            builder: (context, _) => ListView(
              padding: const EdgeInsets.all(16),
              children: [
                for (final game in viewModel.games)
                  Card(
                    child: ListTile(
                      title: Text(game.title),
                      trailing: const Icon(Icons.play_arrow),
                      onTap: () => context.go(Routes.game(game.gameId)),
                    ),
                  ),
              ],
            ),
          );
        },
      ),
    );
  }
}
