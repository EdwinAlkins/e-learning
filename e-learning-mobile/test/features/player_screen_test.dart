import 'package:e_learning_mobile/config/env.dart';
import 'package:e_learning_mobile/data/models/models.dart';
import 'package:e_learning_mobile/data/repositories/formation_repository.dart';
import 'package:e_learning_mobile/data/repositories/note_repository.dart';
import 'package:e_learning_mobile/data/repositories/progress_repository.dart';
import 'package:e_learning_mobile/data/repositories/video_repository.dart';
import 'package:e_learning_mobile/features/player/providers/media_controller.dart';
import 'package:e_learning_mobile/features/player/providers/media_controller_provider.dart';
import 'package:e_learning_mobile/features/player/providers/player_context_provider.dart';
import 'package:e_learning_mobile/features/player/screens/player_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

/// Clé de l'écran testé : le type explicite est nécessaire pour que le littéral
/// prenne bien le `String?` de `PlayerArgs`.
const PlayerArgs _args = (videoId: 'v1', formationId: 'f1');

VideoItem _video(
  String id,
  String title, {
  int position = 0,
  String processingStatus = MediaStatus.ready,
  String summaryStatus = MediaStatus.none,
  double duration = 600,
  List<BackgroundJob> activeJobs = const [],
}) {
  return VideoItem(
    id: id,
    title: title,
    duration: duration,
    position: position,
    kind: 'video',
    processingStatus: processingStatus,
    transcriptionStatus: MediaStatus.none,
    summaryStatus: summaryStatus,
    activeJobs: activeJobs,
  );
}

Formation _formation(List<VideoItem> videos) {
  return Formation(
    id: 'f1',
    name: 'Formation test',
    chapters: [
      ChapterItem(
        id: 'c1',
        name: 'Chapitre 1',
        position: 0,
        videos: videos,
        documents: const [],
      ),
    ],
  );
}

class _FakeFormationRepository implements FormationRepository {
  _FakeFormationRepository(this.formation);

  Formation formation;
  int getByIdCalls = 0;

  @override
  Future<List<Formation>> list() async => [formation];

  @override
  Future<Formation> getById(String id) async {
    getByIdCalls++;
    return formation;
  }

  @override
  Future<AskFormationResponse> ask(String formationId, String question) async =>
      throw UnimplementedError();
}

class _FakeProgressRepository implements ProgressRepository {
  final List<({String videoId, double position})> saved = [];

  @override
  Future<double?> getVideoProgress(String videoId) async => null;

  @override
  Future<void> saveVideoProgress(String videoId, double position) async {
    saved.add((videoId: videoId, position: position));
  }

  @override
  Future<FormationProgress> getFormationProgress(String formationId) async =>
      throw UnimplementedError();

  @override
  Future<Map<String, FormationProgress>> getAllFormationsProgress() async =>
      const {};
}

class _FakeVideoRepository implements VideoRepository {
  final List<String> conversionsStarted = [];

  @override
  String streamUrl(String videoId) => 'http://api.test/videos/$videoId/stream';

  @override
  Future<VideoItem> startConversion(String videoId) async {
    conversionsStarted.add(videoId);
    return _video(videoId, 'inchangé');
  }

  @override
  Future<VideoItem> startTranscription(String videoId) async =>
      throw UnimplementedError();

  @override
  Future<VideoItem> generateSummary(String videoId) async =>
      throw UnimplementedError();

  @override
  Future<String?> getSummary(String videoId) async => null;

  @override
  Future<String> updateSummary(String videoId, String summary) async =>
      throw UnimplementedError();
}

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

/// Flutter valide les transitions de cycle de vie : le passage en arrière-plan
/// et le retour au premier plan doivent suivre la séquence réelle.
Future<void> _lifecycle(
  WidgetTester tester,
  List<AppLifecycleState> states,
) async {
  for (final state in states) {
    tester.binding.handleAppLifecycleStateChanged(state);
    await _settle(tester);
  }
}

const _toBackground = [
  AppLifecycleState.inactive,
  AppLifecycleState.hidden,
  AppLifecycleState.paused,
];

