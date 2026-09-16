import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/network/api_endpoints.dart';
import '../../core/network/dio_client.dart';
import '../models/models.dart';

final formationRepositoryProvider = Provider<FormationRepository>((ref) {
  return FormationRepository(ref.watch(dioProvider));
});

class FormationRepository {
  FormationRepository(this._dio);

  final Dio _dio;

  List<Formation> _extract(dynamic data) {
    if (data is List) {
      return data
          .whereType<Map<String, dynamic>>()
          .map(Formation.fromJson)
          .toList();
    }
    if (data is Map<String, dynamic>) {
      final list = data['formations'] ?? data['data'] ?? data['items'];
      if (list is List) {
        return list
            .whereType<Map<String, dynamic>>()
            .map(Formation.fromJson)
            .toList();
      }
    }
    return const [];
  }

  Future<List<Formation>> list() async {
    try {
      final response = await _dio.get(ApiEndpoints.formations);
      final formations = _extract(response.data);
      return formations
          .map(
            (f) => f.copyWith(
              chapters: [...f.chapters]
                ..sort((a, b) => a.position.compareTo(b.position)),
            ),
          )
          .toList();
    } catch (e) {
      throw mapDioError(e);
    }
  }

  Future<Formation> getById(String id) async {
    try {
      final response = await _dio.get(ApiEndpoints.formation(id));
      final formation = Formation.fromJson(
        response.data as Map<String, dynamic>,
      );
      final chapters = [...formation.chapters]
        ..sort((a, b) => a.position.compareTo(b.position));
      return formation.copyWith(
        chapters: chapters
            .map(
              (c) => c.copyWith(
                videos: [...c.videos]
                  ..sort((a, b) => a.position.compareTo(b.position)),
                documents: [...c.documents]
                  ..sort((a, b) => a.position.compareTo(b.position)),
              ),
            )
            .toList(),
      );
    } catch (e) {
      throw mapDioError(e);
    }
  }

  Future<AskFormationResponse> ask(String formationId, String question) async {
    try {
      final response = await _dio.post(
        ApiEndpoints.formationAsk(formationId),
        data: {'question': question},
      );
      return AskFormationResponse.fromJson(
        response.data as Map<String, dynamic>,
      );
    } catch (e) {
      throw mapDioError(e);
    }
  }
}
