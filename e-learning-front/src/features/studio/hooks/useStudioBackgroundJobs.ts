'use client';

import { useEffect, useState } from 'react';
import type { Formation, Video } from '../../../types';
import { POLLING_INTERVAL_MS } from '../../../constants';
import { setVisibilityInterval } from '../../../utils/visibility-interval';

interface UseStudioBackgroundJobsOptions {
  formation: Formation | null;
  refreshFormation: (formationId: string) => Promise<Formation>;
  startTranscription: (formationId: string, videoId: string) => Promise<Video>;
  startMediaConversion: (formationId: string, videoId: string) => Promise<Video>;
  generateVideoSummary: (formationId: string, videoId: string) => Promise<Video>;
}

export function useStudioBackgroundJobs({
  formation,
  refreshFormation,
  startTranscription,
  startMediaConversion,
  generateVideoSummary,
}: UseStudioBackgroundJobsOptions) {
  const [notice, setNotice] = useState<string | null>(null);
  const [busyVideoId, setBusyVideoId] = useState<string | null>(null);
  const formationId = formation?.id ?? '';
  const processingJobKey = formation
    ? formation.chapters
        .flatMap((chapter) => chapter.videos)
        .filter(
          (video) =>
            video.processing_status === 'processing' ||
            video.transcription_status === 'processing' ||
            video.summary_status === 'processing'
        )
        .map((video) => video.id)
        .sort()
        .join(',')
    : '';

  useEffect(() => {
    if (!formationId || !processingJobKey) return;

    const watchedIds = new Set(processingJobKey.split(','));
    let cancelled = false;

    const poll = async () => {
      try {
        const refreshed = await refreshFormation(formationId);
        if (cancelled) return;
        for (const chapter of refreshed.chapters) {
          for (const video of chapter.videos) {
            if (!watchedIds.has(video.id)) continue;
            if (video.processing_status === 'failed') {
              setNotice(`Échec de conversion : « ${video.title} »`);
            } else if (video.transcription_status === 'failed') {
              setNotice(`Échec de transcription : « ${video.title} »`);
            } else if (video.summary_status === 'failed') {
              setNotice(
                `Échec de génération du résumé : « ${video.title} » (vérifiez la connexion API LLM)`
              );
            }
          }
        }
      } catch {
        // Le polling ne doit pas interrompre l'édition.
      }
    };

    const stop = setVisibilityInterval(() => {
      void poll();
    }, POLLING_INTERVAL_MS);

    return () => {
      cancelled = true;
      stop();
    };
  }, [formationId, processingJobKey, refreshFormation]);

  const runJob = async (
    video: Video,
    operation: (formationId: string, videoId: string) => Promise<Video>,
    fallbackMessage: string
  ) => {
    if (!formation) return;
    setBusyVideoId(video.id);
    setNotice(null);
    try {
      await operation(formation.id, video.id);
    } catch (error) {
      setNotice(error instanceof Error ? error.message : fallbackMessage);
    } finally {
      setBusyVideoId(null);
    }
  };

  return {
    notice,
    clearNotice: () => setNotice(null),
    busyVideoId,
    startTranscription: (video: Video) =>
      runJob(video, startTranscription, 'Échec du lancement de la transcription'),
    startMediaConversion: (video: Video) =>
      runJob(video, startMediaConversion, 'Échec du lancement de la conversion'),
    generateSummary: (video: Video) =>
      runJob(video, generateVideoSummary, 'Échec du lancement du résumé'),
  };
}
