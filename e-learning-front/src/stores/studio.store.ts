import { create } from 'zustand';
import type {
  Chapter,
  Document,
  Formation,
  PatchChapterPayload,
  PatchFormationPayload,
  PatchVideoPayload,
  Video,
} from '../types';
import { studioApi } from '../services/studio.api';
import { useCatalogStore } from './catalog.store';
import { sortChaptersByNumber, sortVideosByNumber } from '../utils/formation';
import {
  addChapterToFormation,
  addVideoToChapter,
  removeChapterFromFormation,
  removeFormationFromList,
  removeVideoFromFormation,
  replaceFormationInList,
  setChapterVideoOrder,
  setFormationChapterOrder,
  updateChapterInFormation,
  updateVideoInFormation,
  upsertFormationInList,
} from '../utils/studio-mutations';

const syncCatalogFormation = (formation: Formation): void => {
  useCatalogStore.getState().upsertFormation(formation);
};

const syncCatalogRemoveFormation = (formationId: string): void => {
  useCatalogStore.getState().removeFormation(formationId);
};

const refreshCatalog = (): void => {
  void useCatalogStore.getState().fetchFormations(true);
};

const setUploadProgressForKey = (
  uploadProgressByKey: Record<string, number>,
  key: string,
  progress: number
): Record<string, number> => ({
  ...uploadProgressByKey,
  [key]: progress,
});

const clearUploadProgressKey = (
  uploadProgressByKey: Record<string, number>,
  key: string
): Record<string, number> => {
  const next = { ...uploadProgressByKey };
  delete next[key];
  return next;
};

const uploadKeyForCreate = (chapterId: string): string => `create:${chapterId}`;
const uploadKeyForPatch = (videoId: string): string => `patch:${videoId}`;

interface StudioState {
  formations: Formation[];
  loading: boolean;
  error: string | null;
  uploadProgressByKey: Record<string, number>;
  /** @param silent ne bascule pas `loading` (poll jobs sans flash UI). */
  fetchFormations: (silent?: boolean) => Promise<void>;
  /** Rafraîchit une formation sans spinner (statuts conversion / IA). */
  refreshFormation: (formationId: string) => Promise<Formation>;
  getUploadProgress: (key: string) => number | undefined;
  createFormation: (name: string) => Promise<Formation>;
  patchFormation: (id: string, payload: PatchFormationPayload) => Promise<Formation>;
  deleteFormation: (id: string) => Promise<void>;
  createChapter: (formationId: string, name: string) => Promise<Chapter>;
  patchChapter: (
    formationId: string,
    chapterId: string,
    payload: PatchChapterPayload
  ) => Promise<Chapter>;
  deleteChapter: (formationId: string, chapterId: string) => Promise<void>;
  createVideo: (
    formationId: string,
    chapterId: string,
    data: { title: string; file: File }
  ) => Promise<Video>;
  patchVideo: (
    formationId: string,
    chapterId: string,
    videoId: string,
    payload: PatchVideoPayload
  ) => Promise<Video>;
  deleteVideo: (formationId: string, chapterId: string, videoId: string) => Promise<void>;
  reorderVideos: (
    formationId: string,
    chapterId: string,
    orderedVideoIds: string[]
  ) => Promise<Chapter>;
  reorderChapters: (formationId: string, orderedChapterIds: string[]) => Promise<Formation>;
  moveVideo: (
    formationId: string,
    fromChapterId: string,
    videoId: string,
    toChapterId: string,
    toIndex?: number
  ) => Promise<Formation>;
  createDocument: (
    formationId: string,
    chapterId: string,
    data: { title: string; file: File; videoId?: string | null }
  ) => Promise<Document>;
  patchDocument: (
    formationId: string,
    documentId: string,
    payload: { title?: string; video_id?: string | null }
  ) => Promise<Document>;
  deleteDocument: (formationId: string, documentId: string) => Promise<void>;
  startTranscription: (formationId: string, videoId: string) => Promise<Video>;
  startMediaConversion: (formationId: string, videoId: string) => Promise<Video>;
  generateVideoSummary: (formationId: string, videoId: string) => Promise<Video>;
}

const applyFormationRefresh = (
  set: (partial: Partial<StudioState>) => void,
  get: () => StudioState,
  formationId: string,
  refreshed: Formation
): Formation => {
  set({ formations: replaceFormationInList(get().formations, formationId, refreshed) });
  syncCatalogFormation(refreshed);
  return refreshed;
};

