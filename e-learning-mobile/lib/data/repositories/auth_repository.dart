import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/network/api_endpoints.dart';
import '../../core/network/dio_client.dart';
import '../models/models.dart';

final authRepositoryProvider = Provider<AuthRepository>((ref) {
  return AuthRepository(ref.watch(dioProvider));
});

class AuthRepository {
  AuthRepository(this._dio);

  final Dio _dio;

  /// OAuth2 password flow : renvoie le jeton d'accès.
  Future<String> login(String email, String password) async {
    try {
      final response = await _dio.post(
        ApiEndpoints.authLogin,
        data: {'username': email, 'password': password},
        options: Options(contentType: Headers.formUrlEncodedContentType),
      );
      return (response.data as Map<String, dynamic>)['access_token'] as String;
    } catch (e) {
      throw mapDioError(e);
    }
  }

  /// Compte porteur du jeton [token] (ou du jeton courant si omis).
  Future<CurrentUser> me({String? token}) async {
    try {
      final response = await _dio.get(
        ApiEndpoints.authMe,
        options: token == null
            ? null
            : Options(headers: {'Authorization': 'Bearer $token'}),
      );
      return CurrentUser.fromJson(response.data as Map<String, dynamic>);
    } catch (e) {
      throw mapDioError(e);
    }
  }
}
