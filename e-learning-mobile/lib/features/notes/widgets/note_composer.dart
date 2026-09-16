import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/utils/time_format.dart';
import '../../../data/repositories/note_repository.dart';
import '../../player/providers/media_controller.dart';
import '../providers/notes_provider.dart';

/// Création d'une note liée au temps courant du lecteur (NOTE-01, NOTE-02).
class NoteComposer extends ConsumerStatefulWidget {
  const NoteComposer({
    super.key,
    required this.videoId,
    required this.playback,
  });

  final String videoId;

  /// `null` tant que le média n'est pas lisible : la note est alors créée à 0.
  final PlaybackHandle? playback;

  @override
  ConsumerState<NoteComposer> createState() => _NoteComposerState();
}

class _NoteComposerState extends ConsumerState<NoteComposer> {
  final _controller = TextEditingController();
  bool _saving = false;
  bool _hasContent = false;

  @override
  void initState() {
    super.initState();
    _controller.addListener(() {
      final hasContent = _controller.text.trim().isNotEmpty;
      if (hasContent != _hasContent) {
        setState(() => _hasContent = hasContent);
      }
    });
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _create() async {
    final content = _controller.text.trim();
    if (content.isEmpty) return;

    setState(() => _saving = true);
    final timecode = widget.playback?.positionSeconds ?? 0;
    try {
      await ref
          .read(noteRepositoryProvider)
          .create(widget.videoId, timecode, content);
      _controller.clear();
      ref.invalidate(notesProvider(widget.videoId));
      if (mounted) {
        FocusScope.of(context).unfocus();
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Note ajoutée à ${formatTimecode(timecode)}'),
            duration: const Duration(seconds: 2),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text('Échec de la création : $e')));
      }
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final playback = widget.playback;

    return Card(
      margin: const EdgeInsets.fromLTRB(12, 12, 12, 4),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            TextField(
              controller: _controller,
              minLines: 2,
              maxLines: 6,
              textCapitalization: TextCapitalization.sentences,
              decoration: const InputDecoration(
                labelText: 'Ajouter une note',
                hintText: 'Texte ou Markdown léger…',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                Expanded(
                  child: playback == null
                      ? Text(
                          'Média non lisible : note non horodatée',
                          style: Theme.of(context).textTheme.bodySmall,
                        )
                      : ListenableBuilder(
                          listenable: playback,
                          builder: (context, _) => Text(
                            'Temps actuel : '
                            '${formatTimecode(playback.positionSeconds)}',
                            style: Theme.of(context).textTheme.bodySmall,
                          ),
                        ),
                ),
                const SizedBox(width: 8),
                FilledButton.icon(
                  onPressed: _saving || !_hasContent ? null : _create,
                  icon: _saving
                      ? const SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.add, size: 18),
                  label: Text(
                    playback == null ? 'Ajouter' : 'Lier au temps actuel',
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
