import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../data/models/models.dart';
import '../../../data/repositories/usage_repository.dart';

/// Consommation IA sur une fenêtre de N jours.
final usageProvider = FutureProvider.autoDispose.family<UserTokenUsage, int>((
  ref,
  days,
) {
  return ref.watch(usageRepositoryProvider).getUsage(days);
});
