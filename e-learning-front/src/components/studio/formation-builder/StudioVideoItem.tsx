'use client';

import {
  Box,
  Chip,
  CircularProgress,
  IconButton,
  ListItem,
  ListItemText,
  Paper,
  Tooltip,
} from '@mui/material';
import {
  ArrowDownward as ArrowDownwardIcon,
  ArrowUpward as ArrowUpwardIcon,
  AutoAwesome as AutoAwesomeIcon,
  Delete as DeleteIcon,
  DragIndicator as DragIndicatorIcon,
  DriveFileMove as DriveFileMoveIcon,
  Edit as EditIcon,
  Headphones as HeadphonesIcon,
  Sync as SyncIcon,
  RecordVoiceOver as RecordVoiceOverIcon,
} from '@mui/icons-material';
import type { Chapter, Video } from '../../../types';
import { formatVideoDuration } from '../../../utils/formation';
import { findActiveJob, jobProgressLabel } from '../../../utils/job-progress';
import { useFormationBuilderContext } from './FormationBuilderContext';

interface StudioVideoItemProps {
  chapter: Chapter;
  video: Video;
  videoIndex: number;
  videoCount: number;
  isBusy: boolean;
  isDeleting: boolean;
}

export default function StudioVideoItem({
  chapter,
  video,
  videoIndex,
  videoCount,
  isBusy,
  isDeleting,
}: StudioVideoItemProps) {
  const {
    draggedVideo,
    setDraggedVideo,
    setDeleteTarget,
    setMoveDialog,
    setVideoDialog,
    handleMoveUp,
    handleMoveDown,
    handleDropOnVideo,
    handleStartTranscription,
    handleStartMediaConversion,
    handleGenerateSummary,
  } = useFormationBuilderContext();

  const mediaReady = video.processing_status === 'ready';
  const canConvert =
    video.processing_status === 'ready' || video.processing_status === 'failed';
  const canTranscribe =
    mediaReady &&
    video.transcription_status !== 'processing' &&
    video.transcription_status !== 'ready';
  const canSummarize =
    mediaReady &&
    video.transcription_status === 'ready' &&
    video.summary_status !== 'processing';
  // ready → régénérer possible ; failed/none → générer
  const conversionJob = findActiveJob(video, 'media_conversion');
  const transcriptionJob = findActiveJob(video, 'transcription');
  const summaryJob = findActiveJob(video, 'summary');

  return (
    <Paper
      variant="outlined"
      sx={{
        mb: 1,
        opacity: draggedVideo?.videoId === video.id || isDeleting ? 0.5 : 1,
        borderColor:
          draggedVideo && draggedVideo.videoId !== video.id ? 'divider' : undefined,
      }}
      draggable={!isBusy}
      onDragStart={() => setDraggedVideo({ chapterId: chapter.id, videoId: video.id })}
      onDragEnd={() => setDraggedVideo(null)}
      onDragOver={(event) => {
        event.preventDefault();
      }}
      onDrop={(event) => {
        event.preventDefault();
        const rect = (event.currentTarget as HTMLElement).getBoundingClientRect();
        const insertAfter = event.clientY > rect.top + rect.height / 2;
        void handleDropOnVideo(chapter, video, insertAfter);
      }}
    >
      <ListItem
        secondaryAction={
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            {canConvert && (
              <Tooltip title="Convertir pour le web (si lecture impossible)">
                <span>
                  <IconButton
                    size="small"
                    aria-label="Convertir pour le web"
                    disabled={isBusy}
                    onClick={() => void handleStartMediaConversion(video)}
                  >
                    <SyncIcon fontSize="small" />
                  </IconButton>
                </span>
              </Tooltip>
            )}
            <Tooltip title="Transcrire">
              <span>
                <IconButton
                  size="small"
                  aria-label="Transcrire"
                  disabled={isBusy || !canTranscribe}
                  onClick={() => void handleStartTranscription(video)}
                >
                  <RecordVoiceOverIcon fontSize="small" />
                </IconButton>
              </span>
            </Tooltip>
            <Tooltip
              title={
                video.transcription_status !== 'ready'
                  ? 'Transcription requise'
                  : 'Générer le résumé'
              }
            >
              <span>
                <IconButton
                  size="small"
                  aria-label="Générer le résumé"
                  disabled={isBusy || !canSummarize}
                  onClick={() => void handleGenerateSummary(video)}
                >
                  <AutoAwesomeIcon fontSize="small" />
                </IconButton>
              </span>
            </Tooltip>
            <Tooltip title="Monter">
              <span>
                <IconButton
                  size="small"
                  aria-label="Monter"
                  disabled={isBusy || videoIndex === 0}
                  onClick={() => void handleMoveUp(chapter, video)}
                >
                  <ArrowUpwardIcon fontSize="small" />
                </IconButton>
              </span>
            </Tooltip>
            <Tooltip title="Descendre">
              <span>
                <IconButton
                  size="small"
                  aria-label="Descendre"
                  disabled={isBusy || videoIndex === videoCount - 1}
                  onClick={() => void handleMoveDown(chapter, video)}
                >
                  <ArrowDownwardIcon fontSize="small" />
                </IconButton>
              </span>
            </Tooltip>
            <Tooltip title="Déplacer vers un autre chapitre">
              <IconButton
                size="small"
                aria-label="Déplacer"
                disabled={isBusy}
                onClick={() => setMoveDialog({ chapter, video })}
              >
                <DriveFileMoveIcon fontSize="small" />
              </IconButton>
            </Tooltip>
            <IconButton
              size="small"
              aria-label="Modifier la vidéo"
              disabled={isBusy}
              onClick={() =>
                setVideoDialog({ open: true, mode: 'edit', chapter, video })
              }
            >
              <EditIcon fontSize="small" />
            </IconButton>
            <IconButton
              size="small"
              aria-label="Supprimer la vidéo"
              disabled={isBusy}
              onClick={() => setDeleteTarget({ type: 'video', chapter, video })}
            >
              <DeleteIcon fontSize="small" />
            </IconButton>
          </Box>
        }
      >
        <DragIndicatorIcon sx={{ mr: 1, color: 'text.disabled', cursor: 'grab' }} />
        {isBusy ? <CircularProgress size={20} sx={{ mr: 2 }} /> : null}
        {video.kind === 'audio' ? (
          <HeadphonesIcon sx={{ mr: 1.5, color: 'text.secondary' }} fontSize="small" />
        ) : null}
        <ListItemText
          primary={
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
              <span>{video.title}</span>
              {video.processing_status === 'processing' && (
                <Chip
                  label={jobProgressLabel(conversionJob, 'Conversion…')}
                  size="small"
                  color="warning"
                  variant="outlined"
                  title={conversionJob?.message}
                />
              )}
              {video.processing_status === 'failed' && (
                <Chip label="Échec conversion" size="small" color="error" variant="outlined" />
              )}
              {video.transcription_status === 'processing' && (
                <Chip
                  label={jobProgressLabel(transcriptionJob, 'Transcription…')}
                  size="small"
                  color="info"
                  variant="outlined"
                  title={transcriptionJob?.message}
                />
              )}
              {video.transcription_status === 'ready' && (
                <Chip label="Transcrit" size="small" color="success" variant="outlined" />
              )}
              {video.transcription_status === 'failed' && (
                <Chip label="Échec transcription" size="small" color="error" variant="outlined" />
              )}
              {video.summary_status === 'processing' && (
                <Chip
                  label={jobProgressLabel(summaryJob, 'Résumé…')}
                  size="small"
                  color="info"
                  variant="outlined"
                  title={summaryJob?.message}
                />
              )}
              {video.summary_status === 'ready' && (
                <Chip label="Résumé" size="small" color="success" variant="outlined" />
              )}
              {video.summary_status === 'failed' && (
                <Chip label="Échec résumé" size="small" color="error" variant="outlined" />
              )}
            </Box>
          }
          secondary={`Durée : ${formatVideoDuration(video.duration)}`}
        />
      </ListItem>
    </Paper>
  );
}
