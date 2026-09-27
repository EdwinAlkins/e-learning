import { z } from 'zod';

export const backgroundJobDtoSchema = z.object({
  id: z.string(),
  kind: z.enum([
    'media_conversion',
    'transcription',
    'summary',
    'rag_index_video',
    'rag_index_formation',
  ]),
  status: z.enum(['queued', 'running', 'succeeded', 'failed', 'cancelled']),
  progress: z.number(),
  message: z.string(),
});

export const videoDtoSchema = z.object({
  id: z.string(),
  title: z.string(),
  duration: z.number(),
  position: z.number(),
  kind: z.enum(['video', 'audio']),
  processing_status: z.enum(['ready', 'processing', 'failed']),
  transcription_status: z.enum(['none', 'processing', 'ready', 'failed']),
  summary_status: z.enum(['none', 'processing', 'ready', 'failed']),
  active_jobs: z.array(backgroundJobDtoSchema),
});

export const documentDtoSchema = z.object({
  id: z.string(),
  title: z.string(),
  position: z.number(),
  filename: z.string(),
  mime_type: z.string().nullable(),
  video_id: z.string().nullable(),
});

export const chapterDtoSchema = z.object({
  id: z.string(),
  name: z.string(),
  slug: z.string(),
  position: z.number(),
  videos: z.array(videoDtoSchema),
  documents: z.array(documentDtoSchema),
});

export const formationDtoSchema = z.object({
  id: z.string(),
  name: z.string(),
  slug: z.string(),
  chapters: z.array(chapterDtoSchema),
});

export const catalogDtoSchema = z.object({
  formations: z.array(formationDtoSchema),
});

export type BackgroundJobDto = z.infer<typeof backgroundJobDtoSchema>;
export type VideoDto = z.infer<typeof videoDtoSchema>;
export type DocumentDto = z.infer<typeof documentDtoSchema>;
export type ChapterDto = z.infer<typeof chapterDtoSchema>;
export type FormationDto = z.infer<typeof formationDtoSchema>;
export type CatalogDto = z.infer<typeof catalogDtoSchema>;
