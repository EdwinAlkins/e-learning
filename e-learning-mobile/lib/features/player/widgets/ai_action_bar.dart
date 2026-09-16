import 'package:flutter/material.dart';

import '../../../data/models/models.dart';

/// Statuts IA + actions (transcrire / générer / régénérer) — PLAY-11 à PLAY-16.
class AiActionBar extends StatelessWidget {
  const AiActionBar({
    super.key,
    required this.video,
    required this.busy,
    required this.onTranscribe,
    required this.onGenerateSummary,
    required this.onOpenSummary,
    this.errorMessage,
  });

  final VideoItem video;
  final bool busy;
  final VoidCallback onTranscribe;
  final VoidCallback onGenerateSummary;
  final VoidCallback onOpenSummary;
  final String? errorMessage;

  @override
  Widget build(BuildContext context) {
    final transcriptionJob = video.activeJob(JobKind.transcription);
    final summaryJob = video.activeJob(JobKind.summary);
    final transcribing = video.transcriptionStatus == MediaStatus.processing;
    final generating = video.summaryStatus == MediaStatus.processing;

    final notices = <Widget>[
      if (errorMessage != null)
        _Notice(message: errorMessage!, severity: _Severity.error),
      if (video.transcriptionStatus == MediaStatus.failed)
        const _Notice(
          message: 'Échec de la transcription. Vous pouvez la relancer.',
          severity: _Severity.error,
        ),
      if (video.summaryStatus == MediaStatus.failed)
        const _Notice(
          message: 'Échec de la génération du résumé.',
          severity: _Severity.error,
        ),
      if (!video.hasTranscription &&
          !transcribing &&
          video.transcriptionStatus != MediaStatus.failed &&
          !video.hasSummary)
        const _Notice(
          message:
              'Une transcription est nécessaire avant de générer le résumé.',
          severity: _Severity.info,
        ),
    ];

    return Padding(
      padding: const EdgeInsets.fromLTRB(12, 4, 12, 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Wrap(
            spacing: 8,
            runSpacing: 8,
            crossAxisAlignment: WrapCrossAlignment.center,
            children: [
              if (!video.hasTranscription)
                OutlinedButton.icon(
                  onPressed: busy || transcribing || !video.isPlayable
                      ? null
                      : onTranscribe,
                  icon: _icon(
                    transcribing || busy,
                    Icons.record_voice_over_outlined,
                  ),
                  label: Text(
                    transcribing
                        ? (transcriptionJob?.label('Transcription…') ??
                              'Transcription…')
                        : 'Transcrire',
                  ),
                ),
              if (!video.hasSummary)
                OutlinedButton.icon(
                  onPressed:
                      busy ||
                          generating ||
                          !video.isPlayable ||
                          !video.hasTranscription
                      ? null
                      : onGenerateSummary,
                  icon: _icon(generating || busy, Icons.auto_awesome_outlined),
                  label: Text(
                    generating
                        ? (summaryJob?.label('Génération…') ?? 'Génération…')
                        : 'Générer le résumé',
                  ),
                ),
              if (video.hasSummary) ...[
                FilledButton.tonalIcon(
                  onPressed: onOpenSummary,
                  icon: const Icon(Icons.article_outlined),
                  label: const Text('Résumé'),
                ),
                TextButton.icon(
                  onPressed: busy || generating || !video.isPlayable
                      ? null
                      : onGenerateSummary,
                  icon: _icon(generating || busy, Icons.refresh),
                  label: const Text('Régénérer'),
                ),
              ],
            ],
          ),
          if (notices.isNotEmpty) ...[const SizedBox(height: 8), ...notices],
        ],
      ),
    );
  }

  Widget _icon(bool loading, IconData icon) {
    if (loading) {
      return const SizedBox(
        width: 16,
        height: 16,
        child: CircularProgressIndicator(strokeWidth: 2),
      );
    }
    return Icon(icon, size: 18);
  }
}

enum _Severity { info, error }

class _Notice extends StatelessWidget {
  const _Notice({required this.message, required this.severity});

  final String message;
  final _Severity severity;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final isError = severity == _Severity.error;
    final background = isError
        ? scheme.errorContainer
        : scheme.surfaceContainerHighest;
    final foreground = isError
        ? scheme.onErrorContainer
        : scheme.onSurfaceVariant;

    return Container(
      width: double.infinity,
      margin: const EdgeInsets.only(bottom: 6),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: background,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: [
          Icon(
            isError ? Icons.error_outline : Icons.info_outline,
            size: 18,
            color: foreground,
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              message,
              style: Theme.of(context).textTheme.bodySmall
                  ?.copyWith(color: foreground),
            ),
          ),
        ],
      ),
    );
  }
}
