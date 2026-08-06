import type { Chapter, Document, Video } from '../../../types';

export type DeleteTarget =
  | { type: 'chapter'; chapter: Chapter }
  | { type: 'video'; chapter: Chapter; video: Video }
  | { type: 'document'; chapter: Chapter; document: Document };

export type DraggedVideo = { chapterId: string; videoId: string };

export type ChapterDialogState = {
  open: boolean;
  mode: 'create' | 'edit';
  chapter?: Chapter;
};

export type VideoDialogState = {
  open: boolean;
  mode: 'create' | 'edit';
  chapter: Chapter;
  video?: Video;
} | null;

export type DocumentDialogState = {
  open: boolean;
  mode: 'create' | 'edit';
  chapter: Chapter;
  document?: Document;
} | null;

export type MoveDialogState = {
  chapter: Chapter;
  video: Video;
} | null;
