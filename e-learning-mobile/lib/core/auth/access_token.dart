import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Jeton d'accès (JWT) de la session en cours, en mémoire.
///
/// La copie persistante vit dans `flutter_secure_storage`
/// (`AppConstants.accessTokenStorageKey`), gérée par `AuthController`.
class AccessToken extends Notifier<String?> {
  @override
  String? build() => null;

  void set(String? token) => state = token;
}

final accessTokenProvider = NotifierProvider<AccessToken, String?>(
  AccessToken.new,
);

/// En-têtes à joindre aux requêtes faites hors client Dio (lecteur média).
Map<String, String> authHeaders(String? token) => {
  if (token != null && token.isNotEmpty) 'Authorization': 'Bearer $token',
};
