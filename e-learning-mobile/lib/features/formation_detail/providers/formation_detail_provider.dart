import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/logging/app_logger.dart';
import '../../../data/models/models.dart';
import '../../../data/repositories/formation_repository.dart';
import '../../../data/repositories/progress_repository.dart';

typedef FormationDetailData = ({
  Formation formation,
  FormationProgress? progress,
});

final formationDetailProvider = FutureProvider.autoDispose
    .family<FormationDetailData, String>((ref, formationId) async {
      final formation = await ref
          .watch(formationRepositoryProvider)
          .getById(formationId);
      FormationProgress? progress;
      try {
        progress = await ref
            .watch(progressRepositoryProvider)
            .getFormationProgress(formationId);
      } catch (e, s) {
        // Best-effort : le détail de la formation reste consultable sans elle.
        logWarning('formation $formationId : progression indisponible', e, s);
      }
      return (formation: formation, progress: progress);
    });
