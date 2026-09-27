import 'package:dio/dio.dart';
import 'package:e_learning_mobile/core/network/api_exception.dart';
import 'package:e_learning_mobile/data/repositories/auth_repository.dart';
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
  late AuthRepository repository;

  setUpAll(() => registerFallbackValue(Options()));

  setUp(() {
    dio = _MockDio();
    repository = AuthRepository(dio);
  });

  test('login envoie username/password en form-urlencoded', () async {
    when(
      () => dio.post(
        '/auth/login',
        data: any(named: 'data'),
        options: any(named: 'options'),
      ),
    ).thenAnswer(
      (_) async => _response('/auth/login', {
        'access_token': 'jwt',
        'token_type': 'bearer',
        'expires_in': 604800,
      }),
    );

    final token = await repository.login('ada@example.com', 'secret-pass');

    expect(token, 'jwt');
    final captured = verify(
      () => dio.post(
        '/auth/login',
        data: captureAny(named: 'data'),
        options: captureAny(named: 'options'),
      ),
    ).captured;
    expect(captured[0], {
      'username': 'ada@example.com',
      'password': 'secret-pass',
    });
    expect(
      (captured[1] as Options).contentType,
      Headers.formUrlEncodedContentType,
    );
  });

  test('login refusé : ApiException avec le statut 401', () async {
    when(
      () => dio.post(
        '/auth/login',
        data: any(named: 'data'),
        options: any(named: 'options'),
      ),
    ).thenThrow(
      DioException(
        requestOptions: RequestOptions(path: '/auth/login'),
        response: _response('/auth/login', {
          'detail': 'Identifiants invalides.',
        }, status: 401),
      ),
    );

    await expectLater(
      repository.login('ada@example.com', 'bad'),
      throwsA(
        isA<ApiException>()
            .having((e) => e.statusCode, 'statusCode', 401)
            .having((e) => e.message, 'message', 'Identifiants invalides.'),
      ),
    );
  });

  test(
    'API d’avant les comptes (404 sur /auth/login) : message explicite',
    () async {
      when(
        () => dio.post(
          '/auth/login',
          data: any(named: 'data'),
          options: any(named: 'options'),
        ),
      ).thenThrow(
        DioException(
          requestOptions: RequestOptions(
            path: '/auth/login',
            baseUrl: 'http://192.168.1.19:8000',
          ),
          response: _response('/auth/login', {
            'detail': 'Not Found',
          }, status: 404),
        ),
      );

      await expectLater(
        repository.login('ada@example.com', 'pw'),
        throwsA(
          isA<ApiException>().having(
            (e) => e.message,
            'message',
            allOf(
              contains('ne gère pas la connexion'),
              contains('192.168.1.19'),
            ),
          ),
        ),
      );
    },
  );

  test('me vérifie un jeton explicite via Authorization', () async {
    when(() => dio.get('/auth/me', options: any(named: 'options'))).thenAnswer(
      (_) async => _response('/auth/me', {
        'id': 'u1',
        'email': 'ada@example.com',
        'full_name': null,
        'is_admin': false,
      }),
    );

    final user = await repository.me(token: 'jwt');

    expect(user.email, 'ada@example.com');
    expect(user.displayName, 'ada@example.com');
    final options =
        verify(() => dio.get('/auth/me', options: captureAny(named: 'options')))
                .captured
                .single
            as Options;
    expect(options.headers?['Authorization'], 'Bearer jwt');
  });

  group('filenameFromContentDisposition', () {
    test('nom simple entre guillemets', () {
      expect(
        filenameFromContentDisposition('attachment; filename="support.pdf"'),
        'support.pdf',
      );
    });

    test('filename* (RFC 5987) prioritaire et décodé', () {
      expect(
        filenameFromContentDisposition(
          "attachment; filename=\"r?sum?.pdf\"; filename*=utf-8''r%C3%A9sum%C3%A9.pdf",
        ),
        'résumé.pdf',
      );
    });

    test('aucun chemin ne peut sortir du dossier cible', () {
      expect(
        filenameFromContentDisposition(
          'attachment; filename="../../etc/passwd"',
        ),
        'passwd',
      );
      expect(
        filenameFromContentDisposition('attachment; filename=".."'),
        isNull,
      );
      expect(filenameFromContentDisposition(null), isNull);
    });
  });
}
