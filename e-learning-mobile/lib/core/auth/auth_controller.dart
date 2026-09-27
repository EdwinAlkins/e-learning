import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../../config/constants.dart';
import '../../data/models/models.dart';
import '../../data/repositories/auth_repository.dart';
import '../network/api_exception.dart';
import 'access_token.dart';

class AuthState {
  const AuthState({this.user, this.isLoading = false, this.error});

  final CurrentUser? user;
  final bool isLoading;
  final String? error;

  bool get isAuthenticated => user != null;
}

class AuthController extends Notifier<AuthState> {
  late final FlutterSecureStorage _storage;

  @override
  AuthState build() {
    _storage = const FlutterSecureStorage();
    return const AuthState(isLoading: true);
  }

  AuthRepository get _repo => ref.read(authRepositoryProvider);

  void _setToken(String? token) {
    ref.read(accessTokenProvider.notifier).set(token);
  }

  /// Reprend la session enregistrée : jeton lu dans le stockage sécurisé,
  /// puis `GET /auth/me` pour obtenir le compte (et vérifier le jeton).
  Future<void> restoreSession() async {
    state = const AuthState(isLoading: true);
    // L'identifiant anonyme d'avant les comptes n'ouvre plus rien.
    await _storage.delete(key: AppConstants.legacyUidStorageKey);
    final stored = await _storage.read(key: AppConstants.accessTokenStorageKey);
    if (stored == null || stored.isEmpty) {
      state = const AuthState();
      return;
    }
    try {
      final user = await _repo.me(token: stored);
      _setToken(stored);
      state = AuthState(user: user);
    } on ApiException catch (e) {
      if (e.statusCode == 401) {
        // Jeton expiré, révoqué ou compte désactivé : reconnexion obligatoire.
        await _storage.delete(key: AppConstants.accessTokenStorageKey);
        state = const AuthState(error: 'Session expirée. Reconnectez-vous.');
      } else {
        // API injoignable : on garde le jeton pour une nouvelle tentative.
        state = AuthState(error: e.message);
      }
    }
  }

  Future<void> login(String email, String password) async {
    state = const AuthState(isLoading: true);
    try {
      final token = await _repo.login(email.trim(), password);
      final user = await _repo.me(token: token);
      await _storage.write(
        key: AppConstants.accessTokenStorageKey,
        value: token,
      );
      _setToken(token);
      state = AuthState(user: user);
    } on ApiException catch (e) {
      state = AuthState(
        error: e.statusCode == 401
            ? 'Email ou mot de passe incorrect.'
            : e.message,
      );
    }
  }

  Future<void> logout() async {
    await _storage.delete(key: AppConstants.accessTokenStorageKey);
    _setToken(null);
    state = const AuthState();
  }

  /// Appelé par le client HTTP sur un 401 : la redirection vers l'écran de
  /// connexion suit via `_AuthRefresh` (routes).
  Future<void> sessionExpired() async {
    if (!state.isAuthenticated) return;
    await _storage.delete(key: AppConstants.accessTokenStorageKey);
    _setToken(null);
    state = const AuthState(error: 'Session expirée. Reconnectez-vous.');
  }
}

final authControllerProvider = NotifierProvider<AuthController, AuthState>(
  AuthController.new,
);
