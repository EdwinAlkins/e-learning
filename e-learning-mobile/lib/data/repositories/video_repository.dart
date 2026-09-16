import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/network/api_endpoints.dart';
import '../../core/network/dio_client.dart';
import '../../core/settings/settings_controller.dart';
import '../models/models.dart';

final videoRepositoryProvider = Provider<VideoRepository>((ref) {
  return VideoRepository(ref.watch(dioProvider), ref.watch(apiBaseUrlProvider));
});

class VideoRepository {
  VideoRepository(this._dio, this._baseUrl);

  final Dio _dio;

  /// Les URL de média sont consommées par le lecteur, hors client Dio.
  final String _baseUrl;

  String streamUrl(String videoId) =>
      '$_baseUrl${ApiEndpoints.videoStream(videoId)}';

  /// `null` si le résumé n'a pas encore été généré (404 côté API).
  Future<String?> getSummary(String videoId) async {
    try {
      final response = await _dio.get(ApiEndpoints.videoSummary(videoId));
      return (response.data as Map<String, dynamic>)['summary'] as String? ??
          '';
    } on DioException catch (e) {
      if (e.response?.statusCode == 404) return null;
      throw mapDioError(e);
    } catch (e) {
      throw mapDioError(e);
    }
  }

  Future<String> updateSummary(String videoId, String summary) async {
    try {
      final response = await _dio.put(
        ApiEndpoints.videoSummary(videoId),
        data: {'summary': summary},
      );
      return (response.data as Map<String, dynamic>)['summary'] as String? ??
          summary;
    } catch (e) {
      throw mapDioError(e);
    }
  }

  /// Lance la transcription — l'API répond 202 avec la vidéo mise à jour.
  Future<VideoItem> startTranscription(String videoId) =>
      _postVideoJob(ApiEndpoints.videoTranscription(videoId));

  /// Génère (ou régénère) le résumé à partir de la transcription.
  Future<VideoItem> generateSummary(String videoId) =>
      _postVideoJob(ApiEndpoints.videoSummaryGenerate(videoId));

  /// Relance la conversion du média (utile après un échec).
  Future<VideoItem> startConversion(String videoId) =>
      _postVideoJob(ApiEndpoints.videoConversion(videoId));

  Future<VideoItem> _postVideoJob(String path) async {
    try {
      final response = await _dio.post(path);
      return VideoItem.fromJson(response.data as Map<String, dynamic>);
    } catch (e) {
      throw mapDioError(e);
    }
  }
}

final documentRepositoryProvider = Provider<DocumentRepository>((ref) {
  return DocumentRepository(
    ref.watch(dioProvider),
    ref.watch(apiBaseUrlProvider),
  );
});

class DocumentRepository {
  DocumentRepository(this._dio, this._baseUrl);

  final Dio _dio;
  final String _baseUrl;

  Future<List<DocumentItem>> listByChapter(String chapterId) async {
    try {
      final response = await _dio.get(ApiEndpoints.chapterDocuments(chapterId));
      final data = response.data as List<dynamic>;
      return data
          .whereType<Map<String, dynamic>>()
          .map(DocumentItem.fromJson)
          .toList()
        ..sort((a, b) => a.position.compareTo(b.position));
    } catch (e) {
      throw mapDioError(e);
    }
  }

  String fileUrl(String documentId, {bool download = false}) =>
      '$_baseUrl${ApiEndpoints.documentFile(documentId, download: download)}';
}
