'use client';

import { useState } from 'react';
import type { Chapter, Formation, Video } from '../../../types';
import type { DraggedVideo, MoveDialogState } from '../builder.types';
import { sortChaptersByNumber, sortVideosByNumber } from '../../../utils/formation';

interface UseVideoReorderOptions {
  formation: Formation | null;
  reorderVideos: (
    formationId: string,
    chapterId: string,
    orderedVideoIds: string[]
  ) => Promise<Chapter>;
  reorderChapters: (
    formationId: string,
    orderedChapterIds: string[]
  ) => Promise<Formation>;
  moveVideo: (
    formationId: string,
    fromChapterId: string,
    videoId: string,
    toChapterId: string,
    toIndex?: number
  ) => Promise<Formation>;
}

export function useVideoReorder({
  formation,
  reorderVideos,
  reorderChapters,
  moveVideo,
}: UseVideoReorderOptions) {
  const [busyVideoId, setBusyVideoId] = useState<string | null>(null);
  const [busyChapterId, setBusyChapterId] = useState<string | null>(null);
  const [draggedVideo, setDraggedVideo] = useState<DraggedVideo | null>(null);

  const reorderInChapter = async (
    chapter: Chapter,
    orderedIds: string[],
    movedVideoId: string
  ) => {
    if (!formation) return;
    setBusyVideoId(movedVideoId);
    try {
      await reorderVideos(formation.id, chapter.id, orderedIds);
    } finally {
      setBusyVideoId(null);
    }
  };

  const moveUp = async (chapter: Chapter, video: Video) => {
    const sorted = sortVideosByNumber(chapter.videos);
    const index = sorted.findIndex((item) => item.id === video.id);
    if (index <= 0) return;
    const orderedIds = sorted.map((item) => item.id);
    [orderedIds[index - 1], orderedIds[index]] = [orderedIds[index], orderedIds[index - 1]];
    await reorderInChapter(chapter, orderedIds, video.id);
  };

  const moveDown = async (chapter: Chapter, video: Video) => {
    const sorted = sortVideosByNumber(chapter.videos);
    const index = sorted.findIndex((item) => item.id === video.id);
    if (index === -1 || index >= sorted.length - 1) return;
    const orderedIds = sorted.map((item) => item.id);
    [orderedIds[index], orderedIds[index + 1]] = [orderedIds[index + 1], orderedIds[index]];
    await reorderInChapter(chapter, orderedIds, video.id);
  };

  const moveChapter = async (chapter: Chapter, direction: -1 | 1) => {
    if (!formation) return;
    const sorted = sortChaptersByNumber(formation.chapters);
    const index = sorted.findIndex((item) => item.id === chapter.id);
    const targetIndex = index + direction;
    if (index === -1 || targetIndex < 0 || targetIndex >= sorted.length) return;
    const orderedIds = sorted.map((item) => item.id);
    [orderedIds[index], orderedIds[targetIndex]] = [orderedIds[targetIndex], orderedIds[index]];
    setBusyChapterId(chapter.id);
    try {
      await reorderChapters(formation.id, orderedIds);
    } finally {
      setBusyChapterId(null);
    }
  };

  const dropOnVideo = async (
    targetChapter: Chapter,
    targetVideo: Video,
    insertAfter: boolean
  ) => {
    if (!formation || !draggedVideo) return;
    const targetSorted = sortVideosByNumber(targetChapter.videos);
    let targetIndex = targetSorted.findIndex((item) => item.id === targetVideo.id);
    if (targetIndex === -1) return;
    if (insertAfter) targetIndex += 1;

    if (draggedVideo.chapterId === targetChapter.id) {
      const orderedIds = targetSorted.map((item) => item.id);
      const fromIndex = orderedIds.indexOf(draggedVideo.videoId);
      if (fromIndex === -1) return;
      orderedIds.splice(fromIndex, 1);
      const adjustedIndex = fromIndex < targetIndex ? targetIndex - 1 : targetIndex;
      orderedIds.splice(adjustedIndex, 0, draggedVideo.videoId);
      await reorderInChapter(targetChapter, orderedIds, draggedVideo.videoId);
    } else {
      setBusyVideoId(draggedVideo.videoId);
      try {
        await moveVideo(
          formation.id,
          draggedVideo.chapterId,
          draggedVideo.videoId,
          targetChapter.id,
          targetIndex
        );
      } finally {
        setBusyVideoId(null);
      }
    }
    setDraggedVideo(null);
  };

  const submitMove = async (
    moveDialog: MoveDialogState,
    toChapterId: string,
    toIndex?: number
  ) => {
    if (!formation || !moveDialog) return;
    setBusyVideoId(moveDialog.video.id);
    try {
      await moveVideo(
        formation.id,
        moveDialog.chapter.id,
        moveDialog.video.id,
        toChapterId,
        toIndex
      );
    } finally {
      setBusyVideoId(null);
    }
  };

  return {
    busyVideoId,
    busyChapterId,
    draggedVideo,
    setDraggedVideo,
    moveUp,
    moveDown,
    moveChapterUp: (chapter: Chapter) => moveChapter(chapter, -1),
    moveChapterDown: (chapter: Chapter) => moveChapter(chapter, 1),
    dropOnVideo,
    submitMove,
  };
}
