import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../config/constants.dart';

class ThemeController extends Notifier<ThemeMode> {
  @override
  ThemeMode build() {
    _load();
    return ThemeMode.system;
  }

  Future<void> _load() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(AppConstants.themeStorageKey);
    state = switch (raw) {
      'light' => ThemeMode.light,
      'dark' => ThemeMode.dark,
      _ => ThemeMode.system,
    };
  }

  Future<void> setMode(ThemeMode mode) async {
    state = mode;
    final prefs = await SharedPreferences.getInstance();
    final value = switch (mode) {
      ThemeMode.light => 'light',
      ThemeMode.dark => 'dark',
      ThemeMode.system => 'system',
    };
    await prefs.setString(AppConstants.themeStorageKey, value);
  }
}

final themeControllerProvider = NotifierProvider<ThemeController, ThemeMode>(
  ThemeController.new,
);

/// Couleur de marque commune aux deux thèmes : `ColorScheme.fromSeed` dérive
/// lui-même une teinte lisible pour chaque `brightness`, inutile (et nuisible à
/// la cohérence) de fournir deux graines différentes.
const _seedColor = Color(0xFF1565C0);

/// Police embarquée (voir `pubspec.yaml`).
const _fontFamily = 'Inter';

ThemeData buildLightTheme() => _buildTheme(Brightness.light);

ThemeData buildDarkTheme() => _buildTheme(Brightness.dark);

ThemeData _buildTheme(Brightness brightness) {
  final scheme = ColorScheme.fromSeed(
    seedColor: _seedColor,
    brightness: brightness,
  );
  final base = ThemeData(
    useMaterial3: true,
    brightness: brightness,
    colorScheme: scheme,
  );

  final isDark = brightness == Brightness.dark;
  // En clair, les blocs ressortent en étant *plus* clairs que le fond ; en
  // sombre, c'est l'inverse. Un `surfaceContainer` unique donnerait des cartes
  // grisâtres en clair et invisibles en sombre.
  final blockColor = isDark
      ? scheme.surfaceContainer
      : scheme.surfaceContainerLowest;

  return base.copyWith(
    scaffoldBackgroundColor: scheme.surface,
    textTheme: _interTextTheme(base.textTheme, scheme),
    primaryTextTheme: _interTextTheme(base.primaryTextTheme, scheme),
    appBarTheme: AppBarTheme(
      backgroundColor: scheme.surface,
      foregroundColor: scheme.onSurface,
      surfaceTintColor: Colors.transparent,
      elevation: 0,
      titleTextStyle: base.textTheme.titleLarge?.copyWith(
        fontFamily: _fontFamily,
        color: scheme.onSurface,
        fontWeight: FontWeight.w600,
      ),
    ),
    // Le contour remplace l'ombre : en thème sombre une ombre ne se voit pas,
    // et la carte se confondait avec le fond.
    cardTheme: base.cardTheme.copyWith(
      color: blockColor,
      surfaceTintColor: Colors.transparent,
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: scheme.outlineVariant),
      ),
    ),
    bottomSheetTheme: base.bottomSheetTheme.copyWith(
      backgroundColor: blockColor,
      surfaceTintColor: Colors.transparent,
    ),
    dialogTheme: base.dialogTheme.copyWith(
      backgroundColor: blockColor,
      surfaceTintColor: Colors.transparent,
    ),
    listTileTheme: base.listTileTheme.copyWith(
      iconColor: scheme.onSurfaceVariant,
      textColor: scheme.onSurface,
    ),
    dividerTheme: base.dividerTheme.copyWith(color: scheme.outlineVariant),
    snackBarTheme: base.snackBarTheme.copyWith(
      backgroundColor: scheme.inverseSurface,
      contentTextStyle: base.textTheme.bodyMedium?.copyWith(
        fontFamily: _fontFamily,
        color: scheme.onInverseSurface,
      ),
      behavior: SnackBarBehavior.floating,
    ),
    inputDecorationTheme: base.inputDecorationTheme.copyWith(
      filled: true,
      fillColor: isDark
          ? scheme.surfaceContainerHigh
          : scheme.surfaceContainerLow,
    ),
  );
}

/// Applique Inter à toute la table typographique et remonte légèrement le
/// contraste : Material 3 laisse `bodySmall`/`labelSmall` en `onSurfaceVariant`,
/// difficilement lisible sur fond sombre à ces tailles.
TextTheme _interTextTheme(TextTheme base, ColorScheme scheme) {
  final themed = base.apply(
    fontFamily: _fontFamily,
    bodyColor: scheme.onSurface,
    displayColor: scheme.onSurface,
  );
  return themed.copyWith(
    titleLarge: themed.titleLarge?.copyWith(fontWeight: FontWeight.w600),
    titleMedium: themed.titleMedium?.copyWith(fontWeight: FontWeight.w600),
    titleSmall: themed.titleSmall?.copyWith(fontWeight: FontWeight.w600),
    labelLarge: themed.labelLarge?.copyWith(fontWeight: FontWeight.w600),
    bodyLarge: themed.bodyLarge?.copyWith(height: 1.45),
    bodyMedium: themed.bodyMedium?.copyWith(height: 1.45),
    bodySmall: themed.bodySmall?.copyWith(
      height: 1.4,
      color: scheme.onSurfaceVariant,
    ),
  );
}
