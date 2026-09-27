import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../auth/access_token.dart';
import '../auth/auth_controller.dart';
import '../logging/app_logger.dart';
import '../settings/settings_controller.dart';
import 'api_endpoints.dart';
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
        // Un en-tête déjà fourni (vérification d'un jeton pas encore activé)
        // est prioritaire.
        options.headers.putIfAbsent(
          'Authorization',
          () => authHeaders(ref.read(accessTokenProvider))['Authorization'],
        );
        options.headers.removeWhere((_, value) => value == null);
        handler.next(options);
      },
      onError: (error, handler) {
        // 401 hors connexion = jeton expiré ou compte désactivé : retour à
        // l'écran de connexion. Un 403 (droits insuffisants) ne déconnecte pas.
        final path = error.requestOptions.path;
        if (error.response?.statusCode == 401 &&
            path != ApiEndpoints.authLogin &&
            path != ApiEndpoints.authMe) {
          ref.read(authControllerProvider.notifier).sessionExpired();
        }
        handler.next(error);
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
    if (status == 404 && error.requestOptions.path == ApiEndpoints.authLogin) {
      // `/auth/login` absent : l'URL vise une API d'avant les comptes.
      message =
          'Cette API ne gère pas la connexion par compte '
          '(${error.requestOptions.baseUrl}). Vérifiez l’URL ou mettez-la à jour.';
    } else if (data is Map && data['detail'] is String) {
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
    } else {
      // Sans réponse ni cause reconnue (connexion coupée, certificat…) :
      // « Erreur réseau » seul ne permet pas de diagnostiquer.
      logWarning('Échec réseau sur ${error.requestOptions.uri}', error);
      final cause = error.error ?? error.message;
      if (cause != null) message = 'Erreur réseau : $cause';
    }
    return ApiException(message: message, statusCode: status);
  }
  return ApiException(message: error.toString());
}
