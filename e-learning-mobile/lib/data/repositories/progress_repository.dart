import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/network/api_endpoints.dart';
import '../../core/network/dio_client.dart';
import '../models/models.dart';

final progressRepositoryProvider = Provider<ProgressRepository>((ref) {
  return ProgressRepository(ref.watch(dioProvider));
});

class ProgressRepository {
  ProgressRepository(this._dio);

  final Dio _dio;

  Future<double?> getVideoProgress(String videoId) async {
    try {
      final response = await _dio.get(ApiEndpoints.progress(videoId));
      final data = response.data as Map<String, dynamic>;
      return (data['last_position'] as num?)?.toDouble();
    } on DioException catch (e) {
      if (e.response?.statusCode == 404) return null;
      throw mapDioError(e);
    } catch (e) {
      throw mapDioError(e);
    }
  }

  Future<void> saveVideoProgress(String videoId, double position) async {
    try {
      await _dio.post(
        ApiEndpoints.progress(videoId),
        data: {'last_position': position},
      );
    } catch (e) {
      throw mapDioError(e);
    }
  }

  Future<FormationProgress> getFormationProgress(String formationId) async {
    try {
      final response = await _dio.get(
        ApiEndpoints.formationProgress(formationId),
      );
      return FormationProgress.fromJson(response.data as Map<String, dynamic>);
    } catch (e) {
      throw mapDioError(e);
    }
  }

  Future<Map<String, FormationProgress>> getAllFormationsProgress() async {
    try {
      final response = await _dio.get(ApiEndpoints.formationsProgress);
      final data = response.data as Map<String, dynamic>;
      final raw = data['progress'];
      if (raw is! Map) return {};
      return raw.map(
        (key, value) => MapEntry(
          '$key',
          FormationProgress.fromJson(value as Map<String, dynamic>),
        ),
      );
    } catch (e) {
      throw mapDioError(e);
    }
  }
}
