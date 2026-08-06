'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  Container,
  Typography,
  Box,
  Paper,
  IconButton,
  CircularProgress,
  Alert,
  Button,
  Collapse,
  Tab,
  Tabs,
  useTheme,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  AutoAwesome as AutoAwesomeIcon,
  Edit as EditIcon,
  Save as SaveIcon,
  Cancel as CancelIcon,
  RecordVoiceOver as RecordVoiceOverIcon,
  SkipPrevious as SkipPreviousIcon,
  SkipNext as SkipNextIcon,
} from '@mui/icons-material';
import MDEditor from '@uiw/react-md-editor';
import '@uiw/react-md-editor/markdown-editor.css';
import VideoPlayer from '../../../components/VideoPlayer';
import type { VideoPlayerRef } from '../../../components/VideoPlayer';
import AudioPlayer from '../../../components/AudioPlayer';
import NotesPanel from '../../../components/NotesPanel';
import NotesList, { type NotesListRef } from '../../../components/NotesList';
import DocumentsPanel from '../../../components/DocumentsPanel';
import ProgressIndicator from '../../../components/ProgressIndicator';
import MarkdownRenderer from '../../../components/MarkdownRenderer';
import { usePlayerStore } from '../../../stores/player.store';
import { useCatalogStore } from '../../../stores/catalog.store';
import { apiService } from '../../../services/api';
import type { Document, Video, Formation } from '../../../types';
import AuthGuard from '../../../components/AuthGuard';
import { flattenFormationVideos } from '../../../utils/formation';
import { findActiveJob, jobProgressLabel } from '../../../utils/job-progress';
import { POLLING_INTERVAL_MS } from '../../../constants';
import { setVisibilityInterval } from '../../../utils/visibility-interval';

