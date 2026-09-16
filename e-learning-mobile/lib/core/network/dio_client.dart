import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../auth/current_uid.dart';
import '../logging/app_logger.dart';
import '../settings/settings_controller.dart';
import 'api_exception.dart';

final dioProvider = Provider<Dio>((ref) {
  // Changer l'URL dans le panneau de config recrée le client, donc tous les
  // repositories (et les données qu'ils exposent) derrière lui.
  final dio = Dio(
    BaseOptions(
      baseUrl: ref.watch(apiBaseUrlProvider),
      connectTimeout: const Duration(seconds: 15),
      receiveTimeout: const Duration(seconds: 30),
      headers: const {'Content-Type': 'application/json'},
    ),
  );

  dio.interceptors.add(
    InterceptorsWrapper(
      onRequest: (options, handler) {
        final uid = ref.read(currentUidProvider);
        if (uid != null && uid.isNotEmpty) {
          options.headers['X-User-UID'] = uid;
        }
        handler.next(options);
      },
    ),
  );

  ref.onDispose(dio.close);

  return dio;
});

ApiException mapDioError(Object error) {
  if (error is DioException) {
    final status = error.response?.statusCode;
    final data = error.response?.data;
    String message = 'Erreur réseau';
    if (data is Map && data['detail'] is String) {
      message = data['detail'] as String;
    } else if (error.type == DioExceptionType.connectionTimeout ||
        error.type == DioExceptionType.receiveTimeout) {
      message = 'Délai dépassé. Vérifiez votre connexion.';
    } else if (error.type == DioExceptionType.connectionError) {
      final target = error.requestOptions.baseUrl;
      message = target.isEmpty
          ? 'Impossible de joindre l’API.'
          : 'Impossible de joindre l’API ($target).';
    } else if (status != null) {
      // Le code HTTP ne dit rien à l'utilisateur : il part dans les logs et
      // reste porté par `statusCode` pour les appelants qui en ont besoin.
      logWarning('HTTP $status sur ${error.requestOptions.uri}', error);
      message = status >= 500
          ? 'Le serveur a rencontré une erreur. Réessayez dans un instant.'
          : 'La requête n’a pas abouti. Réessayez.';
    }
    return ApiException(message: message, statusCode: status);
  }
  return ApiException(message: error.toString());
}
