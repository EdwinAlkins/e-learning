'use client';

import { useCallback, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import type {
  Chapter,
  Document,
  Formation,
  PatchChapterPayload,
  PatchFormationPayload,
  PatchVideoPayload,
  Video,
} from '../../../types';
import {
  fetchFormationIntoCache,
  formationKeys,
  getCachedFormation,
  removeFormationFromCache,
  setFormationInCache,
  updateFormationInCache,
} from '../../catalog/queries/formation.queries';
import { sortChaptersByNumber, sortVideosByNumber } from '../../../utils/formation';
import {
  addChapterToFormation,
  addVideoToChapter,
  removeChapterFromFormation,
  removeVideoFromFormation,
  setChapterVideoOrder,
  setFormationChapterOrder,
  updateChapterInFormation,
  updateVideoInFormation,
} from '../../../utils/studio-mutations';
import { formationProgressKeys } from '../../formation/queries/progress.queries';
import { playerKeys } from '../../player/queries/player.queries';
import { studioApi } from '../api/studio.api';

const uploadKeyForCreate = (chapterId: string): string => `create:${chapterId}`;
const uploadKeyForPatch = (videoId: string): string => `patch:${videoId}`;

export const studioUploadKeys = {
  create: uploadKeyForCreate,
  patch: uploadKeyForPatch,
};

const mutateFormation = (
  formation: Formation,
  updater: (formations: Formation[]) => Formation[]
): Formation => updater([formation])[0];

export function useStudioMutations() {
  const queryClient = useQueryClient();
  // Le catalogue est mis à jour localement, mais les vues apprenant qui en dérivent doivent être relues.
  const invalidateLearnerViews = useCallback(() => {
    for (const queryKey of [
      formationProgressKeys.all,
      playerKeys.allDocuments,
      playerKeys.allSummaries,
    ]) {
      void queryClient.invalidateQueries({ queryKey });
    }
  }, [queryClient]);
  const [uploadProgressByKey, setUploadProgressByKey] = useState<Record<string, number>>({});

  const setUploadProgress = useCallback((key: string, progress?: number) => {
    setUploadProgressByKey((current) => {
      if (progress !== undefined) return { ...current, [key]: progress };
      const next = { ...current };
      delete next[key];
      return next;
    });
  }, []);

  const refreshFormation = useCallback(
    async (formationId: string) => {
      const formation = await fetchFormationIntoCache(queryClient, formationId);
      invalidateLearnerViews();
      return formation;
    },
    [queryClient, invalidateLearnerViews]
  );

  const createFormation = useCallback(
    async (name: string): Promise<Formation> => {
      const formation = await studioApi.createFormation(name);
      setFormationInCache(queryClient, formation);
      await queryClient.invalidateQueries({ queryKey: formationKeys.all });
      invalidateLearnerViews();
      return formation;
    },
    [queryClient, invalidateLearnerViews]
  );

  const patchFormation = useCallback(
    async (id: string, payload: PatchFormationPayload): Promise<Formation> => {
      const formation = await studioApi.patchFormation(id, payload);
      setFormationInCache(queryClient, formation);
      invalidateLearnerViews();
      return formation;
    },
    [queryClient, invalidateLearnerViews]
  );

  const deleteFormation = useCallback(
    async (id: string): Promise<void> => {
      await studioApi.deleteFormation(id);
      removeFormationFromCache(queryClient, id);
      invalidateLearnerViews();
    },
    [queryClient, invalidateLearnerViews]
  );

  const createChapter = useCallback(
    async (formationId: string, name: string): Promise<Chapter> => {
      const chapter = await studioApi.createChapter(formationId, name);
      updateFormationInCache(queryClient, formationId, (formation) =>
        mutateFormation(formation, (formations) =>
          addChapterToFormation(formations, formationId, chapter)
        )
      );
      invalidateLearnerViews();
      return chapter;
    },
    [queryClient, invalidateLearnerViews]
  );

  const patchChapter = useCallback(
    async (
      formationId: string,
      chapterId: string,
      payload: PatchChapterPayload
    ): Promise<Chapter> => {
      const chapter = await studioApi.patchChapter(chapterId, payload);
      updateFormationInCache(queryClient, formationId, (formation) =>
        mutateFormation(formation, (formations) =>
          updateChapterInFormation(formations, formationId, chapterId, chapter)
        )
      );
      invalidateLearnerViews();
      return chapter;
    },
    [queryClient, invalidateLearnerViews]
  );

  const deleteChapter = useCallback(
    async (formationId: string, chapterId: string): Promise<void> => {
      await studioApi.deleteChapter(chapterId);
      updateFormationInCache(queryClient, formationId, (formation) =>
        mutateFormation(formation, (formations) =>
          removeChapterFromFormation(formations, formationId, chapterId)
        )
      );
      invalidateLearnerViews();
    },
    [queryClient, invalidateLearnerViews]
  );

  const createVideo = useCallback(
    async (
      formationId: string,
      chapterId: string,
      data: { title: string; file: File }
    ): Promise<Video> => {
      const uploadKey = uploadKeyForCreate(chapterId);
      setUploadProgress(uploadKey, 0);
      try {
        const video = await studioApi.createVideo(chapterId, data, (progress) =>
          setUploadProgress(uploadKey, progress)
        );
        updateFormationInCache(queryClient, formationId, (formation) =>
          mutateFormation(formation, (formations) =>
            addVideoToChapter(formations, formationId, chapterId, video)
          )
        );
        invalidateLearnerViews();
        return video;
      } finally {
        setUploadProgress(uploadKey);
      }
    },
    [queryClient, setUploadProgress, invalidateLearnerViews]
  );

  const patchVideo = useCallback(
    async (
      formationId: string,
      chapterId: string,
      videoId: string,
      payload: PatchVideoPayload
    ): Promise<Video> => {
      const uploadKey = uploadKeyForPatch(videoId);
      if (payload.file) setUploadProgress(uploadKey, 0);
      try {
        const video = await studioApi.patchVideo(
          videoId,
          payload,
          payload.file ? (progress) => setUploadProgress(uploadKey, progress) : undefined
        );
        if (payload.file) {
          await fetchFormationIntoCache(queryClient, formationId);
        } else {
          updateFormationInCache(queryClient, formationId, (formation) =>
            mutateFormation(formation, (formations) =>
              updateVideoInFormation(formations, formationId, chapterId, videoId, video)
            )
          );
        }
        invalidateLearnerViews();
        return video;
      } finally {
        if (payload.file) setUploadProgress(uploadKey);
      }
    },
    [queryClient, setUploadProgress, invalidateLearnerViews]
  );

  const deleteVideo = useCallback(
    async (formationId: string, chapterId: string, videoId: string): Promise<void> => {
      await studioApi.deleteVideo(videoId);
      updateFormationInCache(queryClient, formationId, (formation) =>
        mutateFormation(formation, (formations) =>
          removeVideoFromFormation(formations, formationId, chapterId, videoId)
        )
      );
      invalidateLearnerViews();
    },
    [queryClient, invalidateLearnerViews]
  );

  const reorderVideos = useCallback(
    async (
      formationId: string,
      chapterId: string,
      orderedVideoIds: string[]
    ): Promise<Chapter> => {
      const previous = getCachedFormation(queryClient, formationId);
      const chapter = previous?.chapters.find((item) => item.id === chapterId);
      if (!previous || !chapter) throw new Error('Chapitre introuvable');

      updateFormationInCache(queryClient, formationId, (formation) =>
        mutateFormation(formation, (formations) =>
          setChapterVideoOrder(formations, formationId, chapterId, orderedVideoIds)
        )
      );

      try {
        const currentIds = sortVideosByNumber(chapter.videos).map((video) => video.id);
        const unchanged =
          currentIds.length === orderedVideoIds.length &&
          currentIds.every((id, index) => id === orderedVideoIds[index]);
        const updated = unchanged
          ? chapter
          : await studioApi.reorderVideos(chapterId, orderedVideoIds);
        updateFormationInCache(queryClient, formationId, (formation) =>
          mutateFormation(formation, (formations) =>
            updateChapterInFormation(formations, formationId, chapterId, updated)
          )
        );
        invalidateLearnerViews();
        return updated;
      } catch (error) {
        setFormationInCache(queryClient, previous);
        throw error;
      }
    },
    [queryClient, invalidateLearnerViews]
  );

  const reorderChapters = useCallback(
    async (formationId: string, orderedChapterIds: string[]): Promise<Formation> => {
      const previous = getCachedFormation(queryClient, formationId);
      if (!previous) throw new Error('Formation introuvable');

      updateFormationInCache(queryClient, formationId, (formation) =>
        mutateFormation(formation, (formations) =>
          setFormationChapterOrder(formations, formationId, orderedChapterIds)
        )
      );

      try {
        const currentIds = sortChaptersByNumber(previous.chapters).map((chapter) => chapter.id);
        const unchanged =
          currentIds.length === orderedChapterIds.length &&
          currentIds.every((id, index) => id === orderedChapterIds[index]);
        const updated = unchanged
          ? previous
          : await studioApi.reorderChapters(formationId, orderedChapterIds);
        setFormationInCache(queryClient, updated);
        invalidateLearnerViews();
        return updated;
      } catch (error) {
        setFormationInCache(queryClient, previous);
        throw error;
      }
    },
    [queryClient, invalidateLearnerViews]
  );

  const moveVideo = useCallback(
    async (
      formationId: string,
      fromChapterId: string,
      videoId: string,
      toChapterId: string,
      toIndex?: number
    ): Promise<Formation> => {
      const formation = await studioApi.moveVideo(
        fromChapterId,
        videoId,
        toChapterId,
        toIndex
      );
      setFormationInCache(queryClient, formation);
      invalidateLearnerViews();
      return formation;
    },
    [queryClient, invalidateLearnerViews]
  );

  const createDocument = useCallback(
    async (
      formationId: string,
      chapterId: string,
      data: { title: string; file: File; videoId?: string | null }
    ): Promise<Document> => {
      const document = await studioApi.createDocument(chapterId, data);
      await fetchFormationIntoCache(queryClient, formationId);
      invalidateLearnerViews();
      return document;
    },
    [queryClient, invalidateLearnerViews]
  );

  const patchDocument = useCallback(
    async (
      formationId: string,
      documentId: string,
      payload: { title?: string; video_id?: string | null }
    ): Promise<Document> => {
      const document = await studioApi.patchDocument(documentId, payload);
      await fetchFormationIntoCache(queryClient, formationId);
      invalidateLearnerViews();
      return document;
    },
    [queryClient, invalidateLearnerViews]
  );

  const deleteDocument = useCallback(
    async (formationId: string, documentId: string): Promise<void> => {
      await studioApi.deleteDocument(documentId);
      await fetchFormationIntoCache(queryClient, formationId);
      invalidateLearnerViews();
    },
    [queryClient, invalidateLearnerViews]
  );

  const runVideoJob = useCallback(
    async (
      formationId: string,
      videoId: string,
      operation: (id: string) => Promise<Video>
    ): Promise<Video> => {
      const video = await operation(videoId);
      await fetchFormationIntoCache(queryClient, formationId);
      invalidateLearnerViews();
      return video;
    },
    [queryClient, invalidateLearnerViews]
  );

  const startTranscription = useCallback(
    (formationId: string, videoId: string) =>
      runVideoJob(formationId, videoId, studioApi.startTranscription),
    [runVideoJob]
  );
  const startMediaConversion = useCallback(
    (formationId: string, videoId: string) =>
      runVideoJob(formationId, videoId, studioApi.startMediaConversion),
    [runVideoJob]
  );
  const generateVideoSummary = useCallback(
    (formationId: string, videoId: string) =>
      runVideoJob(formationId, videoId, studioApi.generateVideoSummary),
    [runVideoJob]
  );

  return {
    uploadProgressByKey,
    refreshFormation,
    createFormation,
    patchFormation,
    deleteFormation,
    createChapter,
    patchChapter,
    deleteChapter,
    createVideo,
    patchVideo,
    deleteVideo,
    reorderVideos,
    reorderChapters,
    moveVideo,
    createDocument,
    patchDocument,
    deleteDocument,
    startTranscription,
    startMediaConversion,
    generateVideoSummary,
  };
}

export type StudioMutations = ReturnType<typeof useStudioMutations>;
