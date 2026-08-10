import type {
  Chapter,
  Document,
  Formation,
  PatchChapterPayload,
  PatchFormationPayload,
  PatchVideoPayload,
  Video,
} from '../types';
import { apiService } from './api';

export type UploadProgressCallback = (progress: number) => void;

export const studioApi = {
  getFormations: (): Promise<Formation[]> => apiService.getFormations(),

  createFormation: (name: string): Promise<Formation> => apiService.createFormation(name),

  patchFormation: (id: string, payload: PatchFormationPayload): Promise<Formation> =>
    apiService.patchFormation(id, payload),

  deleteFormation: (id: string): Promise<void> => apiService.deleteFormation(id),

  createChapter: (formationId: string, name: string): Promise<Chapter> =>
    apiService.createChapter(formationId, name),

  patchChapter: (
    _formationId: string,
    chapterId: string,
    payload: PatchChapterPayload
  ): Promise<Chapter> => apiService.patchChapter(chapterId, payload),

  deleteChapter: (_formationId: string, chapterId: string): Promise<void> =>
    apiService.deleteChapter(chapterId),

  createVideo: (
    _formationId: string,
    chapterId: string,
    data: { title: string; file: File },
    onProgress?: UploadProgressCallback
  ): Promise<Video> => apiService.createVideo(chapterId, data.title, data.file, onProgress),

  patchVideo: (
    _formationId: string,
    _chapterId: string,
    videoId: string,
    payload: PatchVideoPayload,
    onProgress?: UploadProgressCallback
  ): Promise<Video> => apiService.patchVideo(videoId, payload, onProgress),

  deleteVideo: (_formationId: string, _chapterId: string, videoId: string): Promise<void> =>
    apiService.deleteVideo(videoId),

  reorderVideos: (chapterId: string, orderedVideoIds: string[]): Promise<Chapter> =>
    apiService.putChapterVideoOrder(chapterId, orderedVideoIds),

  reorderChapters: (formationId: string, orderedChapterIds: string[]): Promise<Formation> =>
    apiService.putFormationChapterOrder(formationId, orderedChapterIds),

  fetchFormationById: (formationId: string): Promise<Formation> =>
    apiService.getFormation(formationId),

  /** Déplace une vidéo entre chapitres ; `toIndex` → body `{ position }`. */
  moveVideo: (
    fromChapterId: string,
    videoId: string,
    toChapterId: string,
    toIndex?: number
  ): Promise<Formation> =>
    apiService.moveVideoBetweenChapters(
      fromChapterId,
      toChapterId,
      videoId,
      toIndex === undefined ? undefined : { position: toIndex }
    ),

  createDocument: (
    chapterId: string,
    data: { title: string; file: File; videoId?: string | null },
    onProgress?: UploadProgressCallback
  ): Promise<Document> => apiService.createChapterDocument(chapterId, data, onProgress),

  patchDocument: (
    documentId: string,
    payload: { title?: string; video_id?: string | null }
  ): Promise<Document> => apiService.patchDocument(documentId, payload),

  deleteDocument: (documentId: string): Promise<void> => apiService.deleteDocument(documentId),

  startTranscription: (videoId: string): Promise<Video> => apiService.startTranscription(videoId),

  startMediaConversion: (videoId: string): Promise<Video> =>
    apiService.startMediaConversion(videoId),

  generateVideoSummary: (videoId: string): Promise<Video> =>
    apiService.generateVideoSummary(videoId),
};
