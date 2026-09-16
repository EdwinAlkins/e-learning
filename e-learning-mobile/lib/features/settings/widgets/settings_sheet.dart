import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../config/env.dart';
import '../../../core/auth/auth_controller.dart';
import '../../../core/network/api_endpoints.dart';
import '../../../core/network/dio_client.dart';
import '../../../core/settings/settings_controller.dart';
import '../../../core/theme/theme_controller.dart';

/// Panneau de configuration, disponible depuis n'importe quel écran — y compris
/// l'écran de connexion, où corriger l'URL de l'API est souvent la seule façon
/// de s'authentifier.
Future<void> showSettingsSheet(BuildContext context) {
  return showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    useSafeArea: true,
    showDragHandle: true,
    builder: (_) => const _SettingsSheet(),
  );
}

/// Bouton d'accès au panneau, à placer dans les `actions` d'une `AppBar`.
class SettingsButton extends StatelessWidget {
  const SettingsButton({super.key});

  @override
  Widget build(BuildContext context) {
    return IconButton(
      tooltip: 'Paramètres',
      onPressed: () => showSettingsSheet(context),
      icon: const Icon(Icons.settings_outlined),
    );
  }
}

class _SettingsSheet extends ConsumerStatefulWidget {
  const _SettingsSheet();

  @override
  ConsumerState<_SettingsSheet> createState() => _SettingsSheetState();
}

class _SettingsSheetState extends ConsumerState<_SettingsSheet> {
  late final TextEditingController _urlController;
  String? _urlError;
  bool _testing = false;
  ({bool ok, String message})? _testResult;

  @override
  void initState() {
    super.initState();
    _urlController = TextEditingController(
      text: ref.read(settingsControllerProvider).apiUrl,
    );
  }

