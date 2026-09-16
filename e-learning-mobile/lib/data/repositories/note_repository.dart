import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/network/api_endpoints.dart';
import '../../core/network/dio_client.dart';
import '../models/models.dart';

final noteRepositoryProvider = Provider<NoteRepository>((ref) {
  return NoteRepository(ref.watch(dioProvider));
});

class NoteRepository {
  NoteRepository(this._dio);

  final Dio _dio;

  Future<List<Note>> list(String videoId) async {
    try {
      final response = await _dio.get(ApiEndpoints.notes(videoId));
      final data = response.data as List<dynamic>;
      return data.whereType<Map<String, dynamic>>().map(Note.fromJson).toList()
        ..sort((a, b) => a.timecode.compareTo(b.timecode));
    } catch (e) {
      throw mapDioError(e);
    }
  }

  Future<Note> create(String videoId, double timecode, String content) async {
    try {
      final response = await _dio.post(
        ApiEndpoints.notes(videoId),
        data: {'timecode': timecode, 'content': content},
      );
      return Note.fromJson(response.data as Map<String, dynamic>);
    } catch (e) {
      throw mapDioError(e);
    }
  }

  Future<Note> update(String noteId, String content) async {
    try {
      final response = await _dio.put(
        ApiEndpoints.note(noteId),
        data: {'content': content},
      );
      return Note.fromJson(response.data as Map<String, dynamic>);
    } catch (e) {
      throw mapDioError(e);
    }
  }

  Future<void> delete(String noteId) async {
    try {
      await _dio.delete(ApiEndpoints.note(noteId));
    } catch (e) {
      throw mapDioError(e);
    }
  }
}
