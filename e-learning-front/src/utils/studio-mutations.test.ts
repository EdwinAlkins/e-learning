import { describe, expect, it } from 'vitest';
import type { Formation } from '../types';
import {
  addChapterToFormation,
  removeVideoFromFormation,
  setChapterVideoOrder,
  setFormationChapterOrder,
  upsertFormationInList,
} from './studio-mutations';

const formationFixture = (): Formation => ({
  id: 'formation-1',
  name: 'Architecture',
  chapters: [
    {
      id: 'chapter-1',
      name: 'Fondations',
      position: 0,
      videos: [
        { id: 'video-1', title: 'Introduction', duration: 60, position: 1 },
        { id: 'video-2', title: 'Composants', duration: 120, position: 2 },
      ],
    },
    {
      id: 'chapter-2',
      name: 'Pratique',
      position: 1,
      videos: [],
    },
  ],
});

describe('studio mutations', () => {
  it('réordonne les vidéos sans modifier la formation source', () => {
    const source = formationFixture();
    const result = setChapterVideoOrder(
      [source],
      source.id,
      'chapter-1',
      ['video-2', 'video-1']
    );

    expect(result[0]).not.toBe(source);
    expect(result[0].chapters[0].videos).toEqual([
      expect.objectContaining({ id: 'video-2', position: 1, sortOrder: 1 }),
      expect.objectContaining({ id: 'video-1', position: 2, sortOrder: 2 }),
    ]);
    expect(source.chapters[0].videos.map((video) => video.id)).toEqual([
      'video-1',
      'video-2',
    ]);
  });

  it('réordonne les chapitres avec des positions API basées sur zéro', () => {
    const source = formationFixture();
    const result = setFormationChapterOrder(
      [source],
      source.id,
      ['chapter-2', 'chapter-1']
    );

    expect(result[0].chapters).toEqual([
      expect.objectContaining({ id: 'chapter-2', position: 0 }),
      expect.objectContaining({ id: 'chapter-1', position: 1 }),
    ]);
  });

  it('limite une suppression de vidéo au chapitre ciblé', () => {
    const source = formationFixture();
    const untouchedFormation = { ...source, id: 'formation-2' };
    const result = removeVideoFromFormation(
      [source, untouchedFormation],
      source.id,
      'chapter-1',
      'video-1'
    );

    expect(result[0].chapters[0].videos.map((video) => video.id)).toEqual(['video-2']);
    expect(result[1]).toBe(untouchedFormation);
  });

  it('ajoute puis remplace une formation dans une liste', () => {
    const source = formationFixture();
    const added = { ...source, id: 'formation-2', name: 'Réseau' };
    const withAdded = upsertFormationInList([source], added);
    const replacement = { ...added, name: 'Réseau avancé' };

    expect(withAdded).toEqual([source, added]);
    expect(upsertFormationInList(withAdded, replacement)).toEqual([source, replacement]);
  });

  it('ajoute un chapitre de manière immutable', () => {
    const source = formationFixture();
    const chapter = { id: 'chapter-3', name: 'Conclusion', videos: [] };
    const result = addChapterToFormation([source], source.id, chapter);

    expect(result[0].chapters).toHaveLength(3);
    expect(result[0].chapters.at(-1)).toBe(chapter);
    expect(source.chapters).toHaveLength(2);
  });
});
