'use client';

import { useState } from 'react';
import type { Formation } from '../../../types';
import type {
  ChapterSubmitData,
  ChapterDialogState,
  DeleteTarget,
  DocumentDialogState,
  VideoDialogState,
} from '../builder.types';
import type { StudioMutations } from './useStudioMutations';
import { studioUploadKeys } from './useStudioMutations';
import { sortChaptersByNumber } from '../../../utils/formation';

type EditorMutations = Pick<
  StudioMutations,
  | 'uploadProgressByKey'
  | 'patchFormation'
  | 'createChapter'
  | 'patchChapter'
  | 'deleteChapter'
  | 'createVideo'
  | 'patchVideo'
  | 'deleteVideo'
  | 'createDocument'
  | 'patchDocument'
  | 'deleteDocument'
  | 'reorderChapters'
>;

interface UseFormationEditorOptions extends EditorMutations {
  formation: Formation | null;
  chapterDialog: ChapterDialogState;
  videoDialog: VideoDialogState;
  documentDialog: DocumentDialogState;
  deleteTarget: DeleteTarget | null;
  clearDeleteTarget: () => void;
}

const moveIdToOrder = (ids: string[], id: string, order1Based: number): string[] => {
  const without = ids.filter((item) => item !== id);
  const targetIndex = Math.max(0, Math.min(order1Based - 1, without.length));
  without.splice(targetIndex, 0, id);
  return without;
};

export function useFormationEditor({
  formation,
  chapterDialog,
  videoDialog,
  documentDialog,
  deleteTarget,
  clearDeleteTarget,
  uploadProgressByKey,
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
  reorderChapters,
}: UseFormationEditorOptions) {
  const [formationName, setFormationName] = useState('');
  const [editingName, setEditingName] = useState(false);
  const [savingName, setSavingName] = useState(false);
  const [nameError, setNameError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);
  const displayedFormationName = editingName ? formationName : (formation?.name ?? '');

  const handleFormationNameChange = (value: string) => {
    setEditingName(true);
    setFormationName(value);
  };

  const saveFormationName = async () => {
    if (!formation || displayedFormationName.trim() === formation.name) return;
    setSavingName(true);
    setNameError(null);
    try {
      await patchFormation(formation.id, { name: displayedFormationName.trim() });
      setEditingName(false);
    } catch (error) {
      setNameError(error instanceof Error ? error.message : 'Erreur lors de la sauvegarde');
    } finally {
      setSavingName(false);
    }
  };

  const submitChapter = async (data: ChapterSubmitData) => {
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
        await reorderChapters(
          formation.id,
          moveIdToOrder(
            sorted.map((item) => item.id),
            chapter.id,
            data.order
          )
        );
      }
    }
  };

  const submitVideo = async (data: { title: string; file?: File }) => {
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

  const submitDocument = async (data: {
    title: string;
    file: File;
    videoId?: string | null;
  }) => {
    if (!formation || documentDialog?.mode !== 'create') return;
    await createDocument(formation.id, documentDialog.chapter.id, data);
  };

  const editDocument = async (data: { title: string; videoId: string | null }) => {
    if (!formation || documentDialog?.mode !== 'edit' || !documentDialog.document) return;
    await patchDocument(formation.id, documentDialog.document.id, {
      title: data.title,
      video_id: data.videoId,
    });
  };

  const deleteSelection = async () => {
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
      clearDeleteTarget();
    } catch (error) {
      console.error(error);
    } finally {
      setDeleting(false);
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
    return key ? uploadProgressByKey[key] : undefined;
  })();

  return {
    formationName: displayedFormationName,
    setFormationName: handleFormationNameChange,
    savingName,
    nameError,
    deleting,
    currentVideoProgress,
    saveFormationName,
    submitChapter,
    submitVideo,
    submitDocument,
    editDocument,
    deleteSelection,
  };
}
