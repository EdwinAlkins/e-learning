import 'dart:developer' as developer;

/// Trace d'un échec non bloquant.
///
/// Les chemins « best-effort » (progression, préférences locales…) ne doivent
/// pas casser l'écran, mais ne doivent pas non plus disparaître sans laisser de
/// trace : sans cela, un endpoint en panne en production est invisible.
void logWarning(String context, Object error, [StackTrace? stackTrace]) {
  developer.log(
    context,
    name: 'e-learning',
    level: 900, // WARNING
    error: error,
    stackTrace: stackTrace,
  );
}
