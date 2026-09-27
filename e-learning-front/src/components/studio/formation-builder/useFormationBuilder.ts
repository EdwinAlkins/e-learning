'use client';

import { useFormationQuery } from '../../../features/catalog/queries/formation.queries';
import { useStudioMutations } from '../../../features/studio/hooks/useStudioMutations';
import { useStudioDialogs } from '../../../features/studio/hooks/useStudioDialogs';
import { useStudioBackgroundJobs } from '../../../features/studio/hooks/useStudioBackgroundJobs';
import { useVideoReorder } from '../../../features/studio/hooks/useVideoReorder';
import { useFormationEditor } from '../../../features/studio/hooks/useFormationEditor';

export function useFormationBuilder(formationId: string) {
  const formationQuery = useFormationQuery(formationId);
  const mutations = useStudioMutations();
  const formation = formationQuery.data ?? null;
  const loading = formationQuery.isLoading;
  const error = formationQuery.error instanceof Error ? formationQuery.error.message : null;
  const dialogs = useStudioDialogs();
  const jobs = useStudioBackgroundJobs({
    formation,
    refreshFormation: mutations.refreshFormation,
    startTranscription: mutations.startTranscription,
    startMediaConversion: mutations.startMediaConversion,
    generateVideoSummary: mutations.generateVideoSummary,
  });
  const reorder = useVideoReorder({
    formation,
    reorderVideos: mutations.reorderVideos,
    reorderChapters: mutations.reorderChapters,
    moveVideo: mutations.moveVideo,
  });
  const {
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
  } = dialogs;
  const editor = useFormationEditor({
    formation,
    chapterDialog,
    videoDialog,
    documentDialog,
    deleteTarget,
    clearDeleteTarget: () => setDeleteTarget(null),
    uploadProgressByKey: mutations.uploadProgressByKey,
    patchFormation: mutations.patchFormation,
    createChapter: mutations.createChapter,
    patchChapter: mutations.patchChapter,
    deleteChapter: mutations.deleteChapter,
    createVideo: mutations.createVideo,
    patchVideo: mutations.patchVideo,
    deleteVideo: mutations.deleteVideo,
    createDocument: mutations.createDocument,
    patchDocument: mutations.patchDocument,
    deleteDocument: mutations.deleteDocument,
    reorderChapters: mutations.reorderChapters,
  });

  const handleMoveSubmit = async (toChapterId: string, toIndex?: number) => {
    await reorder.submitMove(moveDialog, toChapterId, toIndex);
  };

  return {
    formation,
    loading,
    error,
    jobNotice: jobs.notice,
    clearJobNotice: jobs.clearNotice,
    formationName: editor.formationName,
    setFormationName: editor.setFormationName,
    savingName: editor.savingName,
    nameError: editor.nameError,
    busyVideoId: jobs.busyVideoId ?? reorder.busyVideoId,
    busyChapterId: reorder.busyChapterId,
    draggedVideo: reorder.draggedVideo,
    setDraggedVideo: reorder.setDraggedVideo,
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
    deleting: editor.deleting,
    currentVideoProgress: editor.currentVideoProgress,
    handleSaveFormationName: editor.saveFormationName,
    handleChapterSubmit: editor.submitChapter,
    handleVideoSubmit: editor.submitVideo,
    handleDocumentSubmit: editor.submitDocument,
    handleDocumentEditSubmit: editor.editDocument,
    handleDelete: editor.deleteSelection,
    handleMoveUp: reorder.moveUp,
    handleMoveDown: reorder.moveDown,
    handleMoveChapterUp: reorder.moveChapterUp,
    handleMoveChapterDown: reorder.moveChapterDown,
    handleDropOnVideo: reorder.dropOnVideo,
    handleMoveSubmit,
    handleStartTranscription: jobs.startTranscription,
    handleStartMediaConversion: jobs.startMediaConversion,
    handleGenerateSummary: jobs.generateSummary,
  };
}
