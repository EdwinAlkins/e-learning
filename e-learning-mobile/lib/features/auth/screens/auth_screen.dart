import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/auth/auth_controller.dart';
import '../../../core/settings/settings_controller.dart';
import '../../settings/widgets/settings_sheet.dart';

class AuthScreen extends ConsumerStatefulWidget {
  const AuthScreen({super.key});

  @override
  ConsumerState<AuthScreen> createState() => _AuthScreenState();
}

class _AuthScreenState extends ConsumerState<AuthScreen> {
  final _controller = TextEditingController();

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final auth = ref.watch(authControllerProvider);
    final theme = Theme.of(context);
    final apiUrl = ref.watch(apiBaseUrlProvider);

    return Scaffold(
      body: SafeArea(
        child: Stack(
          children: [
            // Centré quand ça rentre, défilant dès que le clavier réduit la
            // hauteur disponible — sinon le bouton « Restaurer » passe sous le
            // clavier et la colonne déborde.
            Center(
              child: SingleChildScrollView(
                keyboardDismissBehavior:
                    ScrollViewKeyboardDismissBehavior.onDrag,
                child: Center(
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(maxWidth: 420),
                    child: Padding(
                      padding: const EdgeInsets.all(24),
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          Text(
                            'Cladèse',
                            textAlign: TextAlign.center,
                            style: theme.textTheme.headlineMedium?.copyWith(
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          const SizedBox(height: 8),
                          Text(
                            'Connectez-vous avec votre identifiant UID.',
                            textAlign: TextAlign.center,
                            style: theme.textTheme.bodyMedium?.copyWith(
                              color: theme.colorScheme.onSurfaceVariant,
                            ),
                          ),
                          const SizedBox(height: 8),
                          // La connexion échoue surtout quand l'API n'est pas la
                          // bonne : l'URL active est visible et modifiable ici.
                          TextButton.icon(
                            onPressed: () => showSettingsSheet(context),
                            icon: const Icon(Icons.dns_outlined, size: 16),
                            label: Text(
                              apiUrl,
                              overflow: TextOverflow.ellipsis,
                              style: theme.textTheme.bodySmall,
                            ),
                          ),
                          const SizedBox(height: 24),
                          if (auth.error != null) ...[
                            Material(
                              color: theme.colorScheme.errorContainer,
                              borderRadius: BorderRadius.circular(12),
                              child: Padding(
                                padding: const EdgeInsets.all(12),
                                child: Text(
                                  auth.error!,
                                  style: TextStyle(
                                    color: theme.colorScheme.onErrorContainer,
                                  ),
                                ),
                              ),
                            ),
                            const SizedBox(height: 16),
                          ],
                          FilledButton(
                            onPressed: auth.isLoading
                                ? null
                                : () => ref
                                      .read(authControllerProvider.notifier)
                                      .generate(),
                            child: auth.isLoading
                                ? const SizedBox(
                                    height: 20,
                                    width: 20,
                                    child: CircularProgressIndicator(
                                      strokeWidth: 2,
                                    ),
                                  )
                                : const Text('Générer un nouvel UID'),
                          ),
                          const SizedBox(height: 24),
                          TextField(
                            controller: _controller,
                            decoration: const InputDecoration(
                              labelText: 'UID existant',
                              border: OutlineInputBorder(),
                            ),
                            textInputAction: TextInputAction.done,
                            onSubmitted: (_) => _restore(),
                          ),
                          const SizedBox(height: 12),
                          OutlinedButton(
                            onPressed: auth.isLoading ? null : _restore,
                            child: const Text('Restaurer'),
                          ),
                          if (auth.uid != null) ...[
                            const SizedBox(height: 24),
                            SelectableText(
                              auth.uid!,
                              textAlign: TextAlign.center,
                              style: theme.textTheme.bodySmall,
                            ),
                            TextButton.icon(
                              onPressed: () {
                                Clipboard.setData(
                                  ClipboardData(text: auth.uid!),
                                );
                                ScaffoldMessenger.of(context).showSnackBar(
                                  const SnackBar(content: Text('UID copié')),
                                );
                              },
                              icon: const Icon(Icons.copy),
                              label: const Text('Copier l’UID'),
                            ),
                          ],
                        ],
                      ),
                    ),
                  ),
                ),
              ),
            ),
            const Align(
              alignment: Alignment.topRight,
              child: Padding(
                padding: EdgeInsets.all(8),
                child: SettingsButton(),
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _restore() {
    final uid = _controller.text.trim();
    if (uid.isEmpty) return;
    ref.read(authControllerProvider.notifier).restore(uid);
  }
}
