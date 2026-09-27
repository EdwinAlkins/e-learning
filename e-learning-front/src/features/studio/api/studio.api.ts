import {
  chapterDtoSchema,
  documentDtoSchema,
  formationDtoSchema,
  videoDtoSchema,
} from '../../../entities/formation/dto';
import {
  toChapter,
  toDocument,
  toFormation,
  toVideo,
} from '../../../entities/formation/mappers';
import { parseApiResponse } from '../../../shared/api/contracts';
import { API_BASE_URL, httpClient } from '../../../shared/api/http-client';
import type {
  Chapter,
  Document,
  Formation,
  MoveVideoRequest,
  PatchChapterPayload,
  PatchFormationPayload,
  PatchVideoPayload,
  Video,
} from '../../../types';

export type UploadProgressCallback = (progress: number) => void;

const uploadProgress = (callback?: UploadProgressCallback) =>
  callback
    ? {
        onUploadProgress: (event: { loaded: number; total?: number }) => {
          if (event.total) callback(Math.round((event.loaded / event.total) * 100));
        },
      }
    : {};

export const studioApi = {
  createFormation: async (name: string): Promise<Formation> => {
    const response = await httpClient.post('/formations', { name });
    return toFormation(
      parseApiResponse(formationDtoSchema, response.data, 'POST /formations')
    );
  },

  patchFormation: async (
    formationId: string,
    payload: PatchFormationPayload
  ): Promise<Formation> => {
    const response = await httpClient.patch(`/formations/${formationId}`, payload);
    return toFormation(
      parseApiResponse(formationDtoSchema, response.data, 'PATCH /formations/{formation_id}')
    );
  },

  deleteFormation: async (formationId: string): Promise<void> => {
    await httpClient.delete(`/formations/${formationId}`);
  },

  createChapter: async (formationId: string, name: string): Promise<Chapter> => {
    const response = await httpClient.post(`/formations/${formationId}/chapters`, { name });
    return toChapter(
      parseApiResponse(chapterDtoSchema, response.data, 'POST /formations/{formation_id}/chapters')
    );
  },

  patchChapter: async (chapterId: string, payload: PatchChapterPayload): Promise<Chapter> => {
    const response = await httpClient.patch(`/chapters/${chapterId}`, payload);
    return toChapter(
      parseApiResponse(chapterDtoSchema, response.data, 'PATCH /chapters/{chapter_id}')
    );
  },

  deleteChapter: async (chapterId: string): Promise<void> => {
    await httpClient.delete(`/chapters/${chapterId}`);
  },

  createVideo: async (
    chapterId: string,
    data: { title: string; file: File },
    onProgress?: UploadProgressCallback
  ): Promise<Video> => {
    const formData = new FormData();
    formData.append('title', data.title);
    formData.append('file', data.file);
    const response = await httpClient.post(`/chapters/${chapterId}/videos`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      ...uploadProgress(onProgress),
    });
    return toVideo(
      parseApiResponse(videoDtoSchema, response.data, 'POST /chapters/{chapter_id}/videos')
    );
  },

  patchVideo: async (
    videoId: string,
    payload: PatchVideoPayload,
    onProgress?: UploadProgressCallback
  ): Promise<Video> => {
    if (payload.file) {
      const formData = new FormData();
      if (payload.title) formData.append('title', payload.title);
      formData.append('file', payload.file);
      const response = await httpClient.patch(`/videos/${videoId}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        ...uploadProgress(onProgress),
      });
      return toVideo(
        parseApiResponse(videoDtoSchema, response.data, 'PATCH /videos/{video_id}')
      );
    }

    const response = await httpClient.patch(`/videos/${videoId}`, { title: payload.title });
    return toVideo(
      parseApiResponse(videoDtoSchema, response.data, 'PATCH /videos/{video_id}')
    );
  },

  deleteVideo: async (videoId: string): Promise<void> => {
    await httpClient.delete(`/videos/${videoId}`);
  },

  reorderVideos: async (chapterId: string, videoIds: string[]): Promise<Chapter> => {
    const response = await httpClient.put(`/chapters/${chapterId}/videos/order`, {
      video_ids: videoIds,
    });
    return toChapter(
      parseApiResponse(chapterDtoSchema, response.data, 'PUT /chapters/{chapter_id}/videos/order')
    );
  },

  reorderChapters: async (formationId: string, chapterIds: string[]): Promise<Formation> => {
    const response = await httpClient.put(`/formations/${formationId}/chapters/order`, {
      chapter_ids: chapterIds,
    });
    return toFormation(
      parseApiResponse(
        formationDtoSchema,
        response.data,
        'PUT /formations/{formation_id}/chapters/order'
      )
    );
  },

  moveVideo: async (
    fromChapterId: string,
    videoId: string,
    toChapterId: string,
    toIndex?: number
  ): Promise<Formation> => {
    const payload: MoveVideoRequest | null =
      toIndex === undefined ? null : { position: toIndex };
    const response = await httpClient.patch(
      `/chapters/${fromChapterId}/${toChapterId}/${videoId}`,
      payload
    );
    return toFormation(
      parseApiResponse(formationDtoSchema, response.data, 'PATCH /chapters/{source}/{target}/{video_id}')
    );
  },

  createDocument: async (
    chapterId: string,
    data: { title: string; file: File; videoId?: string | null },
    onProgress?: UploadProgressCallback
  ): Promise<Document> => {
    const formData = new FormData();
    formData.append('title', data.title);
    formData.append('file', data.file);
    if (data.videoId) formData.append('video_id', data.videoId);
    const response = await httpClient.post(`/chapters/${chapterId}/docs`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      ...uploadProgress(onProgress),
    });
    return toDocument(
      parseApiResponse(documentDtoSchema, response.data, 'POST /chapters/{chapter_id}/docs')
    );
  },

  patchDocument: async (
    documentId: string,
    payload: { title?: string; video_id?: string | null }
  ): Promise<Document> => {
    const response = await httpClient.patch(`/docs/${documentId}`, payload);
    return toDocument(
      parseApiResponse(documentDtoSchema, response.data, 'PATCH /docs/{document_id}')
    );
  },

  deleteDocument: async (documentId: string): Promise<void> => {
    await httpClient.delete(`/docs/${documentId}`);
  },

  startTranscription: async (videoId: string): Promise<Video> => {
    const response = await httpClient.post(`/videos/${videoId}/transcription`);
    return toVideo(
      parseApiResponse(videoDtoSchema, response.data, 'POST /videos/{video_id}/transcription')
    );
  },

  startMediaConversion: async (videoId: string): Promise<Video> => {
    const response = await httpClient.post(`/videos/${videoId}/conversion`);
    return toVideo(
      parseApiResponse(videoDtoSchema, response.data, 'POST /videos/{video_id}/conversion')
    );
  },

  generateVideoSummary: async (videoId: string): Promise<Video> => {
    const response = await httpClient.post(`/videos/${videoId}/summary/generate`);
    return toVideo(
      parseApiResponse(
        videoDtoSchema,
        response.data,
        'POST /videos/{video_id}/summary/generate'
      )
    );
  },

  documentFileUrl: (documentId: string): string =>
    `${API_BASE_URL}/docs/${documentId}/file`,
};
