import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../../config/constants.dart';
import '../../data/repositories/auth_repository.dart';
import 'current_uid.dart';

class AuthState {
  const AuthState({this.uid, this.isLoading = false, this.error});

  final String? uid;
  final bool isLoading;
  final String? error;

  bool get isAuthenticated => uid != null && uid!.isNotEmpty;

  AuthState copyWith({
    String? uid,
    bool? isLoading,
    String? error,
    bool clearUid = false,
    bool clearError = false,
  }) {
    return AuthState(
      uid: clearUid ? null : (uid ?? this.uid),
      isLoading: isLoading ?? this.isLoading,
      error: clearError ? null : (error ?? this.error),
    );
  }
}

class AuthController extends Notifier<AuthState> {
  late final FlutterSecureStorage _storage;

  @override
  AuthState build() {
    _storage = const FlutterSecureStorage();
    return const AuthState(isLoading: true);
  }

  AuthRepository get _repo => ref.read(authRepositoryProvider);

  void _setUid(String? uid) {
    ref.read(currentUidProvider.notifier).setUid(uid);
  }

  Future<void> restoreSession() async {
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      final stored = await _storage.read(key: AppConstants.uidStorageKey);
      if (stored == null || stored.isEmpty) {
        _setUid(null);
        state = const AuthState();
        return;
      }
      final uid = await _repo.restore(stored);
      await _storage.write(key: AppConstants.uidStorageKey, value: uid);
      _setUid(uid);
      state = AuthState(uid: uid);
    } catch (e) {
      await _storage.delete(key: AppConstants.uidStorageKey);
      _setUid(null);
      state = AuthState(error: e.toString());
    }
  }

  Future<void> generate() async {
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      final uid = await _repo.generate();
      await _storage.write(key: AppConstants.uidStorageKey, value: uid);
      _setUid(uid);
      state = AuthState(uid: uid);
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  Future<void> restore(String uid) async {
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      final restored = await _repo.restore(uid.trim());
      await _storage.write(key: AppConstants.uidStorageKey, value: restored);
      _setUid(restored);
      state = AuthState(uid: restored);
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  Future<void> logout() async {
    await _storage.delete(key: AppConstants.uidStorageKey);
    _setUid(null);
    state = const AuthState();
  }
}

final authControllerProvider = NotifierProvider<AuthController, AuthState>(
  AuthController.new,
);
