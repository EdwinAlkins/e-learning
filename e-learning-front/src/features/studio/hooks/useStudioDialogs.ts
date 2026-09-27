'use client';

import { useState } from 'react';
import type {
  ChapterDialogState,
  DeleteTarget,
  DocumentDialogState,
  MoveDialogState,
  VideoDialogState,
} from '../builder.types';

export function useStudioDialogs() {
  const [chapterDialog, setChapterDialog] = useState<ChapterDialogState>({
    open: false,
    mode: 'create',
  });
  const [videoDialog, setVideoDialog] = useState<VideoDialogState>(null);
  const [documentDialog, setDocumentDialog] = useState<DocumentDialogState>(null);
  const [moveDialog, setMoveDialog] = useState<MoveDialogState>(null);
  const [deleteTarget, setDeleteTarget] = useState<DeleteTarget | null>(null);

  return {
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
  };
}
