'use client';

import { Box, Button } from '@mui/material';
import { Add as AddIcon } from '@mui/icons-material';
import { sortChaptersByNumber } from '../../../utils/formation';
import { useFormationBuilderContext } from './FormationBuilderContext';
import StudioChapterAccordion from './StudioChapterAccordion';

export default function StudioChapterList() {
  const { formation, deleteTarget, deleting, busyChapterId, setChapterDialog } =
    useFormationBuilderContext();

  if (!formation) return null;

  const sortedChapters = sortChaptersByNumber(formation.chapters);

  return (
    <>
      <Box sx={{ mt: 2 }}>
        {sortedChapters.map((chapter, chapterIndex) => {
          const isDeletingChapter =
            deleting &&
            deleteTarget?.type === 'chapter' &&
            deleteTarget.chapter.id === chapter.id;

          return (
            <StudioChapterAccordion
              key={chapter.id}
              chapter={chapter}
              chapterIndex={chapterIndex}
              chapterCount={sortedChapters.length}
              isDeletingChapter={isDeletingChapter}
              isBusy={busyChapterId === chapter.id}
            />
          );
        })}
      </Box>

      <Button
        variant="outlined"
        startIcon={<AddIcon />}
        onClick={() => setChapterDialog({ open: true, mode: 'create' })}
        sx={{ mt: 2 }}
      >
        Ajouter un chapitre
      </Button>
    </>
  );
}
