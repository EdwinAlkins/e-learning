import type { Chapter, Formation, Video } from '../types';
import { orderVideosByIds } from './formation';

export const mapFormations = (
  formations: Formation[],
  formationId: string,
  updater: (formation: Formation) => Formation
): Formation[] =>
  formations.map((formation) =>
    formation.id === formationId ? updater(formation) : formation
  );

export const upsertFormationInList = (
  formations: Formation[],
  formation: Formation
): Formation[] => {
  const index = formations.findIndex((item) => item.id === formation.id);
  if (index === -1) return [...formations, formation];
  const next = [...formations];
  next[index] = formation;
  return next;
};

export const removeFormationFromList = (
  formations: Formation[],
  formationId: string
): Formation[] => formations.filter((formation) => formation.id !== formationId);

export const addChapterToFormation = (
  formations: Formation[],
  formationId: string,
  chapter: Chapter
): Formation[] =>
  mapFormations(formations, formationId, (formation) => ({
    ...formation,
    chapters: [...formation.chapters, chapter],
  }));

export const updateChapterInFormation = (
  formations: Formation[],
  formationId: string,
  chapterId: string,
  chapter: Chapter
): Formation[] =>
  mapFormations(formations, formationId, (formation) => ({
    ...formation,
    chapters: formation.chapters.map((item) =>
      item.id === chapterId
        ? {
            ...item,
            name: chapter.name,
            ...(chapter.videos.length > 0 ? { videos: chapter.videos } : {}),
            ...(chapter.documents !== undefined ? { documents: chapter.documents } : {}),
          }
        : item
    ),
  }));

export const removeChapterFromFormation = (
  formations: Formation[],
  formationId: string,
  chapterId: string
): Formation[] =>
  mapFormations(formations, formationId, (formation) => ({
    ...formation,
    chapters: formation.chapters.filter((chapter) => chapter.id !== chapterId),
  }));

export const addVideoToChapter = (
  formations: Formation[],
  formationId: string,
  chapterId: string,
  video: Video
): Formation[] =>
  mapFormations(formations, formationId, (formation) => ({
    ...formation,
    chapters: formation.chapters.map((chapter) =>
      chapter.id === chapterId
        ? { ...chapter, videos: [...chapter.videos, video] }
        : chapter
    ),
  }));

export const updateVideoInFormation = (
  formations: Formation[],
  formationId: string,
  chapterId: string,
  videoId: string,
  video: Video
): Formation[] =>
  mapFormations(formations, formationId, (formation) => ({
    ...formation,
    chapters: formation.chapters.map((chapter) => {
      if (chapter.id !== chapterId) return chapter;
      return {
        ...chapter,
        videos: chapter.videos.map((item) =>
          item.id === videoId ? { ...item, ...video } : item
        ),
      };
    }),
  }));

export const removeVideoFromFormation = (
  formations: Formation[],
  formationId: string,
  chapterId: string,
  videoId: string
): Formation[] =>
  mapFormations(formations, formationId, (formation) => ({
    ...formation,
    chapters: formation.chapters.map((chapter) =>
      chapter.id === chapterId
        ? { ...chapter, videos: chapter.videos.filter((video) => video.id !== videoId) }
        : chapter
    ),
  }));

export const setChapterVideoOrder = (
  formations: Formation[],
  formationId: string,
  chapterId: string,
  orderedVideoIds: string[]
): Formation[] =>
  mapFormations(formations, formationId, (formation) => ({
    ...formation,
    chapters: formation.chapters.map((chapter) => {
      if (chapter.id !== chapterId) return chapter;
      return {
        ...chapter,
        videos: orderVideosByIds(chapter.videos, orderedVideoIds),
      };
    }),
  }));

export const replaceFormationInList = (
  formations: Formation[],
  formationId: string,
  nextFormation: Formation
): Formation[] => upsertFormationInList(
  formations.filter((formation) => formation.id !== formationId),
  nextFormation
);
