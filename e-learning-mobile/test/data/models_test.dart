import 'package:e_learning_mobile/data/models/models.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('VideoItem', () {
    test('lit les statuts snake_case et les jobs actifs', () {
      final video = VideoItem.fromJson({
        'id': 12,
        'title': '1. Introduction',
        'duration': 125.5,
        'kind': 'audio',
        'processing_status': 'ready',
        'transcription_status': 'processing',
        'summary_status': 'none',
        'active_jobs': [
          {
            'id': 'j1',
            'kind': 'transcription',
            'status': 'running',
            'progress': 42,
            'message': 'Whisper',
          },
          {'id': 'j2', 'kind': 'summary', 'status': 'done', 'progress': 100},
        ],
      });

      expect(video.id, '12');
      expect(video.isAudio, isTrue);
      expect(video.isPlayable, isTrue);
      expect(video.hasRunningAiJob, isTrue);
      expect(video.activeJob(JobKind.transcription)?.progress, 42);
      // Un job terminé n'est plus « actif ».
      expect(video.activeJob(JobKind.summary), isNull);
    });

    test('applique les valeurs par défaut sur une charge minimale', () {
      final video = VideoItem.fromJson({'id': 'v1', 'title': 'Média'});

      expect(video.kind, 'video');
      expect(video.processingStatus, MediaStatus.ready);
      expect(video.transcriptionStatus, MediaStatus.none);
      expect(video.hasSummary, isFalse);
      expect(video.hasRunningAiJob, isFalse);
    });

    test('copyWith ne modifie que les champs fournis', () {
      final video = VideoItem.fromJson({'id': 'v1', 'title': 'Média'});
      final updated = video.copyWith(summaryStatus: MediaStatus.ready);

      expect(updated.id, 'v1');
      expect(updated.title, 'Média');
      expect(updated.hasSummary, isTrue);
      expect(video.hasSummary, isFalse);
    });
  });

  group('BackgroundJob', () {
    test('label ajoute le pourcentage quand il est exploitable', () {
      const withProgress = BackgroundJob(
        id: 'j',
        kind: 'summary',
        status: 'running',
        progress: 60,
      );
      const withoutProgress = BackgroundJob(
        id: 'j',
        kind: 'summary',
        status: 'queued',
      );

      expect(withProgress.label('Génération…'), 'Génération… 60%');
      expect(withoutProgress.label('Génération…'), 'Génération…');
    });
  });

  group('Note', () {
    test('parse la date ISO et normalise les identifiants', () {
      final note = Note.fromJson({
        'id': 7,
        'video_id': 12,
        'timecode': 90,
        'content': '**Point clé**',
        'created_at': '2025-03-12T14:05:00Z',
      });

      expect(note.id, '7');
      expect(note.videoId, '12');
      expect(note.timecode, 90);
      expect(note.createdAt?.toUtc(), DateTime.utc(2025, 3, 12, 14, 5));
    });

    test('tolère une date absente ou invalide', () {
      final note = Note.fromJson({
        'id': '1',
        'video_id': 'v1',
        'content': 'note',
        'created_at': 'pas-une-date',
      });

      expect(note.createdAt, isNull);
      expect(note.timecode, 0);
    });
  });

  group('DocumentItem', () {
    test('lit mime_type et video_id', () {
      final doc = DocumentItem.fromJson({
        'id': 3,
        'title': 'Support',
        'position': 2,
        'filename': 'support.pdf',
        'mime_type': 'application/pdf',
        'video_id': 12,
      });

      expect(doc.id, '3');
      expect(doc.videoId, '12');
      expect(doc.mimeType, 'application/pdf');
    });
  });
}
