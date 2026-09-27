'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type { Note } from '../../../types';
import { playerApi } from '../api/player.api';

export const playerKeys = {
  summary: (videoId: string) => ['video-summary', videoId] as const,
  documents: (chapterId: string) => ['chapter-documents', chapterId] as const,
  progress: (videoId: string) => ['video-progress', videoId] as const,
  notes: (videoId: string) => ['video-notes', videoId] as const,
};

export function useVideoSummaryQuery(videoId: string, enabled: boolean) {
  return useQuery({
    queryKey: playerKeys.summary(videoId),
    queryFn: () => playerApi.getVideoSummary(videoId),
    enabled: Boolean(videoId) && enabled,
    retry: false,
  });
}

export function useUpdateVideoSummaryMutation(videoId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (summary: string) => playerApi.updateVideoSummary(videoId, summary),
    onSuccess: (summary) => {
      queryClient.setQueryData(playerKeys.summary(videoId), summary);
    },
  });
}

export function useChapterDocumentsQuery(chapterId: string, enabled: boolean) {
  return useQuery({
    queryKey: playerKeys.documents(chapterId),
    queryFn: () => playerApi.getChapterDocuments(chapterId),
    enabled: Boolean(chapterId) && enabled,
  });
}

export function useVideoProgressQuery(videoId: string) {
  return useQuery({
    queryKey: playerKeys.progress(videoId),
    queryFn: () => playerApi.getProgress(videoId),
    enabled: Boolean(videoId),
    staleTime: 0,
    refetchOnMount: 'always',
  });
}

export function useVideoNotesQuery(videoId: string) {
  return useQuery({
    queryKey: playerKeys.notes(videoId),
    queryFn: () => playerApi.getNotes(videoId),
    enabled: Boolean(videoId),
    select: (notes) => [...notes].sort((a, b) => a.timecode - b.timecode),
  });
}

export function useNoteMutations(videoId: string) {
  const queryClient = useQueryClient();

  const createNote = useMutation({
    mutationFn: ({ timecode, content }: { timecode: number; content: string }) =>
      playerApi.createNote(videoId, timecode, content),
    onSuccess: (created) => {
      queryClient.setQueryData<Note[]>(playerKeys.notes(videoId), (current) =>
        [...(current ?? []), created].sort((a, b) => a.timecode - b.timecode)
      );
    },
  });

  const updateNote = useMutation({
    mutationFn: ({ noteId, content }: { noteId: string; content: string }) =>
      playerApi.updateNote(noteId, content),
    onSuccess: (updated) => {
      queryClient.setQueryData<Note[]>(playerKeys.notes(videoId), (current) =>
        current?.map((note) => (note.id === updated.id ? updated : note)) ?? [updated]
      );
    },
  });

  const deleteNote = useMutation({
    mutationFn: async (noteId: string) => {
      await playerApi.deleteNote(noteId);
      return noteId;
    },
    onSuccess: (deletedId) => {
      queryClient.setQueryData<Note[]>(playerKeys.notes(videoId), (current) =>
        current?.filter((note) => note.id !== deletedId) ?? []
      );
    },
  });

  return { createNote, updateNote, deleteNote };
}
