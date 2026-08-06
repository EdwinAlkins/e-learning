'use client';

import { useEffect, useLayoutEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import {
  Container,
  Typography,
  Box,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemButton,
  CircularProgress,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  LinearProgress,
  Chip,
  Collapse,
  IconButton,
  Tooltip,
} from '@mui/material';
import { useTheme } from '@mui/material/styles';
import {
  ExpandMore as ExpandMoreIcon,
  PlayArrow as PlayIcon,
  ArrowBack as ArrowBackIcon,
  Description as DescriptionIcon,
  Folder as FolderIcon,
  FolderOpen as FolderOpenIcon,
  Headphones as HeadphonesIcon,
} from '@mui/icons-material';
import { useCatalogStore } from '../../../stores/catalog.store';
import { apiService } from '../../../services/api';
import type { Document, Video, FormationProgress, Formation } from '../../../types';
import AuthGuard from '../../../components/AuthGuard';
import DocumentsPanel from '../../../components/DocumentsPanel';
import FormationAssistant from '../../../components/FormationAssistant';
import {
  sortVideosByNumber,
  sortChaptersByNumber,
  calculateChapterTotalDuration,
  calculateFormationTotalDuration,
  formatDurationDetailed,
  formatVideoDuration,
  getChipColor,
  getChipBackgroundColor,
  getChipBorderColor,
  getChipTextColor,
} from '../../../utils/formation';
import {
  loadChapterExpandedState,
  saveChapterExpanded,
} from '../../../utils/formation-chapter-storage';
import { POLLING_INTERVAL_MS } from '../../../constants';
import { setVisibilityInterval } from '../../../utils/visibility-interval';

const sortDocuments = (documents: Document[]): Document[] =>
  [...documents].sort((a, b) => a.position - b.position);

const chapterLevelDocuments = (documents: Document[] | undefined): Document[] =>
  sortDocuments((documents ?? []).filter((doc) => !doc.video_id));

const videoDocuments = (documents: Document[] | undefined, videoId: string): Document[] =>
  sortDocuments((documents ?? []).filter((doc) => doc.video_id === videoId));

export default function FormationDetail() {
  const params = useParams();
  const formationIdDecoded = decodeURIComponent(params.formationId as string);
  const { formations, loading, error, fetchFormations } = useCatalogStore();
  const router = useRouter();
  const theme = useTheme();

  const [formation, setFormation] = useState<Formation | null>(null);
  const [progressData, setProgressData] = useState<FormationProgress | null>(null);
  const [progressLoading, setProgressLoading] = useState(false);
  const [expandedChapters, setExpandedChapters] = useState<Record<string, boolean> | null>(
    null
  );
  const [expandedVideoDocs, setExpandedVideoDocs] = useState<Record<string, boolean>>({});

  useEffect(() => {
    void fetchFormations(true);
  }, [fetchFormations]);

  useLayoutEffect(() => {
    if (!formation) {
      setExpandedChapters(null);
      return;
    }
    // Ne réinitialise pas l'UI à chaque poll (nouvelle référence formation).
    setExpandedChapters((prev) => prev ?? loadChapterExpandedState(formation));
  }, [formation]);

  useEffect(() => {
    if (formations.length > 0) {
      const found = formations.find((f) => f.id === formationIdDecoded);
      setFormation(found ?? null);
    }
  }, [formations, formationIdDecoded]);

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
    if (!formation?.id || !processingJobKey) return;
    return setVisibilityInterval(() => {
      void fetchFormations(true, true);
    }, POLLING_INTERVAL_MS);
  }, [formation?.id, processingJobKey, fetchFormations]);

  useEffect(() => {
    if (!formation) return;

    let cancelled = false;

    const loadProgress = async () => {
      setProgressLoading(true);
      try {
        const progress = await apiService.getFormationProgress(formation.id);
        if (!cancelled) setProgressData(progress);
      } catch (err) {
        console.error('Error fetching progress', err);
      } finally {
        if (!cancelled) setProgressLoading(false);
      }
    };

    void loadProgress();
    return () => {
      cancelled = true;
    };
  }, [formation?.id]);

  const handleVideoClick = (video: Video) => {
    router.push(`/player/${video.id}`);
  };

  const handleChapterChange =
    (chapterId: string) => (_event: React.SyntheticEvent, isExpanded: boolean) => {
      if (!formation) return;
      setExpandedChapters((prev) => {
        const newState = { ...prev, [chapterId]: isExpanded };
        saveChapterExpanded(formation.id, chapterId, isExpanded);
        return newState;
      });
    };

  if ((loading && !formation) || (formations.length === 0 && !error && loading)) {
    return (
      <AuthGuard>
        <Container maxWidth="lg" sx={{ py: 4 }}>
          <Box sx={{ display: 'flex', justifyContent: 'center', minHeight: '50vh', alignItems: 'center' }}>
            <CircularProgress />
          </Box>
        </Container>
      </AuthGuard>
    );
  }

  if (error || (!formation && formations.length > 0)) {
    return (
      <AuthGuard>
        <Container maxWidth="lg" sx={{ py: 4 }}>
          <Alert severity="error">{error || 'Formation non trouvée'}</Alert>
          <Box sx={{ mt: 2 }}>
            <IconButton onClick={() => router.push('/')} aria-label="Retour">
              <ArrowBackIcon />
            </IconButton>
          </Box>
        </Container>
      </AuthGuard>
    );
  }

  if (!formation) return null;

  const sortedChapters = sortChaptersByNumber(formation.chapters);

  return (
    <AuthGuard>
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
          <IconButton onClick={() => router.push('/')} sx={{ mr: 2 }} aria-label="Retour aux formations">
            <ArrowBackIcon />
          </IconButton>
          <Box sx={{ flexGrow: 1 }}>
            <Typography variant="h4" component="h1">
              {formation.name}
            </Typography>
            <Typography variant="subtitle1" color="text.secondary">
              {sortedChapters.length} chapitres · {formatDurationDetailed(calculateFormationTotalDuration(formation))}
            </Typography>
          </Box>
        </Box>

        {progressLoading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', mb: 4 }}>
            <CircularProgress size={24} />
          </Box>
        ) : progressData ? (
          <Paper sx={{ mb: 4, p: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
              <Typography variant="body2" fontWeight="bold">
                Progression globale
              </Typography>
              <Typography variant="body2">{progressData.progress_percentage.toFixed(1)}%</Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={progressData.progress_percentage}
              sx={{ height: 10, borderRadius: 5 }}
            />
          </Paper>
        ) : null}

        <FormationAssistant formationId={formation.id} formationName={formation.name} />

        <Box sx={{ mt: 3 }}>
          {expandedChapters === null ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <CircularProgress size={24} />
            </Box>
          ) : (
          sortedChapters.map((chapter) => {
            const chapterProgress = progressData?.chapters.find((ch) => ch.name === chapter.name);
            const chapterDocs = chapterLevelDocuments(chapter.documents);
            const allDocsCount = (chapter.documents ?? []).length;

            return (
              <Accordion
                key={chapter.id}
                expanded={expandedChapters?.[chapter.id] ?? false}
                onChange={handleChapterChange(chapter.id)}
                sx={{ mb: 1 }}
              >
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Box sx={{ display: 'flex', alignItems: 'center', width: '100%', gap: 2, flexWrap: 'wrap' }}>
                    <Typography variant="h6" sx={{ color: 'text.primary', flexGrow: 1 }}>
                      {chapter.name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {formatDurationDetailed(calculateChapterTotalDuration(chapter))}
                    </Typography>
                    {allDocsCount > 0 && (
                      <Chip
                        icon={<DescriptionIcon />}
                        label={allDocsCount}
                        size="small"
                        variant="outlined"
                        sx={{ '& .MuiChip-icon': { fontSize: 16 } }}
                      />
                    )}
                    {chapterProgress && (
                      <Chip
                        label={`${chapterProgress.progress_percentage.toFixed(0)}%`}
                        color={getChipColor(chapterProgress.progress_percentage)}
                        sx={{
                          backgroundColor: getChipBackgroundColor(chapterProgress.progress_percentage),
                          borderColor: getChipBorderColor(chapterProgress.progress_percentage),
                          color: getChipTextColor(chapterProgress.progress_percentage, theme.palette.mode),
                        }}
                        size="small"
                        variant="outlined"
                      />
                    )}
                  </Box>
                </AccordionSummary>
                <AccordionDetails>
                  {chapterProgress && (
                    <Box sx={{ mb: 2 }}>
                      <LinearProgress
                        variant="determinate"
                        value={chapterProgress.progress_percentage}
                        sx={{ height: 6, borderRadius: 3 }}
                      />
                    </Box>
                  )}
                  <List disablePadding>
                    {sortVideosByNumber(chapter.videos).map((video) => {
                      const videoProgress = chapterProgress?.videos.find((v) => v.id === video.id);
                      const linkedDocs = videoDocuments(chapter.documents, video.id);
                      const docsExpanded = Boolean(expandedVideoDocs[video.id]);

                      return (
                        <Paper key={video.id} variant="outlined" sx={{ mb: 1 }}>
                          <ListItem
                            disablePadding
                            secondaryAction={
                              linkedDocs.length > 0 ? (
                                <Tooltip
                                  title={
                                    docsExpanded
                                      ? 'Masquer les documents'
                                      : `Documents (${linkedDocs.length})`
                                  }
                                >
                                  <IconButton
                                    edge="end"
                                    aria-label={
                                      docsExpanded
                                        ? 'Masquer les documents de la vidéo'
                                        : 'Afficher les documents de la vidéo'
                                    }
                                    aria-expanded={docsExpanded}
                                    onClick={(event) => {
                                      event.stopPropagation();
                                      setExpandedVideoDocs((prev) => ({
                                        ...prev,
                                        [video.id]: !prev[video.id],
                                      }));
                                    }}
                                  >
                                    {docsExpanded ? (
                                      <FolderOpenIcon color="primary" />
                                    ) : (
                                      <FolderIcon color="action" />
                                    )}
                                  </IconButton>
                                </Tooltip>
                              ) : undefined
                            }
                          >
                            <ListItemButton
                              onClick={() => handleVideoClick(video)}
                              sx={linkedDocs.length > 0 ? { pr: 7 } : undefined}
                              disabled={video.processing_status === 'processing'}
                            >
                              {video.kind === 'audio' ? (
                                <HeadphonesIcon sx={{ mr: 2, color: 'primary.main' }} />
                              ) : (
                                <PlayIcon sx={{ mr: 2, color: 'primary.main' }} />
                              )}
                              <ListItemText
                                primary={video.title}
                                secondary={
                                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5, flexWrap: 'wrap' }}>
                                    <Typography variant="caption" color="text.secondary">
                                      Durée : {formatVideoDuration(video.duration)}
                                    </Typography>
                                    {video.processing_status === 'processing' && (
                                      <Chip label="Conversion…" size="small" color="warning" variant="outlined" />
                                    )}
                                    {video.processing_status === 'failed' && (
                                      <Chip label="Échec" size="small" color="error" variant="outlined" />
                                    )}
                                    {videoProgress && (
                                      <>
                                        <Typography variant="caption" color="text.secondary">
                                          •
                                        </Typography>
                                        <Chip
                                          label={`${videoProgress.progress_percentage.toFixed(0)}%`}
                                          color={getChipColor(videoProgress.progress_percentage)}
                                          size="small"
                                          variant="outlined"
                                          sx={{
                                            height: 18,
                                            fontSize: '0.7rem',
                                            backgroundColor: getChipBackgroundColor(videoProgress.progress_percentage),
                                            borderColor: getChipBorderColor(videoProgress.progress_percentage),
                                            color: getChipTextColor(videoProgress.progress_percentage, theme.palette.mode),
                                          }}
                                        />
                                      </>
                                    )}
                                  </Box>
                                }
                              />
                            </ListItemButton>
                          </ListItem>
                          {videoProgress && (
                            <Box sx={{ px: 2, pb: 1 }}>
                              <LinearProgress
                                variant="determinate"
                                value={videoProgress.progress_percentage}
                                sx={{ height: 4, borderRadius: 2 }}
                              />
                            </Box>
                          )}
                          {linkedDocs.length > 0 && (
                            <Collapse in={docsExpanded} timeout="auto" unmountOnExit>
                              <Box sx={{ px: 1.5, pb: 1.5 }}>
                                <DocumentsPanel
                                  documents={linkedDocs}
                                  compact
                                  hideWhenEmpty
                                />
                              </Box>
                            </Collapse>
                          )}
                        </Paper>
                      );
                    })}
                  </List>

                  {chapterDocs.length > 0 && (
                    <Box sx={{ mt: 2 }}>
                      <DocumentsPanel
                        documents={chapterDocs}
                        compact
                        hideWhenEmpty
                        title="Documents du chapitre"
                      />
                    </Box>
                  )}
                </AccordionDetails>
              </Accordion>
            );
          }))}
        </Box>
      </Container>
    </AuthGuard>
  );
}
