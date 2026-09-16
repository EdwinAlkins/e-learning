import 'package:e_learning_mobile/config/env.dart';
import 'package:e_learning_mobile/data/models/models.dart';
import 'package:e_learning_mobile/data/repositories/note_repository.dart';
import 'package:e_learning_mobile/features/auth/screens/auth_screen.dart';
import 'package:e_learning_mobile/features/notes/widgets/notes_panel.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

/// Écran de téléphone dont la moitié basse est mangée par le clavier.
const _screen = Size(360, 640);
const _keyboardHeight = 320.0;
const _visibleHeight = 640.0 - _keyboardHeight;

class _EmptyNoteRepository implements NoteRepository {
  @override
  Future<List<Note>> list(String videoId) async => const [];

  @override
  Future<Note> create(String videoId, double timecode, String content) async =>
      throw UnimplementedError();

  @override
  Future<Note> update(String noteId, String content) async =>
      throw UnimplementedError();

  @override
  Future<void> delete(String noteId) async => throw UnimplementedError();
}

/// Injecte l'inset clavier sous `MaterialApp`, comme le fait la plateforme.
Widget _withKeyboard(Widget home) {
  return MaterialApp(
    home: home,
    builder: (context, child) => MediaQuery(
      data: MediaQuery.of(context)
          .copyWith(viewInsets: const EdgeInsets.only(bottom: _keyboardHeight)),
      child: child!,
    ),
  );
}

void main() {
  setUp(() {
    Env.apiUrl = 'http://api.test';
  });

  Future<void> useSmallScreen(WidgetTester tester) async {
    tester.view.devicePixelRatio = 1;
    tester.view.physicalSize = _screen;
    addTearDown(tester.view.reset);
  }

  testWidgets('écran de connexion : rien ne déborde, tout reste atteignable', (
    tester,
  ) async {
    await useSmallScreen(tester);
    await tester.pumpWidget(
      ProviderScope(child: _withKeyboard(const AuthScreen())),
    );
    await tester.pump();

    expect(tester.takeException(), isNull);

    // Le champ UID et le bouton de validation sont accessibles au défilement.
    await tester.ensureVisible(find.text('Restaurer'));
    await tester.pump();
    expect(
      tester.getRect(find.text('Restaurer')).bottom,
      lessThan(_visibleHeight),
    );
    expect(tester.takeException(), isNull);
  });

  testWidgets('panneau notes : la saisie et son bouton restent visibles', (
    tester,
  ) async {
    await useSmallScreen(tester);
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          noteRepositoryProvider.overrideWithValue(_EmptyNoteRepository()),
        ],
        child: _withKeyboard(
          const Scaffold(body: NotesPanel(videoId: 'v1', playback: null)),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(tester.takeException(), isNull);
    expect(
      tester.getRect(find.text('Ajouter')).bottom,
      lessThan(_visibleHeight),
    );
  });
}
