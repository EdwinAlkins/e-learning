class AppConstants {
  /// Sauvegarde de progression : debounce court…
  static const progressDebounce = Duration(milliseconds: 500);

  /// …mais au plus 5 s sans écriture pendant une lecture continue.
  static const progressMaxWait = Duration(seconds: 5);

  /// Rafraîchissement des statuts IA quand un job est en cours.
  static const jobPollInterval = Duration(seconds: 3);

  static const uidStorageKey = 'user_uid';
  static const themeStorageKey = 'theme_mode';
  static const apiUrlStorageKey = 'api_url_override';
}
