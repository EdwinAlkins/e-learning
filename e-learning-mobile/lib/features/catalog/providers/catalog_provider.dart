import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/logging/app_logger.dart';
import '../../../data/models/models.dart';
import '../../../data/repositories/formation_repository.dart';
import '../../../data/repositories/progress_repository.dart';

typedef CatalogData = ({
  List<Formation> formations,
  Map<String, FormationProgress> progress,
});

final catalogProvider = FutureProvider.autoDispose<CatalogData>((ref) async {
  final formations = await ref.watch(formationRepositoryProvider).list();
  Map<String, FormationProgress> progress = {};
  try {
    progress = await ref
        .watch(progressRepositoryProvider)
        .getAllFormationsProgress();
  } catch (e, s) {
    // La progression est best-effort sur le catalogue : les formations
    // s'affichent sans elle, mais l'échec doit rester visible dans les logs.
    logWarning('catalog: progression indisponible', e, s);
  }
  return (formations: formations, progress: progress);
});
