import type { Formation } from '../types';
import { sortChaptersByNumber } from './formation';

const STORAGE_KEY_CHAPTER = 'formation_accordion_chapter_';

export const getChapterExpandedKey = (formationId: string, chapterId: string): string =>
  `${STORAGE_KEY_CHAPTER}${formationId}_${chapterId}`;

export const saveChapterExpanded = (
  formationId: string,
  chapterId: string,
  expanded: boolean
): void => {
  if (typeof window === 'undefined') return;
  try {
    localStorage.setItem(getChapterExpandedKey(formationId, chapterId), String(expanded));
  } catch {
    // quota / private mode
  }
};

export function loadChapterExpandedState(formation: Formation): Record<string, boolean> {
  if (typeof window === 'undefined') return {};

  const loaded: Record<string, boolean> = {};
  try {
    sortChaptersByNumber(formation.chapters).forEach((chapter, chapterIndex) => {
      const saved = localStorage.getItem(getChapterExpandedKey(formation.id, chapter.id));
      loaded[chapter.id] = saved === null ? chapterIndex === 0 : saved === 'true';
    });
  } catch {
    sortChaptersByNumber(formation.chapters).forEach((chapter, chapterIndex) => {
      loaded[chapter.id] = chapterIndex === 0;
    });
  }
  return loaded;
}
