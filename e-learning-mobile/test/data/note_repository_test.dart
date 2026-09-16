import 'package:dio/dio.dart';
import 'package:e_learning_mobile/data/repositories/note_repository.dart';
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
  late NoteRepository repository;

  setUp(() {
    dio = _MockDio();
    repository = NoteRepository(dio);
  });

  test('list trie les notes par timecode croissant', () async {
    when(() => dio.get('/notes/v1')).thenAnswer(
      (_) async => _response('/notes/v1', [
        {'id': '2', 'video_id': 'v1', 'timecode': 120, 'content': 'plus tard'},
        {'id': '1', 'video_id': 'v1', 'timecode': 30, 'content': 'plus tôt'},
      ]),
    );

    final notes = await repository.list('v1');

    expect(notes.map((n) => n.id).toList(), ['1', '2']);
  });

  test('create envoie le timecode et le contenu', () async {
    when(() => dio.post('/notes/v1', data: any(named: 'data'))).thenAnswer(
      (_) async => _response('/notes/v1', {
        'id': '9',
        'video_id': 'v1',
        'timecode': 42.5,
        'content': 'ma note',
      }, status: 201),
    );

    final note = await repository.create('v1', 42.5, 'ma note');

    expect(note.id, '9');
    final captured =
        verify(() => dio.post('/notes/v1', data: captureAny(named: 'data')))
                .captured
                .single
            as Map<String, dynamic>;
    expect(captured['timecode'], 42.5);
    expect(captured['content'], 'ma note');
  });

  test('les erreurs réseau sont converties en ApiException lisible', () async {
    when(() => dio.get('/notes/v1')).thenThrow(
      DioException(
        requestOptions: RequestOptions(path: '/notes/v1'),
        response: Response<dynamic>(
          requestOptions: RequestOptions(path: '/notes/v1'),
          statusCode: 500,
          data: {'detail': 'Boom'},
        ),
      ),
    );

    expect(
      () => repository.list('v1'),
      throwsA(predicate((e) => e.toString() == 'Boom')),
    );
  });

  test('delete appelle la route note', () async {
    when(() => dio.delete('/notes/9'))
        .thenAnswer((_) async => _response('/notes/9', null, status: 204));

    await repository.delete('9');

    verify(() => dio.delete('/notes/9')).called(1);
  });
}
