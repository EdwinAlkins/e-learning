import 'package:flutter/material.dart';
import 'package:flutter_markdown_plus/flutter_markdown_plus.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/utils/time_format.dart';
import '../../../data/models/models.dart';
import '../../../data/repositories/note_repository.dart';
import '../../player/providers/media_controller.dart';
import '../providers/notes_provider.dart';
import 'note_composer.dart';

/// Onglet « Notes » du lecteur : création + liste synchronisée au média.
class NotesPanel extends ConsumerStatefulWidget {
  const NotesPanel({super.key, required this.videoId, required this.playback});

  final String videoId;
  final PlaybackHandle? playback;

  @override
  ConsumerState<NotesPanel> createState() => _NotesPanelState();
}

class _NotesPanelState extends ConsumerState<NotesPanel>
    with AutomaticKeepAliveClientMixin {
  @override
  bool get wantKeepAlive => true;

  Future<void> _seekTo(double timecode) async {
    final playback = widget.playback;
    if (playback == null) return;
    await playback.seekTo(timecode);
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Lecture à ${formatTimecode(timecode)}'),
          duration: const Duration(seconds: 1),
        ),
      );
    }
  }

  Future<void> _delete(Note note) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Supprimer cette note ?'),
        content: const Text('Cette action est définitive.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Annuler'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Supprimer'),
          ),
        ],
      ),
    );
    if (confirmed != true) return;

    try {
      await ref.read(noteRepositoryProvider).delete(note.id);
      ref.invalidate(notesProvider(widget.videoId));
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('Échec de la suppression : $e')));
      }
    }
  }

  Future<void> _update(Note note, String content) async {
    try {
      await ref.read(noteRepositoryProvider).update(note.id, content);
      ref.invalidate(notesProvider(widget.videoId));
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('Échec de la mise à jour : $e')));
      }
      rethrow;
    }
  }

  @override
  Widget build(BuildContext context) {
    super.build(context);
    final notes = ref.watch(notesProvider(widget.videoId));

    return Column(
      children: [
        NoteComposer(videoId: widget.videoId, playback: widget.playback),
        Expanded(
          child: notes.when(
            loading: () => const Center(child: CircularProgressIndicator()),
            error: (error, _) => _NotesError(
              message: '$error',
              onRetry: () => ref.invalidate(notesProvider(widget.videoId)),
            ),
            data: (items) {
              if (items.isEmpty) {
                return const _NotesEmpty();
              }
              return RefreshIndicator(
                onRefresh: () async =>
                    ref.invalidate(notesProvider(widget.videoId)),
                child: ListView.builder(
                  keyboardDismissBehavior:
                      ScrollViewKeyboardDismissBehavior.onDrag,
                  padding: const EdgeInsets.fromLTRB(12, 4, 12, 24),
                  itemCount: items.length,
                  itemBuilder: (context, index) {
                    final note = items[index];
                    return _NoteTile(
                      key: ValueKey(note.id),
                      note: note,
                      canSeek: widget.playback != null,
                      onSeek: () => _seekTo(note.timecode),
                      onDelete: () => _delete(note),
                      onSave: (content) => _update(note, content),
                    );
                  },
                ),
              );
            },
          ),
        ),
      ],
    );
  }
}

class _NoteTile extends StatefulWidget {
  const _NoteTile({
    super.key,
    required this.note,
    required this.canSeek,
    required this.onSeek,
    required this.onDelete,
    required this.onSave,
  });

  final Note note;
  final bool canSeek;
  final VoidCallback onSeek;
  final VoidCallback onDelete;
  final Future<void> Function(String content) onSave;

  @override
  State<_NoteTile> createState() => _NoteTileState();
}

class _NoteTileState extends State<_NoteTile> {
  TextEditingController? _editController;
  bool _saving = false;

  @override
  void dispose() {
    _editController?.dispose();
    super.dispose();
  }

  void _startEdit() {
    setState(() {
      _editController = TextEditingController(text: widget.note.content);
    });
  }

  void _cancelEdit() {
    _editController?.dispose();
    setState(() => _editController = null);
  }

  Future<void> _save() async {
    final content = _editController?.text.trim() ?? '';
    if (content.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Le contenu ne peut pas être vide')),
      );
      return;
    }
    setState(() => _saving = true);
    try {
      await widget.onSave(content);
      if (mounted) _cancelEdit();
    } catch (_) {
      // Message déjà affiché par le panneau parent.
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final note = widget.note;
    final editing = _editController != null;

    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: Padding(
        padding: const EdgeInsets.fromLTRB(12, 8, 8, 12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                ActionChip(
                  avatar: const Icon(Icons.schedule, size: 16),
                  label: Text(formatTimecode(note.timecode)),
                  onPressed: widget.canSeek && !editing ? widget.onSeek : null,
                  tooltip: widget.canSeek
                      ? 'Reprendre la lecture à ce moment'
                      : null,
                  visualDensity: VisualDensity.compact,
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    formatDateTime(note.createdAt),
                    style: theme.textTheme.bodySmall,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                if (!editing)
                  PopupMenuButton<String>(
                    tooltip: 'Actions',
                    onSelected: (value) {
                      if (value == 'edit') _startEdit();
                      if (value == 'delete') widget.onDelete();
                    },
                    itemBuilder: (context) => const [
                      PopupMenuItem(
                        value: 'edit',
                        child: ListTile(
                          dense: true,
                          leading: Icon(Icons.edit_outlined),
                          title: Text('Modifier'),
                        ),
                      ),
                      PopupMenuItem(
                        value: 'delete',
                        child: ListTile(
                          dense: true,
                          leading: Icon(Icons.delete_outline),
                          title: Text('Supprimer'),
                        ),
                      ),
                    ],
                  ),
              ],
            ),
            const SizedBox(height: 4),
            if (editing)
              Padding(
                padding: const EdgeInsets.only(right: 4),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    TextField(
                      controller: _editController,
                      autofocus: true,
                      minLines: 3,
                      maxLines: 10,
                      // Marge sous le curseur pour que la liste défile assez
                      // haut et laisse voir les boutons Annuler / Enregistrer.
                      scrollPadding: const EdgeInsets.fromLTRB(20, 20, 20, 140),
                      decoration: const InputDecoration(
                        border: OutlineInputBorder(),
                      ),
                    ),
                    const SizedBox(height: 8),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.end,
                      children: [
                        TextButton(
                          onPressed: _saving ? null : _cancelEdit,
                          child: const Text('Annuler'),
                        ),
                        const SizedBox(width: 8),
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
              )
            else
              Padding(
                padding: const EdgeInsets.only(left: 4, right: 8),
                child: MarkdownBody(data: note.content, selectable: true),
              ),
          ],
        ),
      ),
    );
  }
}

class _NotesEmpty extends StatelessWidget {
  const _NotesEmpty();

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(32),
      children: [
        Icon(
          Icons.sticky_note_2_outlined,
          size: 48,
          color: Theme.of(context).colorScheme.outline,
        ),
        const SizedBox(height: 12),
        Text(
          'Aucune note pour ce média.\n'
          'Mettez la lecture en pause et notez ce qui compte.',
          textAlign: TextAlign.center,
          style: Theme.of(context).textTheme.bodyMedium,
        ),
      ],
    );
  }
}

class _NotesError extends StatelessWidget {
  const _NotesError({required this.message, required this.onRetry});

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
            const SizedBox(height: 12),
            FilledButton.tonal(
              onPressed: onRetry,
              child: const Text('Réessayer'),
            ),
          ],
        ),
      ),
    );
  }
}
