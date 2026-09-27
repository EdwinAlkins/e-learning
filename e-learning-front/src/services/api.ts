import axios from 'axios';
import type { AxiosInstance } from 'axios';
import {
  normalizeApiChapter,
  normalizeApiDocument,
  normalizeApiFormation,
  normalizeApiVideo,
} from '../utils/formation-normalize';
import type {
  AdminUser,
  AskFormationResponse,
  CatalogResponse,
  Formation,
  FormationsProgressResponse,
  Note,
  ProgressResponse,
  FormationProgress,
  Chapter,
  Video,
  Document,
  PatchFormationPayload,
  PatchChapterPayload,
  PatchVideoPayload,
  MoveVideoRequest,
  UserTokenUsage,
  CurrentUser,
  UserListResponse,
  CreateUserPayload,
  UpdateUserPayload,
} from '../types';

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const extractFormationsArray = (data: unknown): Formation[] => {
  if (Array.isArray(data)) {
    return data;
  }
  if (typeof data === 'object' && data !== null) {
    const obj = data as Record<string, unknown>;
    if (Array.isArray(obj.formations)) return obj.formations as Formation[];
    if (Array.isArray(obj.data)) return obj.data as Formation[];
    if (Array.isArray(obj.items)) return obj.items as Formation[];
  }
  console.warn('Unexpected response format, returning empty array');
  return [];
};

// Session : cookie HttpOnly `access_token` posé par POST /auth/login. Il est
// illisible en JS et envoyé automatiquement (`withCredentials`), y compris par
// les balises <video>/<audio> et les liens de téléchargement (URL directes).
// `X-Requested-With` est exigé par l'API sur les écritures authentifiées par
// cookie (protection CSRF) ; on l'envoie sur toutes les requêtes.
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
    'X-Requested-With': 'XMLHttpRequest',
  },
});

interface AuthErrorHandlers {
  /** 401 : pas de session ou session expirée → retour à la connexion. */
  onUnauthorized?: () => void;
  /** 403 : session valide, droits insuffisants → « accès refusé », sans déconnexion. */
  onForbidden?: () => void;
}

let authErrorHandlers: AuthErrorHandlers = {};

/** Branché par le store d'auth (évite une dépendance circulaire api ↔ store). */
export function setAuthErrorHandlers(handlers: AuthErrorHandlers): void {
  authErrorHandlers = handlers;
}

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status;
    const url: string = error.config?.url ?? '';
    // Un échec de connexion n'est pas une session expirée.
    if (status === 401 && url !== '/auth/login') {
      authErrorHandlers.onUnauthorized?.();
    } else if (status === 403) {
      authErrorHandlers.onForbidden?.();
    }
    return Promise.reject(error);
  }
);

/** Message lisible pour une erreur d'API (`detail` FastAPI, sinon `fallback`). */
export function apiErrorMessage(error: unknown, fallback: string): string {
  if (axios.isAxiosError(error)) {
    if (error.response?.status === 429) {
      const retryAfter = Number(error.response.headers['retry-after']);
      const minutes = Number.isFinite(retryAfter) ? Math.ceil(retryAfter / 60) : null;
      return minutes
        ? `Trop de tentatives. Réessayez dans ${minutes} min.`
        : 'Trop de tentatives. Réessayez plus tard.';
    }
    const detail = error.response?.data?.detail;
    if (typeof detail === 'string') return detail;
    if (!error.response) return "Impossible de joindre l'API.";
  }
  return fallback;
}

