/// Statuts renvoyés par l'API pour la conversion, la transcription et le résumé.
class MediaStatus {
  static const none = 'none';
  static const pending = 'pending';
  static const processing = 'processing';
  static const ready = 'ready';
  static const failed = 'failed';
}

/// `kind` des jobs asynchrones exposés dans `active_jobs`.
class JobKind {
  static const mediaConversion = 'media_conversion';
  static const transcription = 'transcription';
  static const summary = 'summary';
  static const ragIndexVideo = 'rag_index_video';
  static const ragIndexFormation = 'rag_index_formation';
}

class BackgroundJob {
  const BackgroundJob({
    required this.id,
    required this.kind,
    required this.status,
    this.progress = 0,
    this.message,
  });

  final String id;
  final String kind;
  final String status;
  final int progress;
  final String? message;

  bool get isActive => status == 'queued' || status == 'running';

  /// `Transcription… 42%` — le pourcentage n'est ajouté que s'il est exploitable.
  String label(String fallback) {
    final pct = progress.clamp(0, 100);
    return pct > 0 ? '$fallback $pct%' : fallback;
  }

  factory BackgroundJob.fromJson(Map<String, dynamic> json) {
    return BackgroundJob(
      id: '${json['id']}',
      kind: '${json['kind'] ?? ''}',
      status: '${json['status'] ?? ''}',
      progress: (json['progress'] as num?)?.toInt() ?? 0,
      message: json['message'] as String?,
    );
  }
}

class DocumentItem {
  const DocumentItem({
    required this.id,
    required this.title,
    this.position = 0,
    this.filename = '',
    this.mimeType,
    this.videoId,
  });

  final String id;
  final String title;
  final int position;
  final String filename;
  final String? mimeType;
  final String? videoId;

  factory DocumentItem.fromJson(Map<String, dynamic> json) {
    return DocumentItem(
      id: '${json['id']}',
      title: '${json['title'] ?? ''}',
      position: (json['position'] as num?)?.toInt() ?? 0,
      filename: '${json['filename'] ?? ''}',
      mimeType: json['mime_type'] as String? ?? json['mimeType'] as String?,
      videoId: json['video_id'] != null
          ? '${json['video_id']}'
          : json['videoId']?.toString(),
    );
  }
}

class VideoItem {
  const VideoItem({
    required this.id,
    required this.title,
    this.duration = 0,
    this.position = 0,
    this.kind = 'video',
    this.processingStatus = 'ready',
    this.transcriptionStatus = 'none',
    this.summaryStatus = 'none',
    this.activeJobs = const [],
  });

  final String id;
  final String title;
  final double duration;
  final int position;
  final String kind;
  final String processingStatus;
  final String transcriptionStatus;
  final String summaryStatus;
  final List<BackgroundJob> activeJobs;

  bool get isAudio => kind == 'audio';
  bool get isPlayable => processingStatus == MediaStatus.ready;
  bool get isConverting => processingStatus == MediaStatus.processing;
  bool get conversionFailed => processingStatus == MediaStatus.failed;
  bool get hasSummary => summaryStatus == MediaStatus.ready;
  bool get hasTranscription => transcriptionStatus == MediaStatus.ready;

  /// Job actif (queued/running) du [kind] demandé, `null` sinon.
  BackgroundJob? activeJob(String kind) {
    for (final job in activeJobs) {
      if (job.kind == kind && job.isActive) return job;
    }
    return null;
  }

  bool get hasRunningAiJob =>
      transcriptionStatus == MediaStatus.processing ||
      summaryStatus == MediaStatus.processing ||
      processingStatus == MediaStatus.processing;

  VideoItem copyWith({
    String? title,
    double? duration,
    String? kind,
    String? processingStatus,
    String? transcriptionStatus,
    String? summaryStatus,
    List<BackgroundJob>? activeJobs,
  }) {
    return VideoItem(
      id: id,
      title: title ?? this.title,
      duration: duration ?? this.duration,
      position: position,
      kind: kind ?? this.kind,
      processingStatus: processingStatus ?? this.processingStatus,
      transcriptionStatus: transcriptionStatus ?? this.transcriptionStatus,
      summaryStatus: summaryStatus ?? this.summaryStatus,
      activeJobs: activeJobs ?? this.activeJobs,
    );
  }

  factory VideoItem.fromJson(Map<String, dynamic> json) {
    final jobs =
        (json['active_jobs'] as List?) ?? (json['activeJobs'] as List?) ?? [];
    return VideoItem(
      id: '${json['id']}',
      title: '${json['title'] ?? ''}',
      duration: (json['duration'] as num?)?.toDouble() ?? 0,
      position:
          (json['position'] as num?)?.toInt() ??
          (json['sortOrder'] as num?)?.toInt() ??
          0,
      kind: '${json['kind'] ?? 'video'}',
      processingStatus:
          '${json['processing_status'] ?? json['processingStatus'] ?? 'ready'}',
      transcriptionStatus:
          '${json['transcription_status'] ?? json['transcriptionStatus'] ?? 'none'}',
      summaryStatus:
          '${json['summary_status'] ?? json['summaryStatus'] ?? 'none'}',
      activeJobs: jobs
          .whereType<Map<String, dynamic>>()
          .map(BackgroundJob.fromJson)
          .toList(),
    );
  }
}

class ChapterItem {
  const ChapterItem({
    required this.id,
    required this.name,
    this.slug,
    this.position = 0,
    this.videos = const [],
    this.documents = const [],
  });