const _toForeground = [
  AppLifecycleState.hidden,
  AppLifecycleState.inactive,
  AppLifecycleState.resumed,
];

/// `pumpAndSettle` ne convient pas dès qu'un job IA tourne : le timer de
/// polling replanifie une frame toutes les 3 s et l'arbre ne se stabilise
/// jamais. On pompe donc un nombre borné de frames.
Future<void> _settle(WidgetTester tester, [int frames = 6]) async {
  for (var i = 0; i < frames; i++) {
    await tester.pump(Duration.zero);
  }
}

void main() {
  late _FakeFormationRepository formations;
  late _FakeProgressRepository progress;
  late _FakeVideoRepository videos;

  setUp(() {
    Env.apiUrl = 'http://api.test';
    progress = _FakeProgressRepository();
    videos = _FakeVideoRepository();
  });

  /// Monte le lecteur derrière un vrai `GoRouter`, pour que la navigation
  /// précédent/suivant s'exerce comme en production.
  Future<void> pumpPlayer(
    WidgetTester tester, {
    required String videoId,
    MediaController? media,
  }) async {
    // Format téléphone en portrait : la surface de test par défaut (800×600)
    // basculerait sur la mise en page paysage à deux colonnes.
    tester.view.devicePixelRatio = 1;
    tester.view.physicalSize = const Size(411, 1000);
    addTearDown(tester.view.reset);

    final router = GoRouter(
      initialLocation: '/player/$videoId?formationId=f1',
      routes: [
        GoRoute(
          path: '/player/:videoId',
          builder: (context, state) => PlayerScreen(
            videoId: state.pathParameters['videoId']!,
            formationId: state.uri.queryParameters['formationId'],
          ),
        ),
      ],
    );
    addTearDown(router.dispose);

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          formationRepositoryProvider.overrideWithValue(formations),
          progressRepositoryProvider.overrideWithValue(progress),
          videoRepositoryProvider.overrideWithValue(videos),
          noteRepositoryProvider.overrideWithValue(_EmptyNoteRepository()),
          if (media != null)
            mediaControllerProvider(_args).overrideWith((ref) async => media),
        ],
        child: MaterialApp.router(routerConfig: router),
      ),
    );
    await _settle(tester);
  }

  testWidgets('conversion en cours : message d’attente et pas de lecteur', (
    tester,
  ) async {
    formations = _FakeFormationRepository(
      _formation([
        _video(
          'v1',
          'Ma vidéo',
          processingStatus: MediaStatus.processing,
          activeJobs: const [
            BackgroundJob(
              id: 'j1',
              kind: JobKind.mediaConversion,
              status: 'running',
              progress: 42,
              message: 'Encodage en 720p',
            ),
          ],
        ),
      ]),
    );

    await pumpPlayer(tester, videoId: 'v1');

    expect(find.text('Conversion du média en cours… 42%'), findsOneWidget);
    expect(find.text('Encodage en 720p'), findsOneWidget);
    expect(find.byType(CircularProgressIndicator), findsWidgets);
  });

  testWidgets('échec de conversion : relance via le bouton dédié', (
    tester,
  ) async {
    formations = _FakeFormationRepository(
      _formation([
        _video('v1', 'Ma vidéo', processingStatus: MediaStatus.failed),
      ]),
    );

    await pumpPlayer(tester, videoId: 'v1');

    expect(find.text('La conversion du média a échoué.'), findsOneWidget);

    await tester.tap(find.text('Relancer la conversion'));
    await tester.pumpAndSettle();

    expect(videos.conversionsStarted, ['v1']);
  });

  testWidgets('la barre précédent/suivant navigue dans la formation', (
    tester,
  ) async {
    // Médias non convertis : la navigation ne dépend pas de la lecture, et on
    // évite d'instancier un vrai backend média dans un test.
    formations = _FakeFormationRepository(
      _formation([
        _video(
          'v1',
          'Première',
          position: 0,
          processingStatus: MediaStatus.failed,
        ),
        _video(
          'v2',
          'Deuxième',
          position: 1,
          processingStatus: MediaStatus.failed,
        ),
        _video(
          'v3',
          'Troisième',
          position: 2,
          processingStatus: MediaStatus.failed,
        ),
      ]),
    );

    await pumpPlayer(tester, videoId: 'v2');

    // Titres des voisins portés par les boutons.
    expect(find.widgetWithText(TextButton, 'Première'), findsOneWidget);
    expect(find.widgetWithText(FilledButton, 'Troisième'), findsOneWidget);

    await tester.tap(find.widgetWithText(FilledButton, 'Troisième'));
    await tester.pumpAndSettle();

    // On est bien sur v3 : son suivant n'existe plus, le précédent est v2.
    expect(find.widgetWithText(TextButton, 'Deuxième'), findsOneWidget);
    final next = tester.widget<FilledButton>(
      find.widgetWithText(FilledButton, 'Suivant'),
    );
    expect(next.onPressed, isNull);
  });

  testWidgets('une seule vidéo : pas de barre de navigation', (tester) async {
    formations = _FakeFormationRepository(
      _formation([_video('v1', 'Seule', processingStatus: MediaStatus.failed)]),
    );

    await pumpPlayer(tester, videoId: 'v1');

    expect(find.byType(BottomAppBar), findsNothing);
  });

  testWidgets('passage en arrière-plan : le polling des jobs IA s’arrête', (
    tester,
  ) async {
    formations = _FakeFormationRepository(
      _formation([
        _video(
          'v1',
          'Ma vidéo',
          processingStatus: MediaStatus.processing,
          activeJobs: const [
            BackgroundJob(
              id: 'j1',
              kind: JobKind.mediaConversion,
              status: 'running',
            ),
          ],
        ),
      ]),
    );

    await pumpPlayer(tester, videoId: 'v1');
    final afterMount = formations.getByIdCalls;

    // Au premier plan, le timer rafraîchit le contexte toutes les 3 s.
    await tester.pump(const Duration(seconds: 4));
    await _settle(tester);
    expect(formations.getByIdCalls, greaterThan(afterMount));

    final afterForeground = formations.getByIdCalls;
    await _lifecycle(tester, _toBackground);

    await tester.pump(const Duration(seconds: 10));
    await _settle(tester);
    expect(
      formations.getByIdCalls,
      afterForeground,
      reason: 'aucune requête ne doit partir en arrière-plan',
    );

    // Retour au premier plan : le polling reprend.
    await _lifecycle(tester, _toForeground);
    await tester.pump(const Duration(seconds: 4));
    await _settle(tester);
    expect(formations.getByIdCalls, greaterThan(afterForeground));
  });

  testWidgets('passage en arrière-plan : la position de lecture est écrite', (
    tester,
  ) async {
    formations = _FakeFormationRepository(
      _formation([_video('v1', 'Ma vidéo')]),
    );

    // Contrôleur non initialisé : `seekTo` ne touche aucun backend natif mais
    // positionne bien la lecture, ce qui suffit à vérifier le flush (PLAY-08).
    final controller = MediaController(
      videoId: 'v1',
      isAudio: false,
      streamUrl: 'http://api.test/videos/v1/stream',
      headers: const {},
      fallbackDuration: 600,
      onSaveProgress: (position) => progress.saveVideoProgress('v1', position),
    );
    addTearDown(controller.dispose);
    await controller.seekTo(42);

    await pumpPlayer(tester, videoId: 'v1', media: controller);

    expect(find.text('00:42 / 10:00'), findsOneWidget);
    expect(progress.saved, isEmpty);

    await _lifecycle(tester, _toBackground);

    // Une seule écriture malgré les trois transitions inactive/hidden/paused.
    expect(progress.saved, hasLength(1));
    expect(progress.saved.single.position, 42);
  });

  testWidgets('vidéo introuvable : message et bouton Réessayer', (
    tester,
  ) async {
    formations = _FakeFormationRepository(_formation([_video('v1', 'Autre')]));

    await pumpPlayer(tester, videoId: 'inconnue');

    expect(
      find.textContaining('Vidéo introuvable dans cette formation.'),
      findsOneWidget,
    );
    expect(find.widgetWithText(FilledButton, 'Réessayer'), findsOneWidget);
  });
}
