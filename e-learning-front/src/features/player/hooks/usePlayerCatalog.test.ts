import { describe, expect, it } from 'vitest';
import type { Formation } from '../../../types';
import { findVideoInCatalog } from './usePlayerCatalog';

const formations: Formation[] = [
  {
    id: 'formation-1',
    name: 'Architecture',
    chapters: [
      {
        id: 'chapter-1',
        name: 'Fondations',
        videos: [
          { id: 'video-1', title: 'Introduction', duration: 60 },
          { id: 'video-2', title: 'Composants', duration: 120 },
        ],
      },
    ],
  },
];

describe('findVideoInCatalog', () => {
  it('retourne la vidéo avec sa formation et son chapitre', () => {
    expect(findVideoInCatalog(formations, 'video-2')).toEqual({
      video: formations[0].chapters[0].videos[1],
      formation: formations[0],
      chapterId: 'chapter-1',
    });
  });

  it('retourne null pour une vidéo absente', () => {
    expect(findVideoInCatalog(formations, 'video-404')).toBeNull();
  });
});
