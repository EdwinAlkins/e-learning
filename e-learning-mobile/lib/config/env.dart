import 'package:flutter_dotenv/flutter_dotenv.dart';

import '../core/logging/app_logger.dart';

/// Configuration de base de l'application.
///
/// Priorité, du plus fort au plus faible :
/// 1. `--dart-define=API_URL=…` — réservé aux builds CI / release ;
/// 2. le fichier `.env` à la racine — configuration de développement ;
/// 3. [defaultApiUrl] — filet de sécurité si `.env` est absent.
///
/// L'utilisateur peut en plus surcharger l'URL à chaud depuis le panneau de
/// réglages ; cette valeur-là est persistée et prime sur tout le reste.
class Env {
  /// Alias de la machine hôte vu depuis l'émulateur Android.
  static const defaultApiUrl = 'http://10.0.2.2:8000';

  static late String apiUrl;

  static Future<void> load() async {
    const fromDefine = String.fromEnvironment('API_URL');
    if (fromDefine.isNotEmpty) {
      apiUrl = fromDefine;
      return;
    }

    try {
      await dotenv.load(fileName: '.env');
      apiUrl = dotenv.env['API_URL'] ?? defaultApiUrl;
    } catch (e, s) {
      // `.env` absent de la racine ou non déclaré dans les assets du pubspec :
      // sans trace, le repli silencieux sur l'émulateur est indébuggable.
      logWarning('.env illisible, repli sur $defaultApiUrl', e, s);
      apiUrl = defaultApiUrl;
    }
  }
}