  @override
  void dispose() {
    _urlController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final settings = ref.watch(settingsControllerProvider);
    final themeMode = ref.watch(themeControllerProvider);
    final auth = ref.watch(authControllerProvider);

    return Padding(
      padding: EdgeInsets.only(
        left: 24,
        right: 24,
        bottom: 24 + MediaQuery.viewInsetsOf(context).bottom,
      ),
      child: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          mainAxisSize: MainAxisSize.min,
          children: [
            Text('Paramètres', style: theme.textTheme.titleLarge),
            const SizedBox(height: 24),

            _SectionTitle('Serveur'),
            TextField(
              controller: _urlController,
              keyboardType: TextInputType.url,
              autocorrect: false,
              decoration: InputDecoration(
                labelText: 'URL de l’API',
                hintText: 'http://192.168.1.10:8000',
                border: const OutlineInputBorder(),
                errorText: _urlError,
                prefixIcon: const Icon(Icons.dns_outlined),
              ),
              onChanged: (_) {
                if (_urlError != null || _testResult != null) {
                  setState(() {
                    _urlError = null;
                    _testResult = null;
                  });
                }
              },
              onSubmitted: (_) => _save(),
            ),
            const SizedBox(height: 8),
            Text(
              settings.isApiUrlOverridden
                  ? 'Active : ${settings.apiUrl} (personnalisée)'
                  : 'Active : ${settings.apiUrl} (valeur du build)',
              style: theme.textTheme.bodySmall?.copyWith(
                color: theme.colorScheme.onSurfaceVariant,
              ),
            ),
            if (_testResult case final result?) ...[
              const SizedBox(height: 12),
              _ResultBanner(ok: result.ok, message: result.message),
            ],
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: _testing ? null : _testConnection,
                    icon: _testing
                        ? const SizedBox(
                            height: 16,
                            width: 16,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Icon(Icons.network_check),
                    label: const Text('Tester'),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: FilledButton.icon(
                    onPressed: _save,
                    icon: const Icon(Icons.save_outlined),
                    label: const Text('Enregistrer'),
                  ),
                ),
              ],
            ),
            if (settings.isApiUrlOverridden)
              TextButton.icon(
                onPressed: _reset,
                icon: const Icon(Icons.restart_alt),
                label: Text('Revenir à ${Env.apiUrl}'),
              ),

            const SizedBox(height: 24),
            _SectionTitle('Apparence'),
            SegmentedButton<ThemeMode>(
              // Sans icônes : sur 360 dp, « Système » passait sur deux lignes.
              segments: const [
                ButtonSegment(value: ThemeMode.system, label: Text('Système')),
                ButtonSegment(value: ThemeMode.light, label: Text('Clair')),
                ButtonSegment(value: ThemeMode.dark, label: Text('Sombre')),
              ],
              selected: {themeMode},
              showSelectedIcon: false,
              onSelectionChanged: (selection) => ref
                  .read(themeControllerProvider.notifier)
                  .setMode(selection.first),
            ),

            const SizedBox(height: 24),
            _SectionTitle('Session'),
            if (auth.uid case final uid?) ...[
              Text(
                'UID',
                style: theme.textTheme.labelMedium?.copyWith(
                  color: theme.colorScheme.onSurfaceVariant,
                ),
              ),
              const SizedBox(height: 4),
              Row(
                children: [
                  Expanded(
                    child: SelectableText(
                      uid,
                      style: theme.textTheme.bodyMedium,
                    ),
                  ),
                  IconButton(
                    tooltip: 'Copier l’UID',
                    onPressed: () {
                      Clipboard.setData(ClipboardData(text: uid));
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text('UID copié')),
                      );
                    },
                    icon: const Icon(Icons.copy, size: 18),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              OutlinedButton.icon(
                onPressed: () async {
                  final navigator = Navigator.of(context);
                  await ref.read(authControllerProvider.notifier).logout();
                  navigator.pop();
                },
                icon: const Icon(Icons.logout),
                label: const Text('Se déconnecter'),
              ),
            ] else
              Text(
                'Aucune session active.',
                style: theme.textTheme.bodyMedium?.copyWith(
                  color: theme.colorScheme.onSurfaceVariant,
                ),
              ),
          ],
        ),
      ),
    );
  }

  /// Ping `/health` sur l'URL saisie, sans toucher à la configuration active.
  Future<void> _testConnection() async {
    final url = normalizeApiUrl(_urlController.text);
    if (url == null) {
      setState(() => _urlError = 'URL invalide');
      return;
    }

    setState(() {
      _testing = true;
      _urlError = null;
      _testResult = null;
    });

    final dio = Dio(
      BaseOptions(
        baseUrl: url,
        connectTimeout: const Duration(seconds: 5),
        receiveTimeout: const Duration(seconds: 5),
      ),
    );
    ({bool ok, String message}) result;
    try {
      final response = await dio.get(ApiEndpoints.health);
      result = (
        ok: true,
        message: 'Serveur joignable (HTTP ${response.statusCode}).',
      );
    } catch (e) {
      result = (ok: false, message: mapDioError(e).message);
    } finally {
      dio.close(force: true);
    }

    if (!mounted) return;
    setState(() {
      _testing = false;
      _testResult = result;
    });
  }

  Future<void> _save() async {
    final messenger = ScaffoldMessenger.of(context);
    final navigator = Navigator.of(context);

    final saved = await ref
        .read(settingsControllerProvider.notifier)
        .setApiUrl(_urlController.text);
    if (!mounted) return;
    if (!saved) {
      setState(() => _urlError = 'URL invalide');
      return;
    }

    navigator.pop();
    messenger.showSnackBar(
      SnackBar(
        content: Text('API : ${ref.read(settingsControllerProvider).apiUrl}'),
      ),
    );
  }

  Future<void> _reset() async {
    await ref.read(settingsControllerProvider.notifier).resetApiUrl();
    if (!mounted) return;
    setState(() {
      _urlController.text = ref.read(settingsControllerProvider).apiUrl;
      _urlError = null;
      _testResult = null;
    });
  }
}

class _SectionTitle extends StatelessWidget {
  const _SectionTitle(this.label);

  final String label;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Text(
        label.toUpperCase(),
        style: theme.textTheme.labelSmall?.copyWith(
          color: theme.colorScheme.primary,
          letterSpacing: 1.2,
          fontWeight: FontWeight.w700,
        ),
      ),
    );
  }
}

class _ResultBanner extends StatelessWidget {
  const _ResultBanner({required this.ok, required this.message});

  final bool ok;
  final String message;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final background = ok ? scheme.secondaryContainer : scheme.errorContainer;
    final foreground = ok
        ? scheme.onSecondaryContainer
        : scheme.onErrorContainer;

    return Material(
      color: background,
      borderRadius: BorderRadius.circular(12),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Row(
          children: [
            Icon(
              ok ? Icons.check_circle_outline : Icons.error_outline,
              color: foreground,
              size: 20,
            ),
            const SizedBox(width: 8),
            Expanded(
              child: Text(message, style: TextStyle(color: foreground)),
            ),
          ],
        ),
      ),
    );
  }
}
