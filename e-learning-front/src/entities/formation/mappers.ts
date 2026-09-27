import type { Chapter, Document, Formation, Video } from '../../types';
import type { ChapterDto, DocumentDto, FormationDto, VideoDto } from './dto';

export const toVideo = (dto: VideoDto): Video => ({
  ...dto,
  sortOrder: dto.position,
});

export const toDocument = (dto: DocumentDto): Document => ({ ...dto });

export const toChapter = (dto: ChapterDto): Chapter => ({
  ...dto,
  videos: dto.videos.map(toVideo),
  documents: dto.documents.map(toDocument),
});

export const toFormation = (dto: FormationDto): Formation => ({
  ...dto,
  chapters: dto.chapters.map(toChapter),
});
