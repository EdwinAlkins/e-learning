import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:shimmer/shimmer.dart';

import '../../../core/auth/auth_controller.dart';
import '../../../core/network/offline_banner.dart';
import '../../../core/utils/time_format.dart';
import '../../settings/widgets/settings_sheet.dart';
import '../providers/catalog_provider.dart';

class CatalogScreen extends ConsumerWidget {
  const CatalogScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final catalog = ref.watch(catalogProvider);
    final auth = ref.watch(authControllerProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Formations'),
        actions: [
          const SettingsButton(),
          IconButton(
            tooltip: 'Déconnexion',
            onPressed: () async {
              await ref.read(authControllerProvider.notifier).logout();
            },
            icon: const Icon(Icons.logout),
          ),
        ],
      ),
      body: Column(
        children: [
          const OfflineBanner(),
          Expanded(
            child: catalog.when(
              loading: () => const _CatalogSkeleton(),
              error: (e, _) => _ErrorView(
                message: e.toString(),
                onRetry: () => ref.invalidate(catalogProvider),
              ),
              data: (data) {
                if (data.formations.isEmpty) {
                  return const Center(
                    child: Text('Aucune formation disponible.'),
                  );
                }
                return RefreshIndicator(
                  onRefresh: () async => ref.invalidate(catalogProvider),
                  child: ListView.separated(
                    padding: const EdgeInsets.all(16),
                    itemCount: data.formations.length,
                    separatorBuilder: (_, _) => const SizedBox(height: 12),
                    itemBuilder: (context, index) {
                      final formation = data.formations[index];
                      final progress = data.progress[formation.id];
                      final pct = progress?.progressPercentage ?? 0;
                      final videoCount = formation.chapters.fold<int>(
                        0,
                        (sum, c) => sum + c.videos.length,
                      );
                      final duration = formation.chapters.fold<double>(
                        0,
                        (sum, c) =>
                            sum +
                            c.videos.fold<double>(0, (s, v) => s + v.duration),
                      );

                      return Card(
                        clipBehavior: Clip.antiAlias,
                        child: InkWell(
                          onTap: () =>
                              context.push('/formation/${formation.id}'),
                          child: Padding(
                            padding: const EdgeInsets.all(16),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  formation.name,
                                  style: Theme.of(context).textTheme.titleMedium
                                      ?.copyWith(fontWeight: FontWeight.w600),
                                ),
                                const SizedBox(height: 8),
                                Text(
                                  '$videoCount médias · ${formatDuration(duration)}',
                                  style: Theme.of(context).textTheme.bodySmall,
                                ),
                                const SizedBox(height: 12),
                                LinearProgressIndicator(
                                  value: (pct / 100).clamp(0, 1),
                                  minHeight: 6,
                                  borderRadius: BorderRadius.circular(8),
                                ),
                                const SizedBox(height: 6),
                                Text(
                                  '${pct.round()} % complété',
                                  style: Theme.of(context)
                                      .textTheme
                                      .labelMedium,
                                ),
                                if (auth.uid != null) ...[
                                  const SizedBox(height: 4),
                                ],
                              ],
                            ),
                          ),
                        ),
                      );
                    },
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

class _CatalogSkeleton extends StatelessWidget {
  const _CatalogSkeleton();

  @override
  Widget build(BuildContext context) {
    // Les couleurs du squelette viennent du `ColorScheme` : en dur, les blocs
    // restaient blancs et éblouissaient en thème sombre.
    final scheme = Theme.of(context).colorScheme;
    final isDark = scheme.brightness == Brightness.dark;
    return Shimmer.fromColors(
      baseColor: scheme.surfaceContainerHighest,
      // Le reflet doit s'éclaircir en sombre et s'assombrir en clair, sinon
      // l'animation passe inaperçue.
      highlightColor: isDark
          ? Color.lerp(
              scheme.surfaceContainerHighest,
              scheme.onSurface,
              0.14,
            )!
          : scheme.surfaceContainerLow,
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: 4,
        itemBuilder: (_, _) => Container(
          height: 110,
          margin: const EdgeInsets.only(bottom: 12),
          decoration: BoxDecoration(
            color: scheme.surfaceContainerHighest,
            borderRadius: BorderRadius.circular(12),
          ),
        ),
      ),
    );
  }
}

class _ErrorView extends StatelessWidget {
  const _ErrorView({required this.message, required this.onRetry});

  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(message, textAlign: TextAlign.center),
            const SizedBox(height: 16),
            FilledButton(onPressed: onRetry, child: const Text('Réessayer')),
          ],
        ),
      ),
    );
  }
}
