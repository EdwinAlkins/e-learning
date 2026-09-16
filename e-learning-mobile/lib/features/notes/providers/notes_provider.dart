import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../data/models/models.dart';
import '../../../data/repositories/note_repository.dart';

/// Notes d'un média, triées par timecode croissant (NOTE-03).
final notesProvider = FutureProvider.autoDispose.family<List<Note>, String>((
  ref,
  videoId,
) {
  return ref.watch(noteRepositoryProvider).list(videoId);
});
