'use client';

import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Box,
  Button,
  IconButton,
  List,
  ListItem,
  ListItemText,
  Paper,
  Typography,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Description as DescriptionIcon,
  Edit as EditIcon,
  ExpandMore as ExpandMoreIcon,
  OpenInNew as OpenInNewIcon,
} from '@mui/icons-material';
import type { Chapter } from '../../../types';
import { apiService } from '../../../services/api';
import {
  calculateChapterTotalDuration,
  formatDurationDetailed,
  sortVideosByNumber,
} from '../../../utils/formation';
import { useFormationBuilderContext } from './FormationBuilderContext';
import StudioVideoItem from './StudioVideoItem';

interface StudioChapterAccordionProps {
  chapter: Chapter;
  isDeletingChapter: boolean;
}

export default function StudioChapterAccordion({
  chapter,
  isDeletingChapter,
}: StudioChapterAccordionProps) {
  const {
    deleteTarget,
    deleting,
    busyVideoId,
    setChapterDialog,
    setDeleteTarget,
    setVideoDialog,
    setDocumentDialog,
  } = useFormationBuilderContext();

  const sortedVideos = sortVideosByNumber(chapter.videos);
  const documents = [...(chapter.documents ?? [])].sort((a, b) => a.position - b.position);

  return (
    <Accordion defaultExpanded sx={{ mb: 1, opacity: isDeletingChapter ? 0.5 : 1 }}>
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Box sx={{ display: 'flex', alignItems: 'center', width: '100%', gap: 1 }}>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            {chapter.name}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {formatDurationDetailed(calculateChapterTotalDuration(chapter))}
          </Typography>
          <IconButton
            size="small"
            aria-label="Modifier le chapitre"
            onClick={(event) => {
              event.stopPropagation();
              setChapterDialog({ open: true, mode: 'edit', chapter });
            }}
          >
            <EditIcon fontSize="small" />
          </IconButton>
          <IconButton
            size="small"
            aria-label="Supprimer le chapitre"
            onClick={(event) => {
              event.stopPropagation();
              setDeleteTarget({ type: 'chapter', chapter });
            }}
          >
            <DeleteIcon fontSize="small" />
          </IconButton>
        </Box>
      </AccordionSummary>
      <AccordionDetails>
        <List disablePadding>
          {sortedVideos.map((video, videoIndex) => {
            const isBusy = busyVideoId === video.id;
            const isDeletingVideo =
              deleting &&
              deleteTarget?.type === 'video' &&
              deleteTarget.video.id === video.id;

            return (
              <StudioVideoItem
                key={video.id}
                chapter={chapter}
                video={video}
                videoIndex={videoIndex}
                videoCount={sortedVideos.length}
                isBusy={isBusy}
                isDeleting={isDeletingVideo}
              />
            );
          })}
        </List>
        <Button
          startIcon={<AddIcon />}
          onClick={() => setVideoDialog({ open: true, mode: 'create', chapter })}
          sx={{ mt: 1 }}
        >
          Ajouter un média
        </Button>

        <Typography variant="subtitle2" sx={{ mt: 3, mb: 1 }}>
          Documents
        </Typography>
        {documents.length === 0 ? (
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            Aucun document associé
          </Typography>
        ) : (
          <List disablePadding>
            {documents.map((document) => {
              const isDeletingDoc =
                deleting &&
                deleteTarget?.type === 'document' &&
                deleteTarget.document.id === document.id;
              const linkedVideo = document.video_id
                ? chapter.videos.find((v) => v.id === document.video_id)
                : null;

              return (
                <Paper
                  key={document.id}
                  variant="outlined"
                  sx={{ mb: 1, opacity: isDeletingDoc ? 0.5 : 1 }}
                >
                  <ListItem
                    secondaryAction={
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <IconButton
                          size="small"
                          aria-label="Ouvrir le document"
                          component="a"
                          href={apiService.documentFileUrl(document.id)}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          <OpenInNewIcon fontSize="small" />
                        </IconButton>
                        <IconButton
                          size="small"
                          aria-label="Modifier le document"
                          onClick={() =>
                            setDocumentDialog({
                              open: true,
                              mode: 'edit',
                              chapter,
                              document,
                            })
                          }
                        >
                          <EditIcon fontSize="small" />
                        </IconButton>
                        <IconButton
                          size="small"
                          aria-label="Supprimer le document"
                          onClick={() => setDeleteTarget({ type: 'document', chapter, document })}
                        >
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </Box>
                    }
                  >
                    <DescriptionIcon sx={{ mr: 1.5, color: 'text.secondary' }} fontSize="small" />
                    <ListItemText
                      primary={document.title}
                      secondary={
                        linkedVideo
                          ? `${document.filename || document.mime_type || 'Fichier'} · ${linkedVideo.title}`
                          : document.filename || document.mime_type || 'Chapitre entier'
                      }
                    />
                  </ListItem>
                </Paper>
              );
            })}
          </List>
        )}
        <Button
          startIcon={<AddIcon />}
          onClick={() => setDocumentDialog({ open: true, mode: 'create', chapter })}
          sx={{ mt: 1 }}
        >
          Ajouter un document
        </Button>
      </AccordionDetails>
    </Accordion>
  );
}
