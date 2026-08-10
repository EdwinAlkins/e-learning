'use client';

import { useEffect, useRef, useState } from 'react';
import { studioUploadKeys, useStudioStore } from '../../../stores/studio.store';
import type { Chapter, Formation, Video } from '../../../types';
import { sortChaptersByNumber, sortVideosByNumber } from '../../../utils/formation';
import { POLLING_INTERVAL_MS } from '../../../constants';
import { setVisibilityInterval } from '../../../utils/visibility-interval';
import type {
  ChapterDialogState,
  DeleteTarget,
  DocumentDialogState,
  DraggedVideo,
  MoveDialogState,
  VideoDialogState,
} from './types';
import type { ChapterSubmitData } from '../ChapterDialog';

function moveIdToOrder(ids: string[], id: string, order1Based: number): string[] {
  const without = ids.filter((item) => item !== id);
  const targetIndex = Math.max(0, Math.min(order1Based - 1, without.length));
  without.splice(targetIndex, 0, id);
  return without;
}

export function useFormationBuilder(formationId: string) {
  const {
    formations,
    loading,
    error,
    fetchFormations,
    refreshFormation,
    patchFormation,
    createChapter,
    patchChapter,
    deleteChapter,
    createVideo,
    patchVideo,
    deleteVideo,
    createDocument,
    patchDocument,
    deleteDocument,
    startTranscription,
    startMediaConversion,
    generateVideoSummary,
    reorderVideos,
    reorderChapters,
    moveVideo,
    getUploadProgress,
  } = useStudioStore();

  const [formation, setFormation] = useState<Formation | null>(null);
  const [formationName, setFormationName] = useState('');
  const [savingName, setSavingName] = useState(false);
  const [nameError, setNameError] = useState<string | null>(null);
  const [jobNotice, setJobNotice] = useState<string | null>(null);
  const [busyVideoId, setBusyVideoId] = useState<string | null>(null);
  const [busyChapterId, setBusyChapterId] = useState<string | null>(null);
  const [draggedVideo, setDraggedVideo] = useState<DraggedVideo | null>(null);
  const [chapterDialog, setChapterDialog] = useState<ChapterDialogState>({
    open: false,
    mode: 'create',
  });
  const [videoDialog, setVideoDialog] = useState<VideoDialogState>(null);
  const [documentDialog, setDocumentDialog] = useState<DocumentDialogState>(null);
  const [moveDialog, setMoveDialog] = useState<MoveDialogState>(null);
  const [deleteTarget, setDeleteTarget] = useState<DeleteTarget | null>(null);
  const [deleting, setDeleting] = useState(false);
  const nameDirtyRef = useRef(false);
  const nameInitializedRef = useRef(false);

  useEffect(() => {
    void fetchFormations();
  }, [fetchFormations]);

  useEffect(() => {
    nameDirtyRef.current = false;
    nameInitializedRef.current = false;
    setFormationName('');
  }, [formationId]);

  useEffect(() => {
    const found = formations.find((item) => item.id === formationId) ?? null;
    setFormation(found);
    if (!found || savingName) return;

    if (!nameInitializedRef.current) {
      setFormationName(found.name);
      nameInitializedRef.current = true;
      return;
    }

    if (!nameDirtyRef.current) {
      setFormationName(found.name);
    }
  }, [formations, formationId, savingName]);

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
              setJobNotice(`Échec de conversion : « ${video.title} »`);
            } else if (video.transcription_status === 'failed') {
              setJobNotice(`Échec de transcription : « ${video.title} »`);
            } else if (video.summary_status === 'failed') {
              setJobNotice(
                `Échec de génération du résumé : « ${video.title} » (vérifiez la connexion API LLM)`
              );
            }
          }
        }
      } catch {
        // poll silencieux : ne pas casser l'UI
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

  const handleFormationNameChange = (value: string) => {
    nameDirtyRef.current = true;
    setFormationName(value);
  };

  const handleSaveFormationName = async () => {
    if (!formation) return;
    if (formationName.trim() === formation.name) return;

    setSavingName(true);
    setNameError(null);
    try {
      await patchFormation(formation.id, { name: formationName.trim() });
      nameDirtyRef.current = false;
    } catch (err) {
      setNameError(err instanceof Error ? err.message : 'Erreur lors de la sauvegarde');
    } finally {
      setSavingName(false);
    }
  };

  const handleChapterSubmit = async (data: ChapterSubmitData) => {
    if (!formation) return;

    if (chapterDialog.mode === 'create') {
      await createChapter(formation.id, data.name);
      return;
    }

    if (!chapterDialog.chapter) return;

    const chapter = chapterDialog.chapter;
    if (data.name !== chapter.name) {
      await patchChapter(formation.id, chapter.id, { name: data.name });
    }

    if (data.order != null) {
      const sorted = sortChaptersByNumber(formation.chapters);
      const currentOrder = sorted.findIndex((item) => item.id === chapter.id) + 1;
      if (data.order !== currentOrder) {
        const orderedIds = moveIdToOrder(
          sorted.map((item) => item.id),
          chapter.id,
          data.order
        );
        await reorderChapters(formation.id, orderedIds);
      }
    }
  };

  const handleVideoSubmit = async (data: { title: string; file?: File }) => {
    if (!formation || !videoDialog) return;

    if (videoDialog.mode === 'create') {
      if (!data.file) throw new Error('Fichier requis');
      await createVideo(formation.id, videoDialog.chapter.id, {
        title: data.title,
        file: data.file,
      });
    } else if (videoDialog.video) {
      await patchVideo(formation.id, videoDialog.chapter.id, videoDialog.video.id, {
        title: data.title,
        file: data.file,
      });
    }
  };

  const handleDocumentSubmit = async (data: {
    title: string;
    file: File;
    videoId?: string | null;
  }) => {
    if (!formation || !documentDialog || documentDialog.mode !== 'create') return;
    await createDocument(formation.id, documentDialog.chapter.id, data);
  };

  const handleDocumentEditSubmit = async (data: {
    title: string;
    videoId: string | null;
  }) => {
    if (!formation || !documentDialog || documentDialog.mode !== 'edit' || !documentDialog.document) {
      return;
    }
    await patchDocument(formation.id, documentDialog.document.id, {
      title: data.title,
      video_id: data.videoId,
    });
  };

  const handleDelete = async () => {
    if (!formation || !deleteTarget) return;
    setDeleting(true);
    try {
      if (deleteTarget.type === 'chapter') {
        await deleteChapter(formation.id, deleteTarget.chapter.id);
      } else if (deleteTarget.type === 'video') {
        await deleteVideo(formation.id, deleteTarget.chapter.id, deleteTarget.video.id);
      } else {
        await deleteDocument(formation.id, deleteTarget.document.id);
      }
      setDeleteTarget(null);
    } catch (err) {
      console.error(err);
    } finally {
      setDeleting(false);
    }
  };

  const reorderInChapter = async (chapter: Chapter, orderedIds: string[]) => {
    if (!formation) return;
    setBusyVideoId(orderedIds.find((id) => id !== busyVideoId) ?? null);
    try {
      await reorderVideos(formation.id, chapter.id, orderedIds);
    } finally {
      setBusyVideoId(null);
    }
  };

  const handleMoveUp = async (chapter: Chapter, video: Video) => {
    const sorted = sortVideosByNumber(chapter.videos);
    const index = sorted.findIndex((item) => item.id === video.id);
    if (index <= 0) return;

    const orderedIds = sorted.map((item) => item.id);
    [orderedIds[index - 1], orderedIds[index]] = [orderedIds[index], orderedIds[index - 1]];
    await reorderInChapter(chapter, orderedIds);
  };

  const handleMoveDown = async (chapter: Chapter, video: Video) => {
    const sorted = sortVideosByNumber(chapter.videos);
    const index = sorted.findIndex((item) => item.id === video.id);
    if (index === -1 || index >= sorted.length - 1) return;

    const orderedIds = sorted.map((item) => item.id);
    [orderedIds[index], orderedIds[index + 1]] = [orderedIds[index + 1], orderedIds[index]];
    await reorderInChapter(chapter, orderedIds);
  };

  const handleMoveChapterUp = async (chapter: Chapter) => {
    if (!formation) return;
    const sorted = sortChaptersByNumber(formation.chapters);
    const index = sorted.findIndex((item) => item.id === chapter.id);
    if (index <= 0) return;

    const orderedIds = sorted.map((item) => item.id);
    [orderedIds[index - 1], orderedIds[index]] = [orderedIds[index], orderedIds[index - 1]];
    setBusyChapterId(chapter.id);
    try {
      await reorderChapters(formation.id, orderedIds);
    } finally {
      setBusyChapterId(null);
    }
  };

  const handleMoveChapterDown = async (chapter: Chapter) => {
    if (!formation) return;
    const sorted = sortChaptersByNumber(formation.chapters);
    const index = sorted.findIndex((item) => item.id === chapter.id);
    if (index === -1 || index >= sorted.length - 1) return;

    const orderedIds = sorted.map((item) => item.id);
    [orderedIds[index], orderedIds[index + 1]] = [orderedIds[index + 1], orderedIds[index]];
    setBusyChapterId(chapter.id);
    try {
      await reorderChapters(formation.id, orderedIds);
    } finally {
      setBusyChapterId(null);
    }
  };

  const handleDropOnVideo = async (
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
      await reorderInChapter(targetChapter, orderedIds);
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

  const handleMoveSubmit = async (toChapterId: string, toIndex?: number) => {
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

  const handleStartTranscription = async (video: Video) => {
    if (!formation) return;
    setBusyVideoId(video.id);
    setJobNotice(null);
    try {
      await startTranscription(formation.id, video.id);
    } catch (err) {
      setJobNotice(
        err instanceof Error ? err.message : 'Échec du lancement de la transcription'
      );
    } finally {
      setBusyVideoId(null);
    }
  };

  const handleStartMediaConversion = async (video: Video) => {
    if (!formation) return;
    setBusyVideoId(video.id);
    setJobNotice(null);
    try {
      await startMediaConversion(formation.id, video.id);
    } catch (err) {
      setJobNotice(err instanceof Error ? err.message : 'Échec du lancement de la conversion');
    } finally {
      setBusyVideoId(null);
    }
  };

  const handleGenerateSummary = async (video: Video) => {
    if (!formation) return;
    setBusyVideoId(video.id);
    setJobNotice(null);
    try {
      await generateVideoSummary(formation.id, video.id);
    } catch (err) {
      setJobNotice(err instanceof Error ? err.message : 'Échec du lancement du résumé');
    } finally {
      setBusyVideoId(null);
    }
  };

  const currentVideoProgress = (() => {
    if (!videoDialog) return undefined;
    const key =
      videoDialog.mode === 'create'
        ? studioUploadKeys.create(videoDialog.chapter.id)
        : videoDialog.video
          ? studioUploadKeys.patch(videoDialog.video.id)
          : null;
    return key ? getUploadProgress(key) : undefined;
  })();

  return {
    formation,
    loading,
    error,
    jobNotice,
    clearJobNotice: () => setJobNotice(null),
    formationName,
    setFormationName: handleFormationNameChange,
    savingName,
    nameError,
    busyVideoId,
    busyChapterId,
    draggedVideo,
    setDraggedVideo,
    chapterDialog,
    setChapterDialog,
    videoDialog,
    setVideoDialog,
    documentDialog,
    setDocumentDialog,
    moveDialog,
    setMoveDialog,
    deleteTarget,
    setDeleteTarget,
    deleting,
    currentVideoProgress,
    handleSaveFormationName,
    handleChapterSubmit,
    handleVideoSubmit,
    handleDocumentSubmit,
    handleDocumentEditSubmit,
    handleDelete,
    handleMoveUp,
    handleMoveDown,
    handleMoveChapterUp,
    handleMoveChapterDown,
    handleDropOnVideo,
    handleMoveSubmit,
    handleStartTranscription,
    handleStartMediaConversion,
    handleGenerateSummary,
  };
}
