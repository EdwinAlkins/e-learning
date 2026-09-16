import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/network/api_endpoints.dart';
import '../../core/network/dio_client.dart';

final authRepositoryProvider = Provider<AuthRepository>((ref) {
  return AuthRepository(ref.watch(dioProvider));
});

class AuthRepository {
  AuthRepository(this._dio);

  final Dio _dio;

  Future<String> generate() async {
    try {
      final response = await _dio.post(ApiEndpoints.authGenerate);
      return response.data['uid'] as String;
    } catch (e) {
      throw mapDioError(e);
    }
  }

  Future<String> restore(String uid) async {
    try {
      final response = await _dio.post(
        ApiEndpoints.authRestore,
        data: {'uid': uid},
      );
      return response.data['uid'] as String;
    } catch (e) {
      throw mapDioError(e);
    }
  }
}
