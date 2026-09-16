import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../data/repositories/video_repository.dart';

/// Résumé IA d'un média — `null` quand il n'a pas encore été généré (AI-04).
final summaryProvider = FutureProvider.autoDispose.family<String?, String>((
  ref,
  videoId,
) {
  return ref.watch(videoRepositoryProvider).getSummary(videoId);
});
