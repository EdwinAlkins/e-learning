import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../data/models/models.dart';
import '../../../data/repositories/formation_repository.dart';

class PlayerContext {
  const PlayerContext({
    required this.video,
    required this.chapter,
    required this.formation,
    this.previousVideo,
    this.nextVideo,
  });

  final VideoItem video;
  final ChapterItem chapter;
  final Formation formation;
  final VideoItem? previousVideo;
  final VideoItem? nextVideo;

  /// Documents rattachés à la vidéo courante (DOC-02).
  List<DocumentItem> get videoDocuments =>
      chapter.documents.where((doc) => doc.videoId == video.id).toList();
}

typedef PlayerArgs = ({String videoId, String? formationId});

final playerContextProvider = FutureProvider.autoDispose
    .family<PlayerContext, PlayerArgs>((ref, args) async {
      final repo = ref.watch(formationRepositoryProvider);

      Formation? formation;
      if (args.formationId != null) {
        formation = await repo.getById(args.formationId!);
      } else {
        // Sans formationId (deep link), on retrouve la vidéo dans le catalogue.
        final all = await repo.list();
        for (final candidate in all) {
          final found = candidate.chapters.any(
            (c) => c.videos.any((v) => v.id == args.videoId),
          );
          if (found) {
            formation = await repo.getById(candidate.id);
            break;
          }
        }
      }
      if (formation == null) {
        throw Exception('Vidéo introuvable dans le catalogue.');
      }

      final flat = <({VideoItem video, ChapterItem chapter})>[
        for (final chapter in formation.chapters)
          for (final video in chapter.videos) (video: video, chapter: chapter),
      ];

      final index = flat.indexWhere((e) => e.video.id == args.videoId);
      if (index < 0) {
        throw Exception('Vidéo introuvable dans cette formation.');
      }

      final current = flat[index];
      return PlayerContext(
        video: current.video,
        chapter: current.chapter,
        formation: formation,
        previousVideo: index > 0 ? flat[index - 1].video : null,
        nextVideo: index < flat.length - 1 ? flat[index + 1].video : null,
      );
    });
