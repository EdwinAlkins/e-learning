import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/auth/current_uid.dart';
import '../../../core/logging/app_logger.dart';
import '../../../data/repositories/progress_repository.dart';
import '../../../data/repositories/video_repository.dart';
import 'media_controller.dart';
import 'player_context_provider.dart';

/// Cycle de vie du lecteur confié à Riverpod : construction, initialisation
/// asynchrone (reprise de position incluse) et libération.
///
/// La clé est celle de l'écran (`PlayerArgs`), donc stable tant qu'on reste sur
/// la même vidéo : le contrôleur survit aux rafraîchissements du contexte.
final mediaControllerProvider = FutureProvider.autoDispose
    .family<MediaController, PlayerArgs>((ref, args) async {
      // Lu sans être observé : le polling des statuts IA invalide
      // `playerContextProvider` toutes les 3 s et recréerait sinon le lecteur
      // en pleine lecture. Les champs utilisés ici (kind, durée) sont figés une
      // fois la conversion terminée, seul moment où le lecteur est construit.
      final context = ref.read(playerContextProvider(args)).value;
      if (context == null) {
        throw StateError(
          'mediaControllerProvider requiert un contexte de lecture chargé.',
        );
      }
      final video = context.video;

      final videoRepo = ref.watch(videoRepositoryProvider);
      final progressRepo = ref.watch(progressRepositoryProvider);
      // L'UID n'est lu qu'à la construction : il ne change qu'à la déconnexion,
      // qui démonte déjà l'écran.
      final uid = ref.read(currentUidProvider);

      double? startAt;
      try {
        startAt = await progressRepo.getVideoProgress(video.id);
      } catch (e, s) {
        // Reprise indisponible : on démarre au début, mais on trace.
        logWarning(
          'player ${video.id} : reprise de position indisponible',
          e,
          s,
        );
      }

      final controller = MediaController(
        videoId: video.id,
        isAudio: video.isAudio,
        streamUrl: videoRepo.streamUrl(video.id),
        headers: {if (uid != null && uid.isNotEmpty) 'X-User-UID': uid},
        fallbackDuration: video.duration,
        onSaveProgress: (position) =>
            progressRepo.saveVideoProgress(video.id, position),
      );

      // Sortie d'écran ou changement de vidéo : la dernière position doit
      // partir avant la libération (PLAY-08).
      ref.onDispose(() {
        unawaited(controller.flushProgress().whenComplete(controller.dispose));
      });

      await controller.initialize(startAt: startAt);
      return controller;
    });
