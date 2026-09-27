import 'dart:io';

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
  return DocumentRepository(ref.watch(dioProvider));
});

class DocumentRepository {
  DocumentRepository(this._dio);

  final Dio _dio;

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

  /// Télécharge le document dans `<directory>/<documentId>/<nom de fichier>`
  /// et renvoie son chemin.
  ///
  /// Passe par le client Dio (et donc le jeton) : une URL ouverte dans le
  /// navigateur ou une autre application n'aurait pas d'en-tête
  /// `Authorization` et recevrait un 401.
  Future<String> downloadTo(String documentId, Directory directory) async {
    try {
      final response = await _dio.get<List<int>>(
        ApiEndpoints.documentFile(documentId, download: true),
        options: Options(responseType: ResponseType.bytes),
      );
      final name =
          filenameFromContentDisposition(
            response.headers.value('content-disposition'),
          ) ??
          documentId;
      final folder = Directory('${directory.path}/$documentId');
      await folder.create(recursive: true);
      final file = File('${folder.path}/$name');
      await file.writeAsBytes(response.data ?? const []);
      return file.path;
    } catch (e) {
      throw mapDioError(e);
    }
  }
}

/// Nom de fichier annoncé par `Content-Disposition` (`filename*` RFC 5987
/// prioritaire), réduit à un nom sans chemin. `null` si absent.
String? filenameFromContentDisposition(String? header) {
  if (header == null) return null;
  String? name;
  final extended = RegExp(
    r"filename\*\s*=\s*[^']*'[^']*'([^;]+)",
    caseSensitive: false,
  ).firstMatch(header);
  if (extended != null) {
    try {
      name = Uri.decodeComponent(extended.group(1)!.trim());
    } on ArgumentError {
      name = null;
    }
  }
  name ??= RegExp(
    r'filename\s*=\s*"?([^";]+)"?',
    caseSensitive: false,
  ).firstMatch(header)?.group(1)?.trim();
  if (name == null) return null;
  final base = name.split(RegExp(r'[/\\]')).last;
  return (base.isEmpty || base == '.' || base == '..') ? null : base;
}