export const useStudioStore = create<StudioState>((set, get) => ({
  formations: [],
  loading: false,
  error: null,
  uploadProgressByKey: {},

  getUploadProgress: (key) => get().uploadProgressByKey[key],

  fetchFormations: async (silent = false) => {
    if (!silent) {
      set({ loading: true, error: null });
    }
    try {
      const formations = await studioApi.getFormations();
      set({ formations, loading: false, error: null });
    } catch (error) {
      if (silent) {
        set({ loading: false });
        return;
      }
      set({
        loading: false,
        error: error instanceof Error ? error.message : 'Échec du chargement studio',
      });
    }
  },

  refreshFormation: async (formationId) => {
    const refreshed = await studioApi.fetchFormationById(formationId);
    return applyFormationRefresh(set, get, formationId, refreshed);
  },

  createFormation: async (name) => {
    const formation = await studioApi.createFormation(name);
    set({ formations: upsertFormationInList(get().formations, formation) });
    refreshCatalog();
    return formation;
  },

  patchFormation: async (id, payload) => {
    const previous = get().formations;
    const formation = await studioApi.patchFormation(id, payload);
    set({ formations: upsertFormationInList(previous, formation) });
    syncCatalogFormation(formation);
    return formation;
  },

  deleteFormation: async (id) => {
    await studioApi.deleteFormation(id);
    set({ formations: removeFormationFromList(get().formations, id) });
    syncCatalogRemoveFormation(id);
  },

  createChapter: async (formationId, name) => {
    const chapter = await studioApi.createChapter(formationId, name);
    set({
      formations: addChapterToFormation(get().formations, formationId, chapter),
    });
    const formation = get().formations.find((item) => item.id === formationId);
    if (formation) syncCatalogFormation(formation);
    return chapter;
  },

  patchChapter: async (formationId, chapterId, payload) => {
    const chapter = await studioApi.patchChapter(formationId, chapterId, payload);
    set({
      formations: updateChapterInFormation(get().formations, formationId, chapterId, chapter),
    });
    const formation = get().formations.find((item) => item.id === formationId);
    if (formation) syncCatalogFormation(formation);
    return chapter;
  },

  deleteChapter: async (formationId, chapterId) => {
    await studioApi.deleteChapter(formationId, chapterId);
    set({
      formations: removeChapterFromFormation(get().formations, formationId, chapterId),
    });
    const formation = get().formations.find((item) => item.id === formationId);
    if (formation) syncCatalogFormation(formation);
  },

  createVideo: async (formationId, chapterId, data) => {
    const uploadKey = uploadKeyForCreate(chapterId);
    set({
      uploadProgressByKey: setUploadProgressForKey(get().uploadProgressByKey, uploadKey, 0),
    });
    try {
      const video = await studioApi.createVideo(formationId, chapterId, data, (progress) => {
        set({
          uploadProgressByKey: setUploadProgressForKey(
            get().uploadProgressByKey,
            uploadKey,
            progress
          ),
        });
      });
      set({
        formations: addVideoToChapter(get().formations, formationId, chapterId, video),
        uploadProgressByKey: clearUploadProgressKey(get().uploadProgressByKey, uploadKey),
      });
      const formation = get().formations.find((item) => item.id === formationId);
      if (formation) syncCatalogFormation(formation);
      return video;
    } catch (error) {
      set({
        uploadProgressByKey: clearUploadProgressKey(get().uploadProgressByKey, uploadKey),
      });
      throw error;
    }
  },

  patchVideo: async (formationId, chapterId, videoId, payload) => {
    const uploadKey = uploadKeyForPatch(videoId);
    if (payload.file) {
      set({
        uploadProgressByKey: setUploadProgressForKey(get().uploadProgressByKey, uploadKey, 0),
      });
    }
    try {
      const video = await studioApi.patchVideo(
        formationId,
        chapterId,
        videoId,
        payload,
        payload.file
          ? (progress) => {
              set({
                uploadProgressByKey: setUploadProgressForKey(
                  get().uploadProgressByKey,
                  uploadKey,
                  progress
                ),
              });
            }
          : undefined
      );
      if (payload.file) {
        const refreshed = await studioApi.fetchFormationById(formationId);
        applyFormationRefresh(set, get, formationId, refreshed);
      } else {
        set({
          formations: updateVideoInFormation(
            get().formations,
            formationId,
            chapterId,
            videoId,
            video
          ),
        });
        const formation = get().formations.find((item) => item.id === formationId);
        if (formation) syncCatalogFormation(formation);
      }
      if (payload.file) {
        set({
          uploadProgressByKey: clearUploadProgressKey(get().uploadProgressByKey, uploadKey),
        });
      }
      return video;
    } catch (error) {
      if (payload.file) {
        set({
          uploadProgressByKey: clearUploadProgressKey(get().uploadProgressByKey, uploadKey),
        });
      }
      throw error;
    }
  },

  deleteVideo: async (formationId, chapterId, videoId) => {
    await studioApi.deleteVideo(formationId, chapterId, videoId);
    set({
      formations: removeVideoFromFormation(get().formations, formationId, chapterId, videoId),
    });
    const formation = get().formations.find((item) => item.id === formationId);
    if (formation) syncCatalogFormation(formation);
  },

  reorderVideos: async (formationId, chapterId, orderedVideoIds) => {
    const previous = get().formations;
    const previousCatalog = useCatalogStore.getState().formations;
    const chapter = previous
      .find((formation) => formation.id === formationId)
      ?.chapters.find((item) => item.id === chapterId);
    if (!chapter) {
      throw new Error('Chapitre introuvable');
    }

    const currentVideoIds = sortVideosByNumber(chapter.videos).map((video) => video.id);

    set({
      formations: setChapterVideoOrder(previous, formationId, chapterId, orderedVideoIds),
    });

    try {
      const isUnchanged = currentVideoIds.every((id, index) => id === orderedVideoIds[index]);
      const updatedChapter = isUnchanged
        ? chapter
        : await studioApi.reorderVideos(chapterId, orderedVideoIds);

      set({
        formations: updateChapterInFormation(
          get().formations,
          formationId,
          chapterId,
          updatedChapter
        ),
      });
      const formation = get().formations.find((item) => item.id === formationId);
      if (formation) syncCatalogFormation(formation);
      return updatedChapter;
    } catch (error) {
      set({ formations: previous });
      useCatalogStore.setState({ formations: previousCatalog });
      throw error;
    }
  },

  reorderChapters: async (formationId, orderedChapterIds) => {
    const previous = get().formations;
    const previousCatalog = useCatalogStore.getState().formations;
    const formation = previous.find((item) => item.id === formationId);
    if (!formation) {
      throw new Error('Formation introuvable');
    }

    const currentChapterIds = sortChaptersByNumber(formation.chapters).map(
      (chapter) => chapter.id
    );

    set({
      formations: setFormationChapterOrder(previous, formationId, orderedChapterIds),
    });

    try {
      const isUnchanged = currentChapterIds.every(
        (id, index) => id === orderedChapterIds[index]
      );
      const updated = isUnchanged
        ? formation
        : await studioApi.reorderChapters(formationId, orderedChapterIds);

      applyFormationRefresh(set, get, formationId, updated);
      return updated;
    } catch (error) {
      set({ formations: previous });
      useCatalogStore.setState({ formations: previousCatalog });
      throw error;
    }
  },

  moveVideo: async (formationId, fromChapterId, videoId, toChapterId, toIndex) => {
    const previous = get().formations;
    const previousCatalog = useCatalogStore.getState().formations;
    try {
      const refreshed = await studioApi.moveVideo(
        fromChapterId,
        videoId,
        toChapterId,
        toIndex
      );
      return applyFormationRefresh(set, get, formationId, refreshed);
    } catch (error) {
      set({ formations: previous });
      useCatalogStore.setState({ formations: previousCatalog });
      throw error;
    }
  },

  createDocument: async (formationId, chapterId, data) => {
    const document = await studioApi.createDocument(chapterId, data);
    const refreshed = await studioApi.fetchFormationById(formationId);
    applyFormationRefresh(set, get, formationId, refreshed);
    return document;
  },

  patchDocument: async (formationId, documentId, payload) => {
    const document = await studioApi.patchDocument(documentId, payload);
    const refreshed = await studioApi.fetchFormationById(formationId);
    applyFormationRefresh(set, get, formationId, refreshed);
    return document;
  },

  deleteDocument: async (formationId, documentId) => {
    await studioApi.deleteDocument(documentId);
    const refreshed = await studioApi.fetchFormationById(formationId);
    applyFormationRefresh(set, get, formationId, refreshed);
  },

  startTranscription: async (formationId, videoId) => {
    const video = await studioApi.startTranscription(videoId);
    const refreshed = await studioApi.fetchFormationById(formationId);
    applyFormationRefresh(set, get, formationId, refreshed);
    return video;
  },

  startMediaConversion: async (formationId, videoId) => {
    const video = await studioApi.startMediaConversion(videoId);
    const refreshed = await studioApi.fetchFormationById(formationId);
    applyFormationRefresh(set, get, formationId, refreshed);
    return video;
  },

  generateVideoSummary: async (formationId, videoId) => {
    const video = await studioApi.generateVideoSummary(videoId);
    const refreshed = await studioApi.fetchFormationById(formationId);
    applyFormationRefresh(set, get, formationId, refreshed);
    return video;
  },
}));

export const studioUploadKeys = {
  create: uploadKeyForCreate,
  patch: uploadKeyForPatch,
};