  final String id;
  final String name;
  final String? slug;
  final int position;
  final List<VideoItem> videos;
  final List<DocumentItem> documents;

  ChapterItem copyWith({
    List<VideoItem>? videos,
    List<DocumentItem>? documents,
  }) {
    return ChapterItem(
      id: id,
      name: name,
      slug: slug,
      position: position,
      videos: videos ?? this.videos,
      documents: documents ?? this.documents,
    );
  }

  factory ChapterItem.fromJson(Map<String, dynamic> json) {
    return ChapterItem(
      id: '${json['id']}',
      name: '${json['name'] ?? ''}',
      slug: json['slug'] as String?,
      position: (json['position'] as num?)?.toInt() ?? 0,
      videos: ((json['videos'] as List?) ?? [])
          .whereType<Map<String, dynamic>>()
          .map(VideoItem.fromJson)
          .toList(),
      documents: ((json['documents'] as List?) ?? [])
          .whereType<Map<String, dynamic>>()
          .map(DocumentItem.fromJson)
          .toList(),
    );
  }
}

class Formation {
  const Formation({
    required this.id,
    required this.name,
    this.slug,
    this.chapters = const [],
  });

  final String id;
  final String name;
  final String? slug;
  final List<ChapterItem> chapters;

  Formation copyWith({List<ChapterItem>? chapters}) {
    return Formation(
      id: id,
      name: name,
      slug: slug,
      chapters: chapters ?? this.chapters,
    );
  }

  factory Formation.fromJson(Map<String, dynamic> json) {
    return Formation(
      id: '${json['id']}',
      name: '${json['name'] ?? ''}',
      slug: json['slug'] as String?,
      chapters: ((json['chapters'] as List?) ?? [])
          .whereType<Map<String, dynamic>>()
          .map(ChapterItem.fromJson)
          .toList(),
    );
  }
}

class Note {
  const Note({
    required this.id,
    required this.videoId,
    required this.timecode,
    required this.content,
    this.createdAt,
  });

  final String id;
  final String videoId;
  final double timecode;
  final String content;
  final DateTime? createdAt;

  factory Note.fromJson(Map<String, dynamic> json) {
    final rawDate = json['created_at'] ?? json['createdAt'];
    return Note(
      id: '${json['id']}',
      videoId: '${json['video_id'] ?? json['videoId']}',
      timecode: (json['timecode'] as num?)?.toDouble() ?? 0,
      content: '${json['content'] ?? ''}',
      createdAt: rawDate is String ? DateTime.tryParse(rawDate) : null,
    );
  }
}

class VideoProgressItem {
  const VideoProgressItem({
    required this.id,
    required this.title,
    this.progressPercentage = 0,
  });

  final String id;
  final String title;
  final double progressPercentage;

  factory VideoProgressItem.fromJson(Map<String, dynamic> json) {
    return VideoProgressItem(
      id: '${json['id']}',
      title: '${json['title'] ?? ''}',
      progressPercentage:
          (json['progress_percentage'] as num?)?.toDouble() ?? 0,
    );
  }
}

class ChapterProgress {
  const ChapterProgress({
    required this.name,
    this.videos = const [],
    this.progressPercentage = 0,
  });

  final String name;
  final List<VideoProgressItem> videos;
  final double progressPercentage;

  factory ChapterProgress.fromJson(Map<String, dynamic> json) {
    return ChapterProgress(
      name: '${json['name'] ?? ''}',
      videos: ((json['videos'] as List?) ?? [])
          .whereType<Map<String, dynamic>>()
          .map(VideoProgressItem.fromJson)
          .toList(),
      progressPercentage:
          (json['progress_percentage'] as num?)?.toDouble() ?? 0,
    );
  }
}

class FormationProgress {
  const FormationProgress({
    required this.name,
    this.chapters = const [],
    this.progressPercentage = 0,
  });

  final String name;
  final List<ChapterProgress> chapters;
  final double progressPercentage;

  factory FormationProgress.fromJson(Map<String, dynamic> json) {
    return FormationProgress(
      name: '${json['name'] ?? ''}',
      chapters: ((json['chapters'] as List?) ?? [])
          .whereType<Map<String, dynamic>>()
          .map(ChapterProgress.fromJson)
          .toList(),
      progressPercentage:
          (json['progress_percentage'] as num?)?.toDouble() ?? 0,
    );
  }
}

class RagCitation {
  const RagCitation({
    this.videoId,
    this.documentId,
    required this.title,
    required this.source,
    required this.excerpt,
  });

  final String? videoId;
  final String? documentId;
  final String title;
  final String source;
  final String excerpt;

  factory RagCitation.fromJson(Map<String, dynamic> json) {
    return RagCitation(
      videoId: json['video_id'] != null ? '${json['video_id']}' : null,
      documentId: json['document_id'] != null ? '${json['document_id']}' : null,
      title: '${json['title'] ?? ''}',
      source: '${json['source'] ?? ''}',
      excerpt: '${json['excerpt'] ?? ''}',
    );
  }
}

class AskFormationResponse {
  const AskFormationResponse({required this.answer, this.citations = const []});

  final String answer;
  final List<RagCitation> citations;

  factory AskFormationResponse.fromJson(Map<String, dynamic> json) {
    return AskFormationResponse(
      answer: '${json['answer'] ?? ''}',
      citations: ((json['citations'] as List?) ?? [])
          .whereType<Map<String, dynamic>>()
          .map(RagCitation.fromJson)
          .toList(),
    );
  }
}
