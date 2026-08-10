'use client';

import ChapterDialog from '../ChapterDialog';
import ConfirmDeleteDialog from '../ConfirmDeleteDialog';
import DocumentEditDialog from '../DocumentEditDialog';
import DocumentUploadDialog from '../DocumentUploadDialog';
import VideoMoveDialog from '../VideoMoveDialog';
import VideoUploadDialog from '../VideoUploadDialog';
import { sortChaptersByNumber, sortVideosByNumber } from '../../../utils/formation';
import { useFormationBuilderContext } from './FormationBuilderContext';

export default function FormationBuilderDialogs() {
  const {
    formation,
    chapterDialog,
    videoDialog,
    documentDialog,
    moveDialog,
    deleteTarget,
    deleting,
    currentVideoProgress,
    setChapterDialog,
    setVideoDialog,
    setDocumentDialog,
    setMoveDialog,
    setDeleteTarget,
    handleChapterSubmit,
    handleVideoSubmit,
    handleDocumentSubmit,
    handleDocumentEditSubmit,
    handleMoveSubmit,
    handleDelete,
  } = useFormationBuilderContext();

  if (!formation) return null;

  const chapters = sortChaptersByNumber(formation.chapters);

  const deleteTitle =
    deleteTarget?.type === 'chapter'
      ? 'Supprimer le chapitre'
      : deleteTarget?.type === 'document'
        ? 'Supprimer le document'
        : 'Supprimer la vidéo';

  const deleteMessage =
    deleteTarget?.type === 'chapter'
      ? `Voulez-vous supprimer le chapitre « ${deleteTarget.chapter.name} » et toutes ses vidéos ?`
      : deleteTarget?.type === 'document'
        ? `Voulez-vous supprimer le document « ${deleteTarget.document.title} » ?`
        : `Voulez-vous supprimer la vidéo « ${deleteTarget?.type === 'video' ? deleteTarget.video.title : ''} » ?`;

  return (
    <>
      <ChapterDialog
        open={chapterDialog.open}
        mode={chapterDialog.mode}
        initialName={chapterDialog.chapter?.name ?? ''}
        initialOrder={
          chapterDialog.mode === 'edit' && chapterDialog.chapter
            ? chapters.findIndex((item) => item.id === chapterDialog.chapter!.id) + 1
            : undefined
        }
        chapterCount={
          chapterDialog.mode === 'edit' ? chapters.length : undefined
        }
        onClose={() => setChapterDialog({ open: false, mode: 'create' })}
        onSubmit={handleChapterSubmit}
      />

      {videoDialog && (
        <VideoUploadDialog
          open={videoDialog.open}
          mode={videoDialog.mode}
          videoId={videoDialog.video?.id}
          initialTitle={videoDialog.video?.title ?? ''}
          uploadProgress={currentVideoProgress}
          onClose={() => setVideoDialog(null)}
          onSubmit={handleVideoSubmit}
        />
      )}

      {documentDialog?.mode === 'create' && (
        <DocumentUploadDialog
          open={documentDialog.open}
          videos={sortVideosByNumber(documentDialog.chapter.videos)}
          onClose={() => setDocumentDialog(null)}
          onSubmit={handleDocumentSubmit}
        />
      )}

      {documentDialog?.mode === 'edit' && documentDialog.document && (
        <DocumentEditDialog
          open={documentDialog.open}
          document={documentDialog.document}
          videos={sortVideosByNumber(documentDialog.chapter.videos)}
          onClose={() => setDocumentDialog(null)}
          onSubmit={handleDocumentEditSubmit}
        />
      )}

      {moveDialog && (
        <VideoMoveDialog
          open
          chapters={chapters}
          currentChapterId={moveDialog.chapter.id}
          videoTitle={moveDialog.video.title}
          onClose={() => setMoveDialog(null)}
          onSubmit={handleMoveSubmit}
        />
      )}

      <ConfirmDeleteDialog
        open={Boolean(deleteTarget)}
        title={deleteTitle}
        message={deleteMessage}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDelete}
        loading={deleting}
      />
    </>
  );
}
