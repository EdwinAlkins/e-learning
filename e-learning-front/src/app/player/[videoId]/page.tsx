'use client';

import { useEffect, useMemo, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  Container,
  Box,
  CircularProgress,
  Alert,
} from '@mui/material';
import type { VideoPlayerRef } from '../../../components/VideoPlayer';
import { usePlayerStore } from '../../../stores/player.store';
import PlayerMediaPanel, {
  PlayerJobNotices,
} from '../../../features/player/components/PlayerMediaPanel';
import PlayerNavigation from '../../../features/player/components/PlayerNavigation';
import PlayerTabs from '../../../features/player/components/PlayerTabs';
import VideoSummaryPanel from '../../../features/player/components/VideoSummaryPanel';
import { usePlayerCatalog } from '../../../features/player/hooks/usePlayerCatalog';
import { usePlayerJobs } from '../../../features/player/hooks/usePlayerJobs';
import { useVideoSummary } from '../../../features/player/hooks/useVideoSummary';
import {
  useChapterDocumentsQuery,
  useVideoProgressQuery,
} from '../../../features/player/queries/player.queries';
import type { Video } from '../../../types';
import AuthGuard from '../../../components/AuthGuard';
import { useAuthStore } from '../../../stores/auth.store';

interface PlayerSessionProps {
  videoId: string;
}

function PlayerSession({ videoId }: PlayerSessionProps) {
  // Jobs IA et édition du résumé : routes admin côté API (403 pour un apprenant).
  const isAdmin = useAuthStore((state) => state.user?.is_admin === true);
  const router = useRouter();
  const videoPlayerRef = useRef<VideoPlayerRef>(null);

  const { setVideo: setPlayerVideo, setCurrentTime } = usePlayerStore();
  const {
    video,
    parentFormation,
    chapterId,
    catalogDocuments,
    prevVideo,
    nextVideo,
    loading,
    error,
  } = usePlayerCatalog(videoId);
  const documentsQuery = useChapterDocumentsQuery(
    chapterId ?? '',
    catalogDocuments === undefined
  );
  const progressQuery = useVideoProgressQuery(videoId);
  const summaryController = useVideoSummary(videoId, video?.summary_status);
  const jobs = usePlayerJobs({
    formationId: parentFormation?.id ?? null,
    chapterId,
    videoId,
  });
  const {
    summary,
    summaryLoading,
    summaryError,
    showSummary,
    isEditingSummary,
    editSummaryContent,
    setEditSummaryContent,
    savingSummary,
  } = summaryController;
  const aiJobBusy = jobs.busy;
  const documentsLoading = documentsQuery.isLoading;
  const documentsError =
    documentsQuery.error instanceof Error ? documentsQuery.error.message : null;

  const transcriptionStatus = video?.transcription_status;
  const summaryStatus = video?.summary_status;

  const statusAiError =
    transcriptionStatus === 'failed'
      ? 'Échec de la transcription'
      : summaryStatus === 'failed'
        ? 'Échec de la génération du résumé (vérifiez la connexion API LLM)'
        : null;
  const displayedAiError = statusAiError ?? jobs.error;

  useEffect(() => {
    if (videoId) setPlayerVideo(videoId);
  }, [videoId, setPlayerVideo]);

  const visibleDocuments = useMemo(() => {
    const docs = catalogDocuments ?? documentsQuery.data ?? [];
    return docs.filter((doc) => doc.video_id === videoId);
  }, [catalogDocuments, documentsQuery.data, videoId]);

  useEffect(() => {
    const lastPosition = progressQuery.data;
    if (lastPosition === null || lastPosition === undefined) return;
    // seekTo file la position jusqu'à loadedmetadata (VideoPlayer / AudioPlayer)
    videoPlayerRef.current?.seekTo(lastPosition);
    setCurrentTime(lastPosition);
  }, [progressQuery.data, setCurrentTime]);

  const handleSeekTo = (time: number) => {
    videoPlayerRef.current?.seekTo(time);
  };

  const handleGetSummary = async () => {
    await summaryController.toggleSummary();
  };

  const handleEditSummary = () => {
    summaryController.startEditing();
  };

  const handleSaveSummary = async () => {
    try {
      await summaryController.saveSummary();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Échec de la mise à jour du résumé';
      alert(errorMessage);
    }
  };

  const handleCancelEditSummary = () => {
    summaryController.cancelEditing();
  };

  const handleStartTranscription = async () => {
    if (!videoId) return;
    try {
      await jobs.startTranscription();
    } catch {
      // L'erreur de mutation est exposée par le hook.
    }
  };

  const handleGenerateSummary = async () => {
    if (!videoId) return;
    try {
      await jobs.generateSummary();
      summaryController.openSummary();
    } catch {
      // L'erreur de mutation est exposée par le hook.
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

  if (loading) {
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

  return (
    <AuthGuard>
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <PlayerNavigation
          formation={parentFormation}
          video={video}
          previousVideo={prevVideo}
          nextVideo={nextVideo}
          onBack={handleGoBack}
          onNavigate={navigateToVideo}
        />

        <PlayerMediaPanel
          videoId={videoId}
          video={video}
          playerRef={videoPlayerRef}
          isAdmin={isAdmin}
          jobBusy={aiJobBusy}
          summaryLoading={summaryLoading}
          onStartTranscription={() => void handleStartTranscription()}
          onGenerateSummary={() => void handleGenerateSummary()}
          onToggleSummary={() => void handleGetSummary()}
        />
        <PlayerJobNotices video={video} isAdmin={isAdmin} error={displayedAiError} />
        <VideoSummaryPanel
          summary={summary}
          loading={summaryLoading}
          error={summaryError}
          visible={showSummary}
          editing={isEditingSummary}
          draft={editSummaryContent}
          saving={savingSummary}
          canEdit={isAdmin}
          onDraftChange={setEditSummaryContent}
          onEdit={handleEditSummary}
          onSave={() => void handleSaveSummary()}
          onCancel={handleCancelEditSummary}
        />

        <PlayerTabs
          videoId={videoId}
          documents={visibleDocuments}
          documentsLoading={documentsLoading}
          documentsError={documentsError}
          onSeekTo={handleSeekTo}
        />
      </Container>
    </AuthGuard>
  );
}

export default function Player() {
  const params = useParams();
  const videoId = params.videoId as string;

  return <PlayerSession key={videoId} videoId={videoId} />;
}
