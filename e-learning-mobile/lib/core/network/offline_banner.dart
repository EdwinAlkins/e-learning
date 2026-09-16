import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

final connectivityProvider = StreamProvider<List<ConnectivityResult>>((ref) {
  return Connectivity().onConnectivityChanged;
});

class OfflineBanner extends ConsumerWidget {
  const OfflineBanner({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final connectivity = ref.watch(connectivityProvider);
    final offline = connectivity.maybeWhen(
      data: (results) =>
          results.isEmpty || results.every((r) => r == ConnectivityResult.none),
      orElse: () => false,
    );
    if (!offline) return const SizedBox.shrink();
    final scheme = Theme.of(context).colorScheme;
    return ColoredBox(
      color: scheme.errorContainer,
      child: SafeArea(
        bottom: false,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          child: Text(
            'Hors ligne — certaines actions sont indisponibles.',
            // Sans couleur explicite, le texte héritait de `onSurface` : illisible
            // sur le fond `errorContainer` du thème sombre.
            style: TextStyle(color: scheme.onErrorContainer),
          ),
        ),
      ),
    );
  }
}
