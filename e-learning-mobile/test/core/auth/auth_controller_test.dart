import 'package:e_learning_mobile/config/constants.dart';
import 'package:e_learning_mobile/core/auth/access_token.dart';
import 'package:e_learning_mobile/core/auth/auth_controller.dart';
import 'package:e_learning_mobile/core/network/api_exception.dart';
import 'package:e_learning_mobile/data/models/models.dart';
import 'package:e_learning_mobile/data/repositories/auth_repository.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

class _MockAuthRepository extends Mock implements AuthRepository {}

const _user = CurrentUser(id: 'u1', email: 'ada@example.com');
const _storage = FlutterSecureStorage();

ApiException _http(int status) =>
    ApiException(message: 'HTTP $status', statusCode: status);

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late _MockAuthRepository repo;
  late ProviderContainer container;

  ProviderContainer build(Map<String, String> stored) {
    FlutterSecureStorage.setMockInitialValues(stored);
    final c = ProviderContainer(
      overrides: [authRepositoryProvider.overrideWithValue(repo)],
    );
    addTearDown(c.dispose);
    return c;
  }

  AuthController controller() =>
      container.read(authControllerProvider.notifier);
  AuthState state() => container.read(authControllerProvider);

  setUp(() => repo = _MockAuthRepository());

  test('sans jeton enregistré : non connecté, sans appel réseau', () async {
    container = build({});

    await controller().restoreSession();

    expect(state().isAuthenticated, isFalse);
    expect(state().isLoading, isFalse);
    verifyNever(() => repo.me(token: any(named: 'token')));
  });

  test('jeton valide : session reprise et jeton activé', () async {
    container = build({AppConstants.accessTokenStorageKey: 'jwt'});
    when(() => repo.me(token: 'jwt')).thenAnswer((_) async => _user);

    await controller().restoreSession();

    expect(state().user?.email, 'ada@example.com');
    expect(container.read(accessTokenProvider), 'jwt');
  });

  test("l'ancien UID anonyme est effacé au démarrage", () async {
    container = build({AppConstants.legacyUidStorageKey: 'old-uid'});

    await controller().restoreSession();

    expect(await _storage.read(key: AppConstants.legacyUidStorageKey), isNull);
  });

  test('jeton refusé (401) : effacé, retour à la connexion', () async {
    container = build({AppConstants.accessTokenStorageKey: 'expired'});
    when(() => repo.me(token: 'expired')).thenThrow(_http(401));

    await controller().restoreSession();

    expect(state().isAuthenticated, isFalse);
    expect(state().error, contains('Session expirée'));
    expect(
      await _storage.read(key: AppConstants.accessTokenStorageKey),
      isNull,
    );
  });

  test('API injoignable : le jeton est conservé pour réessayer', () async {
    container = build({AppConstants.accessTokenStorageKey: 'jwt'});
    when(() => repo.me(token: 'jwt'))
        .thenThrow(ApiException(message: 'Impossible de joindre l’API.'));

    await controller().restoreSession();

    expect(state().isAuthenticated, isFalse);
    expect(await _storage.read(key: AppConstants.accessTokenStorageKey), 'jwt');
  });

  test('login : jeton stocké, utilisateur chargé', () async {
    container = build({});
    when(() => repo.login('ada@example.com', 'pw'))
        .thenAnswer((_) async => 'jwt');
    when(() => repo.me(token: 'jwt')).thenAnswer((_) async => _user);

    await controller().login('  ada@example.com ', 'pw');

    expect(state().isAuthenticated, isTrue);
    expect(container.read(accessTokenProvider), 'jwt');
    expect(await _storage.read(key: AppConstants.accessTokenStorageKey), 'jwt');
  });

  test('login refusé : message générique, rien de stocké', () async {
    container = build({});
    when(() => repo.login(any(), any())).thenThrow(_http(401));

    await controller().login('ada@example.com', 'bad');

    expect(state().isAuthenticated, isFalse);
    expect(state().error, 'Email ou mot de passe incorrect.');
    expect(
      await _storage.read(key: AppConstants.accessTokenStorageKey),
      isNull,
    );
  });

  test('session expirée en cours de route : déconnexion', () async {
    container = build({AppConstants.accessTokenStorageKey: 'jwt'});
    when(() => repo.me(token: 'jwt')).thenAnswer((_) async => _user);
    await controller().restoreSession();

    await controller().sessionExpired();

    expect(state().isAuthenticated, isFalse);
    expect(container.read(accessTokenProvider), isNull);
    expect(
      await _storage.read(key: AppConstants.accessTokenStorageKey),
      isNull,
    );
  });

  test('logout : jeton oublié', () async {
    container = build({AppConstants.accessTokenStorageKey: 'jwt'});
    when(() => repo.me(token: 'jwt')).thenAnswer((_) async => _user);
    await controller().restoreSession();

    await controller().logout();

    expect(state().isAuthenticated, isFalse);
    expect(
      await _storage.read(key: AppConstants.accessTokenStorageKey),
      isNull,
    );
  });
}
