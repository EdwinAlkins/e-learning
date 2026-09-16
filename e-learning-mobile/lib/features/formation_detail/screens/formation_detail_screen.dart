import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../../core/utils/time_format.dart';
import '../../../data/models/models.dart';
import '../../../data/repositories/video_repository.dart';
import '../../settings/widgets/settings_sheet.dart';
import '../providers/formation_detail_provider.dart';

class FormationDetailScreen extends ConsumerWidget {
  const FormationDetailScreen({super.key, required this.formationId});

  final String formationId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final detail = ref.watch(formationDetailProvider(formationId));

    return Scaffold(
      appBar: AppBar(
        title: detail.maybeWhen(
          data: (d) => Text(d.formation.name),
          orElse: () => const Text('Formation'),
        ),
        actions: [
          IconButton(
            tooltip: 'Assistant IA',
            onPressed: () => context.push('/formation/$formationId/assistant'),
            icon: const Icon(Icons.smart_toy_outlined),
          ),
          const SettingsButton(),
        ],
      ),
      body: detail.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(e.toString(), textAlign: TextAlign.center),
                const SizedBox(height: 12),
                FilledButton(
                  onPressed: () =>
                      ref.invalidate(formationDetailProvider(formationId)),
                  child: const Text('Réessayer'),
                ),
              ],
            ),
          ),
        ),
        data: (data) {
          final formation = data.formation;
          final progressMap = <String, double>{};
          for (final chapter in data.progress?.chapters ?? const []) {
            for (final video in chapter.videos) {
              progressMap[video.id] = video.progressPercentage;
            }
          }

          if (formation.chapters.isEmpty) {
            return const Center(child: Text('Aucun chapitre.'));
          }

          return ListView.builder(
            padding: const EdgeInsets.only(bottom: 24),
            itemCount: formation.chapters.length,
            itemBuilder: (context, index) {
              final chapter = formation.chapters[index];
              return _ChapterSection(
                chapter: chapter,
                formationId: formationId,
                progressMap: progressMap,
              );
            },
          );
        },
      ),
    );
  }
}

class _ChapterSection extends ConsumerWidget {
  const _ChapterSection({
    required this.chapter,
    required this.formationId,
    required this.progressMap,
  });

  final ChapterItem chapter;
  final String formationId;
  final Map<String, double> progressMap;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return ExpansionTile(
      initiallyExpanded: true,
      title: Text(
        chapter.name,
        style: const TextStyle(fontWeight: FontWeight.w600),
      ),
      subtitle: Text(
        '${chapter.videos.length} médias · ${chapter.documents.length} docs',
      ),
      children: [
        ...chapter.videos.map((video) {
          final pct = progressMap[video.id] ?? 0;
          final ready = video.isPlayable;
          return ListTile(
            leading: Icon(
              video.isAudio ? Icons.audiotrack : Icons.play_circle_outline,
            ),
            title: Text(video.title),
            subtitle: Text(
              [
                formatDuration(video.duration),
                if (video.isConverting)
                  video
                          .activeJob(JobKind.mediaConversion)
                          ?.label('Conversion…') ??
                      'Conversion…',
                if (video.conversionFailed) 'Échec de conversion',
                if (video.transcriptionStatus == MediaStatus.processing)
                  'Transcription…',
                if (video.summaryStatus == MediaStatus.processing)
                  'Résumé en cours…',
                if (video.hasSummary) 'Résumé disponible',
              ].join(' · '),
            ),
            trailing: pct > 0
                ? SizedBox(
                    width: 40,
                    child: Text(
                      '${pct.round()}%',
                      textAlign: TextAlign.end,
                      style: Theme.of(context).textTheme.labelSmall,
                    ),
                  )
                : null,
            enabled: ready,
            onTap: ready
                ? () => context.push(
                    '/player/${video.id}?formationId=$formationId',
                  )
                : null,
          );
        }),
        if (chapter.documents.isNotEmpty) ...[
          const Divider(),
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 4),
            child: Text(
              'Documents',
              style: Theme.of(context).textTheme.titleSmall,
            ),
          ),
          ...chapter.documents.map((doc) {
            return ListTile(
              leading: const Icon(Icons.description_outlined),
              title: Text(doc.title),
              subtitle: Text(doc.filename),
              onTap: () async {
                final url = ref
                    .read(documentRepositoryProvider)
                    .fileUrl(doc.id);
                final uri = Uri.parse(url);
                final ok = await launchUrl(
                  uri,
                  mode: LaunchMode.externalApplication,
                );
                if (!ok && context.mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(
                      content: Text('Impossible d’ouvrir le document'),
                    ),
                  );
                }
              },
            );
          }),
        ],
      ],
    );
  }
}
