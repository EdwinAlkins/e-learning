import axios from 'axios';
import { z } from 'zod';
import { documentDtoSchema, videoDtoSchema } from '../../../entities/formation/dto';
import { toDocument, toVideo } from '../../../entities/formation/mappers';
import { parseApiResponse } from '../../../shared/api/contracts';
import { API_BASE_URL, httpClient } from '../../../shared/api/http-client';
import type { Document, Note, ProgressResponse, Video } from '../../../types';

export const playerApi = {
  getProgress: async (videoId: string): Promise<number | null> => {
    try {
      const response = await httpClient.get<ProgressResponse>(`/progress/${videoId}`);
      return response.data.last_position;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.status === 404) return null;
      throw error;
    }
  },

  saveProgress: async (videoId: string, position: number): Promise<void> => {
    await httpClient.post<ProgressResponse>(`/progress/${videoId}`, {
      last_position: position,
    });
  },

  getNotes: async (videoId: string): Promise<Note[]> => {
    const response = await httpClient.get<Note[]>(`/notes/${videoId}`);
    return response.data;
  },

  createNote: async (videoId: string, timecode: number, content: string): Promise<Note> => {
    const response = await httpClient.post<Note>(`/notes/${videoId}`, {
      timecode,
      content,
    });
    return response.data;
  },

  updateNote: async (noteId: string, content: string): Promise<Note> => {
    const response = await httpClient.put<Note>(`/notes/${noteId}`, { content });
    return response.data;
  },

  deleteNote: async (noteId: string): Promise<void> => {
    await httpClient.delete(`/notes/${noteId}`);
  },

  getVideoSummary: async (videoId: string): Promise<string> => {
    try {
      const response = await httpClient.get<{ summary: string }>(`/videos/${videoId}/summary`);
      return response.data.summary;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.status === 404) {
        throw new Error('Summary not available for this video');
      }
      throw error;
    }
  },

  updateVideoSummary: async (videoId: string, summary: string): Promise<string> => {
    const response = await httpClient.put<{ summary: string }>(`/videos/${videoId}/summary`, {
      summary,
    });
    return response.data.summary;
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

  getVideoTranscription: async (videoId: string): Promise<string> => {
    const response = await httpClient.get<{ content: string }>(
      `/videos/${videoId}/transcription`
    );
    return response.data.content;
  },

  getChapterDocuments: async (chapterId: string): Promise<Document[]> => {
    const response = await httpClient.get(`/docs/chapters/${chapterId}`);
    const dtos = parseApiResponse(
      z.array(documentDtoSchema),
      response.data,
      'GET /docs/chapters/{chapter_id}'
    );
    return dtos.map(toDocument);
  },

  documentFileUrl: (documentId: string, download = false): string =>
    `${API_BASE_URL}/docs/${documentId}/file${download ? '?download=true' : ''}`,
};
