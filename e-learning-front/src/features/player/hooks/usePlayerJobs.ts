'use client';

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { updateVideoInFormationCache } from '../../catalog/queries/formation.queries';
import { playerApi } from '../api/player.api';

interface PlayerJobContext {
  formationId: string | null;
  chapterId: string | null;
  videoId: string;
}

export function usePlayerJobs({ formationId, chapterId, videoId }: PlayerJobContext) {
  const queryClient = useQueryClient();
  const updateCatalogVideo = (video: Awaited<ReturnType<typeof playerApi.startTranscription>>) => {
    if (!formationId || !chapterId) return;
    updateVideoInFormationCache(queryClient, formationId, chapterId, videoId, video);
  };

  const transcription = useMutation({
    mutationFn: () => playerApi.startTranscription(videoId),
    onSuccess: updateCatalogVideo,
  });
  const summary = useMutation({
    mutationFn: () => playerApi.generateVideoSummary(videoId),
    onSuccess: updateCatalogVideo,
  });

  const startTranscription = async () => {
    transcription.reset();
    summary.reset();
    return transcription.mutateAsync();
  };

  const generateSummary = async () => {
    transcription.reset();
    summary.reset();
    return summary.mutateAsync();
  };

  const mutationError = transcription.error ?? summary.error;
  const error = mutationError instanceof Error ? mutationError.message : null;

  return {
    startTranscription,
    generateSummary,
    busy: transcription.isPending || summary.isPending,
    error,
  };
}