// API functions
export const apiService = {
  /** OAuth2 password flow : l'API pose le cookie de session. */
  login: async (email: string, password: string): Promise<void> => {
    await api.post(
      '/auth/login',
      new URLSearchParams({ username: email, password }),
      { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
    );
  },

  logout: async (): Promise<void> => {
    await api.post('/auth/logout');
  },

  getMe: async (): Promise<CurrentUser> => {
    const response = await api.get<CurrentUser>('/auth/me');
    return response.data;
  },

  changePassword: async (currentPassword: string, newPassword: string): Promise<void> => {
    await api.patch('/auth/me/password', {
      current_password: currentPassword,
      new_password: newPassword,
    });
  },

  listUsers: async (offset: number, limit: number): Promise<UserListResponse> => {
    const response = await api.get<UserListResponse>('/admin/users', {
      params: { offset, limit },
    });
    return response.data;
  },

  createUser: async (payload: CreateUserPayload): Promise<AdminUser> => {
    const response = await api.post<AdminUser>('/admin/users', payload);
    return response.data;
  },

  updateUser: async (userId: string, payload: UpdateUserPayload): Promise<AdminUser> => {
    const response = await api.patch<AdminUser>(`/admin/users/${userId}`, payload);
    return response.data;
  },

  deleteUser: async (userId: string): Promise<void> => {
    await api.delete(`/admin/users/${userId}`);
  },

  getFormations: async (): Promise<Formation[]> => {
    const response = await api.get<CatalogResponse>('/formations');
    return extractFormationsArray(response.data).map(normalizeApiFormation);
  },

  getFormation: async (id: string): Promise<Formation> => {
    const response = await api.get<Formation>(`/formations/${id}`);
    return normalizeApiFormation(response.data);
  },

  askFormation: async (formationId: string, question: string): Promise<AskFormationResponse> => {
    try {
      const response = await api.post<AskFormationResponse>(
        `/formations/${encodeURIComponent(formationId)}/ask`,
        { question }
      );
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const detail = error.response?.data?.detail;
        if (typeof detail === 'string') {
          throw new Error(detail);
        }
      }
      throw error;
    }
  },

  indexFormation: async (formationId: string): Promise<void> => {
    await api.post(`/formations/${encodeURIComponent(formationId)}/index`);
  },

  getProgress: async (videoId: string): Promise<number | null> => {
    try {
      const response = await api.get<ProgressResponse>(`/progress/${videoId}`);
      return response.data.last_position;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.status === 404) {
        return null;
      }
      throw error;
    }
  },

  saveProgress: async (videoId: string, position: number): Promise<void> => {
    await api.post<ProgressResponse>(`/progress/${videoId}`, {
      last_position: position,
    });
  },

  getFormationProgress: async (formationId: string): Promise<FormationProgress> => {
    const response = await api.get<FormationProgress>(
      `/progress/formation/${encodeURIComponent(formationId)}`
    );
    return response.data;
  },

  getFormationsProgress: async (): Promise<Record<string, FormationProgress>> => {
    const response = await api.get<FormationsProgressResponse>('/progress/formations');
    return response.data.progress ?? {};
  },

  getTokenUsage: async (days: number): Promise<UserTokenUsage> => {
    const response = await api.get<UserTokenUsage>('/usage', { params: { days } });
    return response.data;
  },

  getNotes: async (videoId: string): Promise<Note[]> => {
    const response = await api.get<Note[]>(`/notes/${videoId}`);
    return response.data.map((note) => ({ ...note, id: String(note.id) }));
  },

  createNote: async (
    videoId: string,
    timecode: number,
    content: string
  ): Promise<Note> => {
    const response = await api.post<Note>(`/notes/${videoId}`, {
      timecode,
      content,
    });
    return { ...response.data, id: String(response.data.id) };
  },

  updateNote: async (noteId: string, content: string): Promise<Note> => {
    const response = await api.put<Note>(`/notes/${noteId}`, { content });
    return { ...response.data, id: String(response.data.id) };
  },

  deleteNote: async (noteId: string): Promise<void> => {
    await api.delete(`/notes/${noteId}`);
  },

  getVideoSummary: async (videoId: string): Promise<string> => {
    try {
      const response = await api.get<{ summary: string }>(`/videos/${videoId}/summary`);
      return response.data.summary;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.status === 404) {
        throw new Error('Summary not available for this video');
      }
      throw error;
    }
  },

  updateVideoSummary: async (videoId: string, summary: string): Promise<string> => {
    const response = await api.put<{ summary: string }>(`/videos/${videoId}/summary`, {
      summary,
    });
    return response.data.summary;
  },

  startTranscription: async (videoId: string): Promise<Video> => {
    const response = await api.post<Video>(`/videos/${videoId}/transcription`);
    return normalizeApiVideo(response.data);
  },

  startMediaConversion: async (videoId: string): Promise<Video> => {
    const response = await api.post<Video>(`/videos/${videoId}/conversion`);
    return normalizeApiVideo(response.data);
  },

  generateVideoSummary: async (videoId: string): Promise<Video> => {
    const response = await api.post<Video>(`/videos/${videoId}/summary/generate`);
    return normalizeApiVideo(response.data);
  },

  getVideoTranscription: async (videoId: string): Promise<string> => {
    const response = await api.get<{ content: string }>(`/videos/${videoId}/transcription`);
    return response.data.content;
  },

  createFormation: async (name: string): Promise<Formation> => {
    const response = await api.post<Formation>('/formations', { name });
    return normalizeApiFormation(response.data);
  },

  patchFormation: async (id: string, payload: PatchFormationPayload): Promise<Formation> => {
    const response = await api.patch<Formation>(`/formations/${id}`, payload);
    return normalizeApiFormation(response.data);
  },

  deleteFormation: async (id: string): Promise<void> => {
    await api.delete(`/formations/${id}`);
  },

  createChapter: async (formationId: string, name: string): Promise<Chapter> => {
    const response = await api.post<Chapter>(`/formations/${formationId}/chapters`, { name });
    return normalizeApiChapter(response.data);
  },

  patchChapter: async (chapterId: string, payload: PatchChapterPayload): Promise<Chapter> => {
    const response = await api.patch<Chapter>(`/chapters/${chapterId}`, payload);
    return normalizeApiChapter(response.data);
  },

  deleteChapter: async (chapterId: string): Promise<void> => {
    await api.delete(`/chapters/${chapterId}`);
  },

  createVideo: async (
    chapterId: string,
    title: string,
    file: File,
    onProgress?: (progress: number) => void
  ): Promise<Video> => {
    const formData = new FormData();
    formData.append('title', title);
    formData.append('file', file);

    const response = await api.post<Video>(`/chapters/${chapterId}/videos`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (event) => {
        if (event.total && onProgress) {
          onProgress(Math.round((event.loaded / event.total) * 100));
        }
      },
    });
    return normalizeApiVideo(response.data);
  },

  patchVideo: async (
    videoId: string,
    payload: PatchVideoPayload,
    onProgress?: (progress: number) => void
  ): Promise<Video> => {
    if (payload.file) {
      const formData = new FormData();
      if (payload.title) formData.append('title', payload.title);
      formData.append('file', payload.file);

      const response = await api.patch<Video>(`/videos/${videoId}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (event) => {
          if (event.total && onProgress) {
            onProgress(Math.round((event.loaded / event.total) * 100));
          }
        },
      });
      return normalizeApiVideo(response.data);
    }

    const response = await api.patch<Video>(`/videos/${videoId}`, {
      title: payload.title,
    });
    return normalizeApiVideo(response.data);
  },

  deleteVideo: async (videoId: string): Promise<void> => {
    await api.delete(`/videos/${videoId}`);
  },

  /**
   * PATCH /chapters/{source}/{target}/{video_id}
   * Body optionnel : `{ position }` / `{ after_video_id }`.
   * Réponse : formation complète.
   */
  moveVideoBetweenChapters: async (
    fromChapterId: string,
    toChapterId: string,
    videoId: string,
    options?: MoveVideoRequest
  ): Promise<Formation> => {
    const payload =
      options && (options.position !== undefined || options.after_video_id !== undefined)
        ? options
        : undefined;
    const response = await api.patch<Formation>(
      `/chapters/${fromChapterId}/${toChapterId}/${videoId}`,
      payload ?? null
    );
    return normalizeApiFormation(response.data);
  },

  /** PUT /chapters/{chapter_id}/videos/order — réordonnancement intra-chapitre (une requête). */
  putChapterVideoOrder: async (chapterId: string, videoIds: string[]): Promise<Chapter> => {
    const response = await api.put<Chapter>(`/chapters/${chapterId}/videos/order`, {
      video_ids: videoIds,
    });
    return normalizeApiChapter(response.data);
  },

  /** PUT /formations/{formation_id}/chapters/order — réordonnancement des chapitres. */
  putFormationChapterOrder: async (
    formationId: string,
    chapterIds: string[]
  ): Promise<Formation> => {
    const response = await api.put<Formation>(`/formations/${formationId}/chapters/order`, {
      chapter_ids: chapterIds,
    });
    return normalizeApiFormation(response.data);
  },

  getChapterDocuments: async (chapterId: string): Promise<Document[]> => {
    const response = await api.get<Document[]>(`/docs/chapters/${chapterId}`);
    return response.data.map(normalizeApiDocument);
  },

  createChapterDocument: async (
    chapterId: string,
    data: { title: string; file: File; videoId?: string | null },
    onProgress?: (progress: number) => void
  ): Promise<Document> => {
    const formData = new FormData();
    formData.append('title', data.title);
    formData.append('file', data.file);
    if (data.videoId) formData.append('video_id', data.videoId);

    const response = await api.post<Document>(`/chapters/${chapterId}/docs`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (event) => {
        if (event.total && onProgress) {
          onProgress(Math.round((event.loaded / event.total) * 100));
        }
      },
    });
    return normalizeApiDocument(response.data);
  },

  patchDocument: async (
    documentId: string,
    payload: { title?: string; video_id?: string | null }
  ): Promise<Document> => {
    const response = await api.patch<Document>(`/docs/${documentId}`, payload);
    return normalizeApiDocument(response.data);
  },

  deleteDocument: async (documentId: string): Promise<void> => {
    await api.delete(`/docs/${documentId}`);
  },

  /** URL directe : le cookie de session suffit (pas de header à ajouter). */
  documentFileUrl: (documentId: string, download = false): string =>
    `${API_BASE_URL}/docs/${documentId}/file${download ? '?download=true' : ''}`,
};

export default api;
