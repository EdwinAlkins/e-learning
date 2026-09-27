'use client';

import type { RefObject } from 'react';
import { Alert, Box, Button, CircularProgress, Paper } from '@mui/material';
import {
  AutoAwesome as AutoAwesomeIcon,
  RecordVoiceOver as RecordVoiceOverIcon,
} from '@mui/icons-material';
import type { Video } from '../../../types';
import AudioPlayer from '../../../components/AudioPlayer';
import VideoPlayer, { type VideoPlayerRef } from '../../../components/VideoPlayer';
import ProgressIndicator from '../../../components/ProgressIndicator';
import { findActiveJob, jobProgressLabel } from '../../../utils/job-progress';

interface PlayerMediaPanelProps {
  videoId: string;
  video: Video;
  playerRef: RefObject<VideoPlayerRef | null>;
  isAdmin: boolean;
  jobBusy: boolean;
  summaryLoading: boolean;
  onStartTranscription: () => void;
  onGenerateSummary: () => void;
  onToggleSummary: () => void;
}

export default function PlayerMediaPanel({
  videoId,
  video,
  playerRef,
  isAdmin,
  jobBusy,
  summaryLoading,
  onStartTranscription,
  onGenerateSummary,
  onToggleSummary,
}: PlayerMediaPanelProps) {
  const conversionJob = findActiveJob(video, 'media_conversion');
  const transcriptionJob = findActiveJob(video, 'transcription');
  const summaryJob = findActiveJob(video, 'summary');

  return (
    <Paper sx={{ p: 2, mb: 3 }}>
      {video.processing_status === 'processing' ? (
        <Alert severity="info">
          {jobProgressLabel(conversionJob, 'Conversion du média en cours…')}
          {conversionJob?.message ? ` — ${conversionJob.message}` : ''}
        </Alert>
      ) : video.processing_status === 'failed' ? (
        <Alert severity="error">Échec de la conversion du média.</Alert>
      ) : video.kind === 'audio' ? (
        <AudioPlayer ref={playerRef} videoId={videoId} />
      ) : (
        <VideoPlayer ref={playerRef} videoId={videoId} />
      )}

      <Box sx={{ mt: 2 }}>
        <ProgressIndicator
          duration={video.duration}
          rightElement={
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
              {isAdmin && video.transcription_status !== 'ready' && (
                <Button
                  variant="outlined"
                  size="small"
                  title={transcriptionJob?.message || undefined}
                  startIcon={
                    video.transcription_status === 'processing' || jobBusy ? (
                      <CircularProgress size={14} color="inherit" />
                    ) : (
                      <RecordVoiceOverIcon fontSize="small" />
                    )
                  }
                  onClick={onStartTranscription}
                  disabled={
                    jobBusy ||
                    video.processing_status !== 'ready' ||
                    video.transcription_status === 'processing'
                  }
                  sx={{ minWidth: 'auto', px: 1.5 }}
                >
                  {video.transcription_status === 'processing'
                    ? jobProgressLabel(transcriptionJob, 'Transcription…')
                    : 'Transcrire'}
                </Button>
              )}
              {isAdmin && video.summary_status !== 'ready' && (
                <Button
                  variant="outlined"
                  size="small"
                  title={summaryJob?.message || undefined}
                  startIcon={
                    video.summary_status === 'processing' || jobBusy ? (
                      <CircularProgress size={14} color="inherit" />
                    ) : (
                      <AutoAwesomeIcon fontSize="small" />
                    )
                  }
                  onClick={onGenerateSummary}
                  disabled={
                    jobBusy ||
                    video.processing_status !== 'ready' ||
                    video.transcription_status !== 'ready' ||
                    video.summary_status === 'processing'
                  }
                  sx={{ minWidth: 'auto', px: 1.5 }}
                >
                  {video.summary_status === 'processing'
                    ? jobProgressLabel(summaryJob, 'Génération…')
                    : 'Générer'}
                </Button>
              )}
              {video.summary_status === 'ready' && (
                <Button
                  variant="outlined"
                  onClick={onToggleSummary}
                  disabled={summaryLoading || video.processing_status !== 'ready'}
                  size="small"
                  sx={{ minWidth: 'auto', px: 1.5 }}
                >
                  {summaryLoading ? 'Chargement…' : 'Résumé'}
                </Button>
              )}
              {isAdmin && video.summary_status === 'ready' && (
                <Button
                  variant="text"
                  size="small"
                  startIcon={<AutoAwesomeIcon fontSize="small" />}
                  onClick={onGenerateSummary}
                  disabled={jobBusy || video.processing_status !== 'ready'}
                  sx={{ minWidth: 'auto', px: 1 }}
                >
                  Régénérer
                </Button>
              )}
            </Box>
          }
        />
      </Box>
    </Paper>
  );
}

interface PlayerJobNoticesProps {
  video: Video;
  isAdmin: boolean;
  error: string | null;
}

export function PlayerJobNotices({ video, isAdmin, error }: PlayerJobNoticesProps) {
  const visible =
    error ||
    video.transcription_status === 'failed' ||
    video.summary_status === 'failed' ||
    (isAdmin &&
      video.transcription_status !== 'ready' &&
      video.transcription_status !== 'processing' &&
      video.summary_status !== 'ready');

  if (!visible) return null;

  return (
    <Box sx={{ mb: 3, display: 'flex', flexDirection: 'column', gap: 1 }}>
      {error && <Alert severity="error">{error}</Alert>}
      {video.transcription_status === 'failed' && (
        <Alert severity="error">
          {isAdmin
            ? 'Échec de la transcription. Vous pouvez relancer.'
            : 'Échec de la transcription.'}
        </Alert>
      )}
      {video.summary_status === 'failed' && (
        <Alert severity="error">Échec de la génération du résumé.</Alert>
      )}
      {isAdmin &&
        video.transcription_status !== 'ready' &&
        video.transcription_status !== 'failed' &&
        video.transcription_status !== 'processing' &&
        video.summary_status !== 'ready' && (
          <Alert severity="info">
            Une transcription est nécessaire avant de générer le résumé.
          </Alert>
        )}
    </Box>
  );
}
