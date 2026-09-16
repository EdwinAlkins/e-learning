import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../config/constants.dart';
import '../../config/env.dart';
import '../logging/app_logger.dart';

/// Nettoie une URL saisie à la main : ajoute `http://` si le schéma manque,
/// enlève les `/` finaux. Renvoie `null` si l'URL est inexploitable.
String? normalizeApiUrl(String raw) {
  var value = raw.trim();
  if (value.isEmpty) return null;
  if (!value.contains('://')) value = 'http://$value';
  while (value.endsWith('/')) {
    value = value.substring(0, value.length - 1);
  }
  final uri = Uri.tryParse(value);
  if (uri == null || uri.host.isEmpty) return null;
  if (uri.scheme != 'http' && uri.scheme != 'https') return null;
  return value;
}

class AppSettings {
  const AppSettings({required this.apiUrl, this.isApiUrlOverridden = false});

  /// URL effectivement utilisée par le client HTTP.
  final String apiUrl;

  /// `true` quand l'URL vient du panneau de config plutôt que du build / `.env`.
  final bool isApiUrlOverridden;
}

/// Valeurs persistées lues une fois au démarrage : le premier appel réseau
/// doit déjà partir sur la bonne base.
class SettingsStore {
  static String? _apiUrl;

  static String? get apiUrl => _apiUrl;

  static Future<void> load() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      _apiUrl = normalizeApiUrl(
        prefs.getString(AppConstants.apiUrlStorageKey) ?? '',
      );
    } catch (e, s) {
      // Sans override lisible on repart sur Env.apiUrl, mais un stockage
      // inaccessible au démarrage explique des bugs d'URL difficiles à isoler.
      logWarning('settings: lecture de l’override d’URL impossible', e, s);
      _apiUrl = null;
    }
  }
}

class SettingsController extends Notifier<AppSettings> {
  @override
  AppSettings build() {
    final stored = SettingsStore._apiUrl;
    return AppSettings(
      apiUrl: stored ?? Env.apiUrl,
      isApiUrlOverridden: stored != null,
    );
  }

  /// Renvoie `false` si l'URL est invalide — l'état reste alors inchangé.
  Future<bool> setApiUrl(String raw) async {
    final url = normalizeApiUrl(raw);
    if (url == null) return false;

    SettingsStore._apiUrl = url;
    state = AppSettings(apiUrl: url, isApiUrlOverridden: true);
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(AppConstants.apiUrlStorageKey, url);
    return true;
  }

  /// Revient à l'URL fournie au build (`--dart-define`) ou par le `.env`.
  Future<void> resetApiUrl() async {
    SettingsStore._apiUrl = null;
    state = AppSettings(apiUrl: Env.apiUrl);
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(AppConstants.apiUrlStorageKey);
  }
}

final settingsControllerProvider =
    NotifierProvider<SettingsController, AppSettings>(SettingsController.new);

/// Base des appels HTTP : tout ce qui en dépend se reconstruit à sa modification.
final apiBaseUrlProvider = Provider<String>(
  (ref) => ref.watch(settingsControllerProvider).apiUrl,
);
