import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:media_kit/media_kit.dart';

import 'app.dart';
import 'config/env.dart';
import 'core/auth/auth_controller.dart';
import 'core/settings/settings_controller.dart';
import 'features/player/providers/media_controller.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  // Backend de lecture desktop (libmpv) — inutile sur Android / iOS.
  if (usesMediaKitBackend) {
    MediaKit.ensureInitialized();
  }
  await Env.load();
  // URL d'API éventuellement redéfinie depuis le panneau de config.
  await SettingsStore.load();

  final container = ProviderContainer();
  await container.read(authControllerProvider.notifier).restoreSession();

  runApp(
    UncontrolledProviderScope(
      container: container,
      child: const ELearningApp(),
    ),
  );
}
