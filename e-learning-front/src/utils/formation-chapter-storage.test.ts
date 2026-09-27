import { beforeEach, describe, expect, it } from 'vitest';
import type { Formation } from '../types';
import {
  getChapterExpandedKey,
  loadChapterExpandedState,
  saveChapterExpanded,
} from './formation-chapter-storage';

const formation: Formation = {
  id: 'formation-1',
  name: 'Infrastructure',
  chapters: [
    { id: 'chapter-2', name: 'Pratique', position: 1, videos: [] },
    { id: 'chapter-1', name: 'Fondations', position: 0, videos: [] },
  ],
};

beforeEach(() => localStorage.clear());

describe('formation chapter storage', () => {
  it('ouvre seulement le premier chapitre ordonné en l’absence de préférence', () => {
    expect(loadChapterExpandedState(formation)).toEqual({
      'chapter-1': true,
      'chapter-2': false,
    });
  });

  it('restaure les préférences enregistrées par formation et chapitre', () => {
    saveChapterExpanded(formation.id, 'chapter-1', false);
    saveChapterExpanded(formation.id, 'chapter-2', true);

    expect(localStorage.getItem(getChapterExpandedKey(formation.id, 'chapter-2'))).toBe(
      'true'
    );
    expect(loadChapterExpandedState(formation)).toEqual({
      'chapter-1': false,
      'chapter-2': true,
    });
  });
});