export default function Player() {
  const params = useParams();
  const videoId = params.videoId as string;
  const router = useRouter();
  const videoPlayerRef = useRef<VideoPlayerRef>(null);
  const notesListRef = useRef<NotesListRef>(null);

  const [video, setVideo] = useState<Video | null>(null);
  const [parentFormation, setParentFormation] = useState<Formation | null>(null);
  const [chapterId, setChapterId] = useState<string | null>(null);
  const [prevVideo, setPrevVideo] = useState<Video | null>(null);
  const [nextVideo, setNextVideo] = useState<Video | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [summary, setSummary] = useState<string | null>(null);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [summaryError, setSummaryError] = useState<string | null>(null);
  const [showSummary, setShowSummary] = useState(false);
  const [isEditingSummary, setIsEditingSummary] = useState(false);
  const [editSummaryContent, setEditSummaryContent] = useState<string>('');
  const [savingSummary, setSavingSummary] = useState(false);
  const [aiJobBusy, setAiJobBusy] = useState(false);
  const [aiJobError, setAiJobError] = useState<string | null>(null);
  const [bottomTab, setBottomTab] = useState(0);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [documentsLoading, setDocumentsLoading] = useState(false);
  const [documentsError, setDocumentsError] = useState<string | null>(null);

  const { setVideo: setPlayerVideo, setCurrentTime } = usePlayerStore();
  const { formations, loading: catalogLoading, fetchFormations } = useCatalogStore();
  const theme = useTheme();

  useEffect(() => {
    fetchFormations();
  }, [fetchFormations]);

  useEffect(() => {
    if (!videoId) {
      setError('Identifiant vidéo manquant');
      setLoading(false);
      return;
    }

    // Ne bloque pas la synchro des statuts IA pendant un reload catalogue.
    if (formations.length === 0) {
      return;
    }

    let foundVideo: Video | null = null;
    let currentFormation: Formation | null = null;
    let currentChapterId: string | null = null;

    for (const formation of formations) {
      for (const chapter of formation.chapters) {
        const v = chapter.videos.find((vid) => vid.id === videoId);
        if (v) {
          foundVideo = v;
          currentFormation = formation;
          currentChapterId = chapter.id;
          break;
        }
      }
      if (foundVideo) break;
    }

    if (foundVideo && currentFormation) {
      const nextVideo = foundVideo;
      setVideo((prev) => {
        // Toujours reprendre les statuts frais du catalogue (évite « Génération… » fantôme).
        if (
          prev &&
          prev.id === nextVideo.id &&
          prev.processing_status === nextVideo.processing_status &&
          prev.transcription_status === nextVideo.transcription_status &&
          prev.summary_status === nextVideo.summary_status &&
          prev.title === nextVideo.title &&
          prev.duration === nextVideo.duration &&
          JSON.stringify(prev.active_jobs ?? []) === JSON.stringify(nextVideo.active_jobs ?? [])
        ) {
          return prev;
        }
        return nextVideo;
      });
      setParentFormation(currentFormation);
      setChapterId(currentChapterId);
      setPlayerVideo(videoId);
      setError(null);

      const flatVideos = flattenFormationVideos(currentFormation.chapters);
      const currentIndex = flatVideos.findIndex((v) => v.id === videoId);
      if (currentIndex !== -1) {
        setPrevVideo(currentIndex > 0 ? flatVideos[currentIndex - 1] : null);
        setNextVideo(currentIndex < flatVideos.length - 1 ? flatVideos[currentIndex + 1] : null);
      }
    } else {
      setVideo(null);
      setParentFormation(null);
      setChapterId(null);
      setPrevVideo(null);
      setNextVideo(null);
      setError('Vidéo introuvable');
    }

    setLoading(false);
  }, [videoId, formations, setPlayerVideo]);

  useEffect(() => {
    setSummary(null);
    setShowSummary(false);
    setSummaryError(null);
    setIsEditingSummary(false);
    setEditSummaryContent('');
    setAiJobError(null);
    setBottomTab(0);
  }, [videoId]);

  useEffect(() => {
    if (!video) return;
    const aiProcessing =
      video.transcription_status === 'processing' || video.summary_status === 'processing';
    if (!aiProcessing) return;
    return setVisibilityInterval(() => {
      void fetchFormations(true, true);
    }, POLLING_INTERVAL_MS);
  }, [video?.id, video?.transcription_status, video?.summary_status, fetchFormations]);

  useEffect(() => {
    if (!video) return;
    if (video.transcription_status === 'failed') {
      setAiJobError('Échec de la transcription');
    } else if (video.summary_status === 'failed') {
      setAiJobError('Échec de la génération du résumé (vérifiez la connexion API LLM)');
    } else if (
      video.transcription_status === 'ready' ||
      video.summary_status === 'ready'
    ) {
      setAiJobError(null);
    }
  }, [video?.id, video?.transcription_status, video?.summary_status]);

  useEffect(() => {
    if (!video || video.summary_status !== 'ready' || summary !== null) return;
    let cancelled = false;
    const loadReadySummary = async () => {
      try {
        const text = await apiService.getVideoSummary(videoId);
        if (!cancelled) {
          setSummary(text);
          setSummaryError(null);
        }
      } catch {
        // résumé pas encore lisible côté fichier
      }
    };
    void loadReadySummary();
    return () => {
      cancelled = true;
    };
  }, [video, videoId, summary]);

  useEffect(() => {
    if (!chapterId) {
      setDocuments([]);
      return;
    }

    const chapterFromCatalog = parentFormation?.chapters.find((c) => c.id === chapterId);
    if (chapterFromCatalog?.documents) {
      setDocuments(chapterFromCatalog.documents);
      setDocumentsError(null);
      setDocumentsLoading(false);
      return;
    }

    let cancelled = false;
    const loadDocuments = async () => {
      setDocumentsLoading(true);
      setDocumentsError(null);
      try {
        const docs = await apiService.getChapterDocuments(chapterId);
        if (!cancelled) setDocuments(docs);
      } catch (err) {
        if (!cancelled) {
          setDocuments([]);
          setDocumentsError(
            err instanceof Error ? err.message : 'Échec du chargement des documents'
          );
        }
      } finally {
        if (!cancelled) setDocumentsLoading(false);
      }
    };

    void loadDocuments();
    return () => {
      cancelled = true;
    };
  }, [chapterId, parentFormation]);

  const visibleDocuments = useMemo(
    () => documents.filter((doc) => doc.video_id === videoId),
    [documents, videoId]
  );

  useEffect(() => {
    if (!videoId) return;

    let cancelled = false;

    const loadProgress = async () => {
      try {
        const lastPosition = await apiService.getProgress(videoId);
        if (cancelled || lastPosition === null) return;
        // seekTo file la position jusqu'à loadedmetadata (VideoPlayer / AudioPlayer)
        videoPlayerRef.current?.seekTo(lastPosition);
        setCurrentTime(lastPosition);
      } catch (err) {
        console.error('Failed to load progress:', err);
      }
    };

    void loadProgress();
    return () => {
      cancelled = true;
    };
  }, [videoId, setCurrentTime]);

  const handleSeekTo = (time: number) => {
    videoPlayerRef.current?.seekTo(time);
  };

  const handleNoteCreated = () => {
    notesListRef.current?.refresh();
  };

  const handleGetSummary = async () => {
    if (!videoId) return;

    if (summary !== null) {
      setShowSummary(!showSummary);
      return;
    }

    setSummaryLoading(true);
    setSummaryError(null);
    setShowSummary(true);

    try {
      const summaryText = await apiService.getVideoSummary(videoId);
      setSummary(summaryText);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Échec du chargement du résumé';
      setSummaryError(errorMessage);
      setShowSummary(false);
    } finally {
      setSummaryLoading(false);
    }
  };

  const handleEditSummary = () => {
    if (summary) {
      setIsEditingSummary(true);
      setEditSummaryContent(summary);
    }
  };

  const handleSaveSummary = async () => {
    if (!videoId || !editSummaryContent.trim()) {
      alert('Le résumé ne peut pas être vide');
      return;
    }

    setSavingSummary(true);
    try {
      const updatedSummary = await apiService.updateVideoSummary(videoId, editSummaryContent.trim());
      setSummary(updatedSummary);
      setIsEditingSummary(false);
      setEditSummaryContent('');
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Échec de la mise à jour du résumé';
      alert(errorMessage);
    } finally {
      setSavingSummary(false);
    }
  };

  const handleCancelEditSummary = () => {
    setIsEditingSummary(false);
    setEditSummaryContent('');
  };

  const handleStartTranscription = async () => {
    if (!videoId) return;
    setAiJobBusy(true);
    setAiJobError(null);
    try {
      const updated = await apiService.startTranscription(videoId);
      setVideo(updated);
      void fetchFormations(true, true);
    } catch (err) {
      setAiJobError(
        err instanceof Error ? err.message : 'Échec du lancement de la transcription'
      );
    } finally {
      setAiJobBusy(false);
    }
  };

  const handleGenerateSummary = async () => {
    if (!videoId) return;
    setAiJobBusy(true);
    setAiJobError(null);
    try {
      const updated = await apiService.generateVideoSummary(videoId);
      setVideo(updated);
      setShowSummary(true);
      void fetchFormations(true, true);
    } catch (err) {
      setAiJobError(err instanceof Error ? err.message : 'Échec de la génération du résumé');
    } finally {
      setAiJobBusy(false);
    }
  };

  const handleGoBack = () => {
    if (parentFormation) {
      router.push(`/formation/${encodeURIComponent(parentFormation.id)}`);
    } else {
      router.push('/');
    }
  };

  const navigateToVideo = (target: Video) => {
    router.push(`/player/${target.id}`);
  };

  if (loading || (catalogLoading && !video)) {
    return (
      <AuthGuard>
        <Container maxWidth="lg" sx={{ py: 4 }}>
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
            <CircularProgress />
          </Box>
        </Container>
      </AuthGuard>
    );
  }

  if (error || !video) {
    return (
      <AuthGuard>
        <Container maxWidth="lg" sx={{ py: 4 }}>
          <Alert severity="error">{error || 'Vidéo introuvable'}</Alert>
        </Container>
      </AuthGuard>
    );
  }

  const conversionJob = findActiveJob(video, 'media_conversion');
  const transcriptionJob = findActiveJob(video, 'transcription');
  const summaryJob = findActiveJob(video, 'summary');

  return (
    <AuthGuard>
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Box
          sx={{
            display: 'flex',
            alignItems: { xs: 'flex-start', sm: 'center' },
            flexDirection: { xs: 'column', sm: 'row' },
            gap: { xs: 2, sm: 0 },
            mb: 3,
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', flexGrow: 1, minWidth: 0 }}>
            <IconButton onClick={handleGoBack} sx={{ mr: 1 }} aria-label="Retour">
              <ArrowBackIcon />
            </IconButton>
            <Box sx={{ minWidth: 0 }}>
              {parentFormation && (
                <Typography variant="caption" color="text.secondary" display="block" noWrap>
                  {parentFormation.name}
                </Typography>
              )}
              <Typography variant="h5" component="h1" noWrap title={video.title}>
                {video.title}
              </Typography>
            </Box>
          </Box>

          <Box sx={{ display: 'flex', gap: 1, flexShrink: 0, alignSelf: { xs: 'stretch', sm: 'auto' } }}>
            <Button
              variant="outlined"
              startIcon={<SkipPreviousIcon />}
              disabled={!prevVideo}
              onClick={() => prevVideo && navigateToVideo(prevVideo)}
              sx={{ display: { xs: 'none', sm: 'flex' } }}
            >
              Précédent
            </Button>
            <IconButton
              color="primary"
              disabled={!prevVideo}
              onClick={() => prevVideo && navigateToVideo(prevVideo)}
              sx={{ display: { xs: 'flex', sm: 'none' } }}
              aria-label="Vidéo précédente"
            >
              <SkipPreviousIcon />
            </IconButton>

            <Button
              variant="contained"
              endIcon={<SkipNextIcon />}
              disabled={!nextVideo}
              onClick={() => nextVideo && navigateToVideo(nextVideo)}
              sx={{ display: { xs: 'none', sm: 'flex' } }}
            >
              Suivant
            </Button>
            <IconButton
              color="primary"
              disabled={!nextVideo}
              onClick={() => nextVideo && navigateToVideo(nextVideo)}
              sx={{ display: { xs: 'flex', sm: 'none' } }}
              aria-label="Vidéo suivante"
            >
              <SkipNextIcon />
            </IconButton>
          </Box>
        </Box>

        {(prevVideo || nextVideo) && (
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'space-between',
              gap: 2,
              mb: 2,
              flexDirection: { xs: 'column', sm: 'row' },
            }}
          >
            {prevVideo ? (
              <Typography
                variant="caption"
                color="text.secondary"
                sx={{ cursor: 'pointer', '&:hover': { color: 'primary.main' } }}
                onClick={() => navigateToVideo(prevVideo)}
              >
                ← {prevVideo.title}
              </Typography>
            ) : (
              <span />
            )}
            {nextVideo && (
              <Typography
                variant="caption"
                color="text.secondary"
                sx={{
                  cursor: 'pointer',
                  textAlign: { xs: 'left', sm: 'right' },
                  '&:hover': { color: 'primary.main' },
                }}
                onClick={() => navigateToVideo(nextVideo)}
              >
                {nextVideo.title} →
              </Typography>
            )}
          </Box>
        )}

        <Paper sx={{ p: 2, mb: 3 }}>
          {video.processing_status === 'processing' ? (
            <Alert severity="info">
              {jobProgressLabel(conversionJob, 'Conversion du média en cours…')}
              {conversionJob?.message ? ` — ${conversionJob.message}` : ''}
            </Alert>
          ) : video.processing_status === 'failed' ? (
            <Alert severity="error">Échec de la conversion du média.</Alert>
          ) : video.kind === 'audio' ? (
            <AudioPlayer ref={videoPlayerRef} videoId={videoId} />
          ) : (
            <VideoPlayer ref={videoPlayerRef} videoId={videoId} />
          )}
          <Box sx={{ mt: 2 }}>
            <ProgressIndicator
              duration={video.duration}
              rightElement={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                  {video.transcription_status !== 'ready' && (
                    <Button
                      variant="outlined"
                      size="small"
                      title={transcriptionJob?.message || undefined}
                      startIcon={
                        video.transcription_status === 'processing' || aiJobBusy ? (
                          <CircularProgress size={14} color="inherit" />
                        ) : (
                          <RecordVoiceOverIcon fontSize="small" />
                        )
                      }
                      onClick={() => void handleStartTranscription()}
                      disabled={
                        aiJobBusy ||
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
                  {video.summary_status !== 'ready' && (
                    <Button
                      variant="outlined"
                      size="small"
                      title={summaryJob?.message || undefined}
                      startIcon={
                        video.summary_status === 'processing' || aiJobBusy ? (
                          <CircularProgress size={14} color="inherit" />
                        ) : (
                          <AutoAwesomeIcon fontSize="small" />
                        )
                      }
                      onClick={() => void handleGenerateSummary()}
                      disabled={
                        aiJobBusy ||
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
                      onClick={handleGetSummary}
                      disabled={summaryLoading || video.processing_status !== 'ready'}
                      size="small"
                      sx={{ minWidth: 'auto', px: 1.5 }}
                    >
                      {summaryLoading ? 'Chargement…' : 'Résumé'}
                    </Button>
                  )}
                  {video.summary_status === 'ready' && (
                    <Button
                      variant="text"
                      size="small"
                      startIcon={<AutoAwesomeIcon fontSize="small" />}
                      onClick={() => void handleGenerateSummary()}
                      disabled={aiJobBusy || video.processing_status !== 'ready'}
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
        {(aiJobError ||
          video.transcription_status === 'failed' ||
          video.summary_status === 'failed' ||
          (video.transcription_status !== 'ready' &&
            video.transcription_status !== 'processing' &&
            video.summary_status !== 'ready')) && (
          <Box sx={{ mb: 3, display: 'flex', flexDirection: 'column', gap: 1 }}>
            {aiJobError && <Alert severity="error">{aiJobError}</Alert>}
            {video.transcription_status === 'failed' && (
              <Alert severity="error">Échec de la transcription. Vous pouvez relancer.</Alert>
            )}
            {video.summary_status === 'failed' && (
              <Alert severity="error">Échec de la génération du résumé.</Alert>
            )}
            {video.transcription_status !== 'ready' &&
              video.transcription_status !== 'failed' &&
              video.transcription_status !== 'processing' &&
              video.summary_status !== 'ready' && (
                <Alert severity="info">
                  Une transcription est nécessaire avant de générer le résumé.
                </Alert>
              )}
          </Box>
        )}
        {summaryError && (
          <Box sx={{ mb: 3 }}>
            <Alert severity="error">{summaryError}</Alert>
          </Box>
        )}
        <Collapse in={showSummary && !summaryLoading && !summaryError}>
          <Box sx={{ mb: 3 }}>
            {summary && (
              <Paper sx={{ p: 2, backgroundColor: 'background.default' }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6">Résumé</Typography>
                  <Box>
                    {isEditingSummary ? (
                      <>
                        <IconButton
                          size="small"
                          aria-label="Enregistrer"
                          onClick={handleSaveSummary}
                          disabled={savingSummary}
                          color="primary"
                        >
                          <SaveIcon />
                        </IconButton>
                        <IconButton
                          size="small"
                          aria-label="Annuler"
                          onClick={handleCancelEditSummary}
                          disabled={savingSummary}
                        >
                          <CancelIcon />
                        </IconButton>
                      </>
                    ) : (
                      <IconButton size="small" aria-label="Modifier" onClick={handleEditSummary}>
                        <EditIcon />
                      </IconButton>
                    )}
                  </Box>
                </Box>
                <Collapse in={isEditingSummary}>
                  <Box sx={{ mb: 2 }}>
                    <MDEditor
                      value={editSummaryContent}
                      onChange={(value) => setEditSummaryContent(value || '')}
                      preview="edit"
                      hideToolbar={false}
                      visibleDragbar={false}
                      data-color-mode={theme.palette.mode}
                      height={400}
                    />
                  </Box>
                </Collapse>
                {!isEditingSummary && summary !== null && (
                  <MarkdownRenderer source={summary} />
                )}
              </Paper>
            )}
          </Box>
        </Collapse>

        <Box sx={{ mb: 3 }}>
          <Tabs
            value={bottomTab}
            onChange={(_, value: number) => setBottomTab(value)}
            sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}
          >
            <Tab label="Notes" />
            <Tab label={`Documents${visibleDocuments.length ? ` (${visibleDocuments.length})` : ''}`} />
          </Tabs>

          {bottomTab === 0 && (
            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 3 }}>
              <Box>
                <NotesPanel videoId={videoId} onNoteCreated={handleNoteCreated} />
              </Box>
              <Box>
                <NotesList ref={notesListRef} videoId={videoId} onSeekTo={handleSeekTo} />
              </Box>
            </Box>
          )}

          {bottomTab === 1 && (
            <DocumentsPanel
              documents={visibleDocuments}
              loading={documentsLoading}
              error={documentsError}
            />
          )}
        </Box>
      </Container>
    </AuthGuard>
  );
}
