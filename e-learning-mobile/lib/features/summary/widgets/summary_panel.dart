import 'package:flutter/material.dart';
import 'package:flutter_markdown_plus/flutter_markdown_plus.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../data/models/models.dart';
import '../../../data/repositories/video_repository.dart';
import '../providers/summary_provider.dart';

/// Onglet « Résumé » : consultation, édition Markdown et (re)génération.
class SummaryPanel extends ConsumerStatefulWidget {
  const SummaryPanel({
    super.key,
    required this.video,
    required this.busy,
    required this.onGenerate,
  });

  final VideoItem video;
  final bool busy;
  final VoidCallback onGenerate;

  @override
  ConsumerState<SummaryPanel> createState() => _SummaryPanelState();
}

class _SummaryPanelState extends ConsumerState<SummaryPanel>
    with AutomaticKeepAliveClientMixin {
  @override
  bool get wantKeepAlive => true;

  TextEditingController? _editController;
  bool _previewing = false;
  bool _saving = false;

  @override
  void dispose() {
    _editController?.dispose();
    super.dispose();
  }

  void _startEdit(String initial) {
    setState(() {
      _editController = TextEditingController(text: initial);
      _previewing = false;
    });
  }

  void _cancelEdit() {
    _editController?.dispose();
    setState(() {
      _editController = null;
      _previewing = false;
    });
  }

  Future<void> _save() async {
    final content = _editController?.text.trim() ?? '';
    if (content.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Le résumé ne peut pas être vide')),
      );
      return;
    }
    setState(() => _saving = true);
    try {
      await ref
          .read(videoRepositoryProvider)
          .updateSummary(widget.video.id, content);
      ref.invalidate(summaryProvider(widget.video.id));
      if (mounted) _cancelEdit();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Échec de l’enregistrement : $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    super.build(context);
    final video = widget.video;

    if (video.summaryStatus == MediaStatus.processing) {
      final job = video.activeJob(JobKind.summary);
      return _Centered(
        children: [
          const CircularProgressIndicator(),
          const SizedBox(height: 16),
          Text(
            job?.label('Génération du résumé en cours…') ??
                'Génération du résumé en cours…',
          ),
          if (job?.message != null && job!.message!.isNotEmpty) ...[
            const SizedBox(height: 8),
            Text(job.message!, textAlign: TextAlign.center),
          ],
        ],
      );
    }

    if (video.summaryStatus == MediaStatus.failed) {
      return _Centered(
        children: [
          const Icon(Icons.error_outline, size: 40),
          const SizedBox(height: 12),
          const Text(
            'La génération du résumé a échoué.',
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 12),
          FilledButton.tonalIcon(
            onPressed: widget.busy ? null : widget.onGenerate,
            icon: const Icon(Icons.refresh),
            label: const Text('Relancer la génération'),
          ),
        ],
      );
    }

    if (!video.hasSummary) {
      return _Centered(
        children: [
          Icon(
            Icons.auto_awesome_outlined,
            size: 40,
            color: Theme.of(context).colorScheme.outline,
          ),
          const SizedBox(height: 12),
          Text(
            video.hasTranscription
                ? 'Aucun résumé n’a encore été généré pour ce média.'
                : 'Transcrivez d’abord le média pour pouvoir générer un résumé.',
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 12),
          FilledButton.icon(
            onPressed:
                widget.busy || !video.hasTranscription || !video.isPlayable
                ? null
                : widget.onGenerate,
            icon: const Icon(Icons.auto_awesome),
            label: const Text('Générer le résumé'),
          ),
        ],
      );
    }

    final summary = ref.watch(summaryProvider(video.id));

    return summary.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (error, _) => _Centered(
        children: [
          Text('$error', textAlign: TextAlign.center),
          const SizedBox(height: 12),
          FilledButton.tonal(
            onPressed: () => ref.invalidate(summaryProvider(video.id)),
            child: const Text('Réessayer'),
          ),
        ],
      ),
      data: (text) {
        if (text == null) {
          return _Centered(
            children: [
              const Text('Résumé non disponible.', textAlign: TextAlign.center),
              const SizedBox(height: 12),
              FilledButton.tonalIcon(
                onPressed: widget.busy ? null : widget.onGenerate,
                icon: const Icon(Icons.refresh),
                label: const Text('Générer à nouveau'),
              ),
            ],
          );
        }

        final controller = _editController;
        if (controller != null) {
          return Column(
            children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(12, 8, 12, 0),
                // `Wrap` et non `Row` : sur un écran de téléphone, le sélecteur
                // et les deux boutons ne tiennent pas sur une seule ligne.
                child: Wrap(
                  spacing: 8,
                  runSpacing: 4,
                  alignment: WrapAlignment.spaceBetween,
                  crossAxisAlignment: WrapCrossAlignment.center,
                  children: [
                    SegmentedButton<bool>(
                      segments: const [
                        ButtonSegment(value: false, label: Text('Édition')),
                        ButtonSegment(value: true, label: Text('Aperçu')),
                      ],
                      selected: {_previewing},
                      onSelectionChanged: (values) =>
                          setState(() => _previewing = values.first),
                    ),
                    Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        TextButton(
                          onPressed: _saving ? null : _cancelEdit,
                          child: const Text('Annuler'),
                        ),
                        const SizedBox(width: 4),
                        FilledButton(
                          onPressed: _saving ? null : _save,
                          child: _saving
                              ? const SizedBox(
                                  width: 16,
                                  height: 16,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2,
                                  ),
                                )
                              : const Text('Enregistrer'),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              Expanded(
                child: Padding(
                  padding: const EdgeInsets.all(12),
                  child: _previewing
                      ? Markdown(
                          data: controller.text,
                          padding: EdgeInsets.zero,
                          selectable: true,
                        )
                      : TextField(
                          controller: controller,
                          maxLines: null,
                          expands: true,
                          textAlignVertical: TextAlignVertical.top,
                          decoration: const InputDecoration(
                            border: OutlineInputBorder(),
                            alignLabelWithHint: true,
                          ),
                        ),
                ),
              ),
            ],
          );
        }

        return Column(
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(12, 4, 4, 0),
              child: Row(
                children: [
                  Text(
                    'Résumé',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const Spacer(),
                  TextButton.icon(
                    onPressed: widget.busy ? null : widget.onGenerate,
                    icon: const Icon(Icons.refresh, size: 18),
                    label: const Text('Régénérer'),
                  ),
                  IconButton(
                    tooltip: 'Éditer le résumé',
                    onPressed: () => _startEdit(text),
                    icon: const Icon(Icons.edit_outlined),
                  ),
                ],
              ),
            ),
            Expanded(
              child: Markdown(
                data: text.isEmpty ? '_Résumé vide._' : text,
                padding: const EdgeInsets.fromLTRB(16, 8, 16, 32),
                selectable: true,
              ),
            ),
          ],
        );
      },
    );
  }
}

class _Centered extends StatelessWidget {
  const _Centered({required this.children});

  final List<Widget> children;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(mainAxisSize: MainAxisSize.min, children: children),
      ),
    );
  }
}
