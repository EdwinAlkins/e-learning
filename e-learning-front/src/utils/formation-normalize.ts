import type { Chapter, Document, Formation, Video } from '../types';

/** Normalise les ids API en strings et aligne `position` → `sortOrder` pour le tri UI. */
export const normalizeApiVideo = (video: Video): Video => {
  const position = video.position ?? video.sortOrder;
  return {
    ...video,
    id: String(video.id),
    position,
    sortOrder: position,
    kind: video.kind === 'audio' ? 'audio' : 'video',
    processing_status: video.processing_status ?? 'ready',
    transcription_status: video.transcription_status ?? 'none',
    summary_status: video.summary_status ?? 'none',
    active_jobs: (video.active_jobs ?? []).map((job) => ({
      id: String(job.id),
      kind: job.kind,
      status: job.status,
      progress: typeof job.progress === 'number' ? job.progress : 0,
      message: job.message ?? '',
    })),
  };
};

export const normalizeApiDocument = (document: Document): Document => ({
  ...document,
  id: String(document.id),
  video_id: document.video_id ? String(document.video_id) : null,
  filename: document.filename ?? '',
  position: document.position ?? 0,
});

export const normalizeApiChapter = (chapter: Chapter): Chapter => ({
  ...chapter,
  id: String(chapter.id),
  position: chapter.position,
  videos: (chapter.videos ?? []).map(normalizeApiVideo),
  documents: (chapter.documents ?? []).map(normalizeApiDocument),
});

export const normalizeApiFormation = (formation: Formation): Formation => ({
  ...formation,
  id: String(formation.id),
  chapters: (formation.chapters ?? []).map(normalizeApiChapter),
});

/** @deprecated Utiliser normalizeApiFormation pour les réponses API réelles. */
export const normalizeFormation = (formation: Formation): Formation =>
  normalizeApiFormation(formation);

export const prefixWithNumber = (label: string, index: number): string => {
  if (/^\d+\.\s/.test(label.trim())) {
    return label.trim();
  }
  return `${index}. ${label.trim()}`;
};
