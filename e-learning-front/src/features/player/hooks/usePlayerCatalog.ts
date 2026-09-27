'use client';

import { useEffect, useMemo } from 'react';
import type { Formation, Video } from '../../../types';
import { POLLING_INTERVAL_MS } from '../../../constants';
import { flattenFormationVideos } from '../../../utils/formation';
import { setVisibilityInterval } from '../../../utils/visibility-interval';
import { useFormationsQuery } from '../../catalog/queries/formation.queries';

export interface PlayerCatalogMatch {
  video: Video;
  formation: Formation;
  chapterId: string;
}

export function findVideoInCatalog(
  formations: Formation[],
  videoId: string
): PlayerCatalogMatch | null {
  for (const formation of formations) {
    for (const chapter of formation.chapters) {
      const video = chapter.videos.find((candidate) => candidate.id === videoId);
      if (video) return { video, formation, chapterId: chapter.id };
    }
  }
  return null;
}

export function usePlayerCatalog(videoId: string) {
  const formationsQuery = useFormationsQuery();
  const formations = useMemo(
    () => formationsQuery.data ?? [],
    [formationsQuery.data]
  );
  const match = useMemo(
    () => (videoId ? findVideoInCatalog(formations, videoId) : null),
    [formations, videoId]
  );
  const video = match?.video ?? null;
  const formation = match?.formation ?? null;
  const chapterId = match?.chapterId ?? null;

  const navigation = useMemo(() => {
    if (!formation || !videoId) return { prevVideo: null, nextVideo: null };
    const videos = flattenFormationVideos(formation.chapters);
    const index = videos.findIndex((candidate) => candidate.id === videoId);
    if (index === -1) return { prevVideo: null, nextVideo: null };
    return {
      prevVideo: index > 0 ? videos[index - 1] : null,
      nextVideo: index < videos.length - 1 ? videos[index + 1] : null,
    };
  }, [formation, videoId]);

  const processing =
    video?.transcription_status === 'processing' || video?.summary_status === 'processing';
  const refetch = formationsQuery.refetch;

  useEffect(() => {
    if (!video?.id || !processing) return;
    return setVisibilityInterval(() => {
      void refetch();
    }, POLLING_INTERVAL_MS);
  }, [processing, refetch, video?.id]);

  const missingIdError = videoId ? null : 'Identifiant vidéo manquant';
  const queryError =
    formationsQuery.error instanceof Error ? formationsQuery.error.message : null;
  const notFoundError =
    !formationsQuery.isLoading && videoId && !video ? 'Vidéo introuvable' : null;

  return {
    video,
    parentFormation: formation,
    chapterId,
    catalogDocuments: formation?.chapters.find((chapter) => chapter.id === chapterId)
      ?.documents,
    ...navigation,
    loading: Boolean(videoId) && formationsQuery.isLoading,
    error: missingIdError ?? queryError ?? notFoundError,
  };
}
