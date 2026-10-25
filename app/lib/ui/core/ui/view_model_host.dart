import 'package:flutter/widgets.dart';

/// Owns a route's view model: creates it once (route rebuilds do not
/// recreate it) and disposes it when the route goes away.
class ViewModelHost<T extends ChangeNotifier> extends StatefulWidget {
  const ViewModelHost({super.key, required this.create, required this.builder});

  /// Creates the view model; may read providers from [BuildContext].
  final T Function(BuildContext context) create;

  /// Builds the screen for the view model.
  final Widget Function(BuildContext context, T viewModel) builder;

  @override
  State<ViewModelHost<T>> createState() => _ViewModelHostState<T>();
}

class _ViewModelHostState<T extends ChangeNotifier>
    extends State<ViewModelHost<T>> {
  late final T _viewModel = widget.create(context);

  @override
  void dispose() {
    _viewModel.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => widget.builder(context, _viewModel);
}
