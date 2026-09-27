import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/network/api_endpoints.dart';
import '../../core/network/dio_client.dart';
import '../models/models.dart';

final usageRepositoryProvider = Provider<UsageRepository>((ref) {
  return UsageRepository(ref.watch(dioProvider));
});

class UsageRepository {
  UsageRepository(this._dio);

  final Dio _dio;

  /// Consommation LLM du compte connecté sur les [days] derniers jours (1–365).
  Future<UserTokenUsage> getUsage(int days) async {
    try {
      final response = await _dio.get(
        ApiEndpoints.usage,
        queryParameters: {'days': days},
      );
      return UserTokenUsage.fromJson(response.data as Map<String, dynamic>);
    } catch (e) {
      throw mapDioError(e);
    }
  }
}
