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
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _obscure = true;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
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
            // hauteur disponible — sinon le bouton « Se connecter » passe sous
            // le clavier et la colonne déborde.
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
                            'Connectez-vous avec votre email et votre mot de passe.',
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
                          AutofillGroup(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.stretch,
                              children: [
                                TextField(
                                  controller: _emailController,
                                  decoration: const InputDecoration(
                                    labelText: 'Email',
                                    border: OutlineInputBorder(),
                                    prefixIcon: Icon(Icons.alternate_email),
                                  ),
                                  keyboardType: TextInputType.emailAddress,
                                  autocorrect: false,
                                  enabled: !auth.isLoading,
                                  autofillHints: const [
                                    AutofillHints.username,
                                    AutofillHints.email,
                                  ],
                                  textInputAction: TextInputAction.next,
                                ),
                                const SizedBox(height: 12),
                                TextField(
                                  controller: _passwordController,
                                  decoration: InputDecoration(
                                    labelText: 'Mot de passe',
                                    border: const OutlineInputBorder(),
                                    prefixIcon: const Icon(Icons.lock_outline),
                                    suffixIcon: IconButton(
                                      tooltip: _obscure
                                          ? 'Afficher le mot de passe'
                                          : 'Masquer le mot de passe',
                                      icon: Icon(
                                        _obscure
                                            ? Icons.visibility_outlined
                                            : Icons.visibility_off_outlined,
                                      ),
                                      onPressed: () =>
                                          setState(() => _obscure = !_obscure),
                                    ),
                                  ),
                                  obscureText: _obscure,
                                  enabled: !auth.isLoading,
                                  autofillHints: const [AutofillHints.password],
                                  textInputAction: TextInputAction.done,
                                  onSubmitted: (_) => _login(),
                                ),
                              ],
                            ),
                          ),
                          const SizedBox(height: 16),
                          FilledButton(
                            onPressed: auth.isLoading ? null : _login,
                            child: auth.isLoading
                                ? const SizedBox(
                                    height: 20,
                                    width: 20,
                                    child: CircularProgressIndicator(
                                      strokeWidth: 2,
                                    ),
                                  )
                                : const Text('Se connecter'),
                          ),
                          const SizedBox(height: 16),
                          Text(
                            'Pas de compte ? Demandez-en un à votre administrateur.',
                            textAlign: TextAlign.center,
                            style: theme.textTheme.bodySmall?.copyWith(
                              color: theme.colorScheme.onSurfaceVariant,
                            ),
                          ),
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

  void _login() {
    final email = _emailController.text.trim();
    final password = _passwordController.text;
    if (email.isEmpty || password.isEmpty) return;
    TextInput.finishAutofillContext();
    ref.read(authControllerProvider.notifier).login(email, password);
  }
}
