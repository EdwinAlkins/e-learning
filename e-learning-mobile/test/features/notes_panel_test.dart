import 'package:e_learning_mobile/data/models/models.dart';
import 'package:e_learning_mobile/data/repositories/note_repository.dart';
import 'package:e_learning_mobile/features/notes/widgets/notes_panel.dart';
import 'package:e_learning_mobile/features/player/providers/media_controller.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

class _FakeNoteRepository implements NoteRepository {
  _FakeNoteRepository(this.notes);

  List<Note> notes;
  final List<({double timecode, String content})> created = [];
  final List<String> deleted = [];
  final List<({String id, String content})> updated = [];

  @override
  Future<List<Note>> list(String videoId) async =>
      [...notes]..sort((a, b) => a.timecode.compareTo(b.timecode));

  @override
  Future<Note> create(String videoId, double timecode, String content) async {
    created.add((timecode: timecode, content: content));
    final note = Note(
      id: 'new-${created.length}',
      videoId: videoId,
      timecode: timecode,
      content: content,
      createdAt: DateTime(2025, 3, 12, 14, 5),
    );
    notes = [...notes, note];
    return note;
  }

  @override
  Future<Note> update(String noteId, String content) async {
    updated.add((id: noteId, content: content));
    notes = [
      for (final note in notes)
        if (note.id == noteId)
          Note(
            id: note.id,
            videoId: note.videoId,
            timecode: note.timecode,
            content: content,
            createdAt: note.createdAt,
          )
        else
          note,
    ];
    return notes.firstWhere((n) => n.id == noteId);
  }

  @override
  Future<void> delete(String noteId) async {
    deleted.add(noteId);
    notes = notes.where((n) => n.id != noteId).toList();
  }
}

class _FakePlayback extends ChangeNotifier implements PlaybackHandle {
  double _position = 42;
  final List<double> seeks = [];

  @override
  double get positionSeconds => _position;

  @override
  double get durationSeconds => 600;

  @override
  bool get isPlaying => false;

  @override
  Future<void> seekTo(double seconds) async {
    seeks.add(seconds);
    _position = seconds;
    notifyListeners();
  }
}

Note _note(String id, double timecode, String content) => Note(
  id: id,
  videoId: 'v1',
  timecode: timecode,
  content: content,
  createdAt: DateTime(2025, 3, 12, 14, 5),
);

void main() {
  late _FakeNoteRepository repository;
  late _FakePlayback playback;

  Future<void> pumpPanel(WidgetTester tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [noteRepositoryProvider.overrideWithValue(repository)],
        child: MaterialApp(
          home: Scaffold(
            body: NotesPanel(videoId: 'v1', playback: playback),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
  }

  setUp(() {
    repository = _FakeNoteRepository([
      _note('2', 120, 'Deuxième note'),
      _note('1', 30, 'Première note'),
    ]);
    playback = _FakePlayback();
  });

  testWidgets('affiche les notes triées par timecode', (tester) async {
    await pumpPanel(tester);

    expect(find.text('Première note'), findsOneWidget);
    expect(find.text('Deuxième note'), findsOneWidget);

    final first = tester.getTopLeft(find.text('Première note'));
    final second = tester.getTopLeft(find.text('Deuxième note'));
    expect(first.dy, lessThan(second.dy));

    expect(find.text('00:30'), findsOneWidget);
    expect(find.text('02:00'), findsOneWidget);
    expect(find.text('12/03/2025 14:05'), findsNWidgets(2));
  });

  testWidgets('crée une note au temps courant du lecteur', (tester) async {
    await pumpPanel(tester);

    expect(find.text('Temps actuel : 00:42'), findsOneWidget);

    await tester.enterText(find.byType(TextField).first, 'Ma nouvelle note');
    await tester.pump();
    await tester.tap(find.text('Lier au temps actuel'));
    await tester.pumpAndSettle();

    expect(repository.created, hasLength(1));
    expect(repository.created.single.timecode, 42);
    expect(repository.created.single.content, 'Ma nouvelle note');
    expect(find.text('Ma nouvelle note'), findsOneWidget);
  });

  testWidgets('le bouton reste désactivé tant que la note est vide', (
    tester,
  ) async {
    await pumpPanel(tester);

    final button = tester.widget<FilledButton>(
      find.widgetWithText(FilledButton, 'Lier au temps actuel'),
    );
    expect(button.onPressed, isNull);
  });

  testWidgets('un appui sur le timecode déplace la lecture', (tester) async {
    await pumpPanel(tester);

    await tester.tap(find.widgetWithText(ActionChip, '02:00'));
    await tester.pumpAndSettle();

    expect(playback.seeks, [120]);
  });

  testWidgets('la suppression demande confirmation', (tester) async {
    await pumpPanel(tester);

    await tester.tap(find.byType(PopupMenuButton<String>).first);
    await tester.pumpAndSettle();
    await tester.tap(find.text('Supprimer'));
    await tester.pumpAndSettle();

    // Dialogue affiché : rien n'est supprimé tant qu'on annule.
    expect(find.text('Supprimer cette note ?'), findsOneWidget);
    await tester.tap(find.text('Annuler'));
    await tester.pumpAndSettle();
    expect(repository.deleted, isEmpty);

    await tester.tap(find.byType(PopupMenuButton<String>).first);
    await tester.pumpAndSettle();
    await tester.tap(find.text('Supprimer'));
    await tester.pumpAndSettle();
    await tester.tap(find.widgetWithText(FilledButton, 'Supprimer'));
    await tester.pumpAndSettle();

    expect(repository.deleted, ['1']);
    expect(find.text('Première note'), findsNothing);
  });

  testWidgets('l’édition met à jour le contenu', (tester) async {
    await pumpPanel(tester);

    await tester.tap(find.byType(PopupMenuButton<String>).first);
    await tester.pumpAndSettle();
    await tester.tap(find.text('Modifier'));
    await tester.pumpAndSettle();

    await tester.enterText(find.byType(TextField).last, 'Contenu corrigé');
    await tester.tap(find.widgetWithText(FilledButton, 'Enregistrer'));
    await tester.pumpAndSettle();

    expect(repository.updated, hasLength(1));
    expect(repository.updated.single.content, 'Contenu corrigé');
    expect(find.text('Contenu corrigé'), findsOneWidget);
  });
}
