import 'package:dio/dio.dart';
import 'package:e_learning_mobile/data/models/models.dart';
import 'package:e_learning_mobile/data/repositories/video_repository.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

class _MockDio extends Mock implements Dio {}

Response<dynamic> _response(String path, dynamic data, {int status = 200}) {
  return Response<dynamic>(
    requestOptions: RequestOptions(path: path),
    data: data,
    statusCode: status,
  );
}

void main() {
  late _MockDio dio;
  late VideoRepository repository;

  setUp(() {
    dio = _MockDio();
    repository = VideoRepository(dio, 'http://api.test');
  });

  test('streamUrl pointe vers la route de stream absolue', () {
    expect(repository.streamUrl('v1'), 'http://api.test/videos/v1/stream');
  });

  test('getSummary renvoie null quand le résumé n’existe pas (404)', () async {
    when(() => dio.get('/videos/v1/summary')).thenThrow(
      DioException(
        requestOptions: RequestOptions(path: '/videos/v1/summary'),
        response: Response<dynamic>(
          requestOptions: RequestOptions(path: '/videos/v1/summary'),
          statusCode: 404,
        ),
      ),
    );

    expect(await repository.getSummary('v1'), isNull);
  });

  test('getSummary renvoie le texte quand il est disponible', () async {
    when(() => dio.get('/videos/v1/summary')).thenAnswer(
      (_) async => _response('/videos/v1/summary', {'summary': '# Résumé'}),
    );

    expect(await repository.getSummary('v1'), '# Résumé');
  });

  test('startTranscription renvoie la vidéo mise à jour', () async {
    when(() => dio.post('/videos/v1/transcription')).thenAnswer(
      (_) async => _response('/videos/v1/transcription', {
        'id': 'v1',
        'title': 'Média',
        'transcription_status': 'processing',
        'active_jobs': [
          {'id': 'j1', 'kind': 'transcription', 'status': 'queued'},
        ],
      }, status: 202),
    );

    final video = await repository.startTranscription('v1');

    expect(video.transcriptionStatus, MediaStatus.processing);
    expect(video.activeJob(JobKind.transcription), isNotNull);
  });

  test('generateSummary poste sur la route de génération', () async {
    when(() => dio.post('/videos/v1/summary/generate')).thenAnswer(
      (_) async => _response('/videos/v1/summary/generate', {
        'id': 'v1',
        'title': 'Média',
        'summary_status': 'processing',
      }, status: 202),
    );

    final video = await repository.generateSummary('v1');

    expect(video.summaryStatus, MediaStatus.processing);
    verify(() => dio.post('/videos/v1/summary/generate')).called(1);
  });
}
