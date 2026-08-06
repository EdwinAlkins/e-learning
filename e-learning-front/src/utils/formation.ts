import type { Chapter, Video } from '../types';

export const getVideoNumber = (title: string): number => {
  const regex = /^(\d+)\.\s/;
  const match = regex.exec(title);
  if (match) return Number.parseInt(match[1], 10);
  return Infinity;
};

const videoOrder = (video: Video): number =>
  video.position ?? video.sortOrder ?? Number.POSITIVE_INFINITY;

const chapterOrder = (chapter: Chapter): number =>
  chapter.position ?? Number.POSITIVE_INFINITY;

export const sortVideosByNumber = (videos: Video[]): Video[] => {
  if (videos.some((video) => video.position !== undefined || video.sortOrder !== undefined)) {
    return [...videos].sort((a, b) => videoOrder(a) - videoOrder(b));
  }
  return [...videos].sort((a, b) => getVideoNumber(a.title) - getVideoNumber(b.title));
};

export const orderVideosByIds = (videos: Video[], orderedIds: string[]): Video[] => {
  const byId = new Map(videos.map((video) => [video.id, video]));
  return orderedIds.map((id, index) => {
    const position = index + 1;
    return { ...byId.get(id)!, position, sortOrder: position };
  });
};

export const getNextVideoSortOrder = (videos: Video[]): number =>
  videos.reduce((max, video) => Math.max(max, video.position ?? video.sortOrder ?? 0), 0) + 1;

export const sortChaptersByNumber = (chapters: Chapter[]): Chapter[] => {
  if (chapters.some((chapter) => chapter.position !== undefined)) {
    return [...chapters].sort((a, b) => chapterOrder(a) - chapterOrder(b));
  }
  return [...chapters].sort((a, b) => getVideoNumber(a.name) - getVideoNumber(b.name));
};
export const calculateChapterTotalDuration = (chapter: Chapter): number =>
  chapter.videos.reduce((total, video) => total + video.duration, 0);

export const calculateFormationTotalDuration = (formation: { chapters: Chapter[] }): number =>
  formation.chapters.reduce((total, chapter) => total + calculateChapterTotalDuration(chapter), 0);

/** Format compact pour les cartes : 2h05 */
export const formatDurationCompact = (totalSeconds: number): string => {
  const totalMinutes = Math.floor(Math.max(0, totalSeconds) / 60);
  if (totalMinutes === 0) return '—';
  const hours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;
  if (hours === 0) return `${minutes} min`;
  return `${hours}h${minutes.toString().padStart(2, '0')}`;
};

/** Format détaillé : 2:05 heures */
export const formatDurationDetailed = (totalSeconds: number): string => {
  const totalMinutes = Math.floor(totalSeconds / 60);
  const hours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;
  return `${hours}:${minutes.toString().padStart(2, '0')} heures`;
};

export const formatVideoDuration = (seconds: number): string => {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
};

export const flattenFormationVideos = (chapters: Chapter[]): Video[] => {
  const flatVideos: Video[] = [];
  for (const chapter of sortChaptersByNumber(chapters)) {
    flatVideos.push(...sortVideosByNumber(chapter.videos));
  }
  return flatVideos;
};

export const getChipColor = (percentage: number): 'primary' | 'default' =>
  percentage >= 99 ? 'primary' : 'default';

export const getChipBackgroundColor = (percentage: number): string | undefined => {
  if (percentage >= 99) return 'primary.main';
  if (percentage === 0) return 'white';
  return 'grey.300';
};

export const getChipBorderColor = (percentage: number): string | undefined => {
  if (percentage >= 99) return 'primary.main';
  if (percentage === 0) return 'grey.300';
  return 'grey.400';
};

export const getChipTextColor = (
  percentage: number,
  themeMode: 'light' | 'dark'
): string => {
  if (percentage >= 99) return themeMode === 'dark' ? 'black' : 'white';
  // Fonds chip (white / grey.300) toujours clairs → texte sombre
  return 'rgba(0, 0, 0, 0.87)';
};
