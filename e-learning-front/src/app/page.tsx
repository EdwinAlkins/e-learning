'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  Container,
  Typography,
  Box,
  Paper,
  CircularProgress,
  Alert,
  Card,
  CardContent,
  CardActionArea,
  LinearProgress,
} from '@mui/material';
import { useCatalogStore } from '../stores/catalog.store';
import { apiService } from '../services/api';
import type { FormationProgress } from '../types';
import AuthGuard from '../components/AuthGuard';
import {
  calculateFormationTotalDuration,
  formatDurationCompact,
} from '../utils/formation';

export default function Dashboard() {
  const { formations, loading, error, fetchFormations } = useCatalogStore();
  const router = useRouter();
  const [progressData, setProgressData] = useState<Record<string, FormationProgress>>({});
  const [progressLoading, setProgressLoading] = useState<Record<string, boolean>>({});

  const formationIdsKey = useMemo(
    () =>
      (Array.isArray(formations) ? formations : [])
        .map((f) => f.id)
        .sort()
        .join(','),
    [formations]
  );

  useEffect(() => {
    void fetchFormations();
  }, [fetchFormations]);

  useEffect(() => {
    if (!formationIdsKey) return;

    const formationIds = formationIdsKey.split(',');
    let cancelled = false;

    const loadProgress = async () => {
      setProgressLoading(Object.fromEntries(formationIds.map((id) => [id, true])));

      try {
        const progressById = await apiService.getFormationsProgress();
        if (cancelled) return;
        setProgressData(progressById);
      } catch (err) {
        console.error('Failed to load formations progress', err);
        if (!cancelled) setProgressData({});
      } finally {
        if (!cancelled) {
          setProgressLoading(Object.fromEntries(formationIds.map((id) => [id, false])));
        }
      }
    };

    void loadProgress();
    return () => {
      cancelled = true;
    };
  }, [formationIdsKey]);

  const handleFormationClick = (formationId: string) => {
    router.push(`/formation/${encodeURIComponent(formationId)}`);
  };

  const safeFormations = Array.isArray(formations) ? formations : [];

  return (
    <AuthGuard>
      {loading ? (
        <Container maxWidth="lg" sx={{ py: 4 }}>
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
            <CircularProgress />
          </Box>
        </Container>
      ) : error ? (
        <Container maxWidth="lg" sx={{ py: 4 }}>
          <Alert severity="error">{error}</Alert>
        </Container>
      ) : safeFormations.length === 0 ? (
        <Container maxWidth="lg" sx={{ py: 4 }}>
          <Typography variant="h4" component="h1" gutterBottom>
            Mes formations
          </Typography>
          <Paper sx={{ p: 4, textAlign: 'center' }}>
            <Typography color="text.secondary">Aucune formation disponible.</Typography>
          </Paper>
        </Container>
      ) : (
        <Container maxWidth="lg" sx={{ py: 4 }}>
          <Typography variant="h4" component="h1" gutterBottom>
            Mes formations
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
            {safeFormations.length} formation{safeFormations.length > 1 ? 's' : ''} disponible
            {safeFormations.length > 1 ? 's' : ''}
          </Typography>

          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', md: '1fr 1fr 1fr' },
              gap: 3,
            }}
          >
            {safeFormations.map((formation) => {
              const formationProgress = progressData[formation.id];
              const isLoadingProgress = progressLoading[formation.id];
              const totalDurationSeconds = calculateFormationTotalDuration(formation);
              const progressPercentage = formationProgress?.progress_percentage ?? 0;
              const doneDurationSeconds = totalDurationSeconds * (progressPercentage / 100);
              const chapterCount = formation.chapters.length;
              const videoCount = formation.chapters.reduce(
                (total, chapter) => total + chapter.videos.length,
                0
              );

              return (
                <Card
                  key={formation.id}
                  sx={{
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                    transition: 'transform 0.2s, box-shadow 0.2s',
                    '@media (prefers-reduced-motion: reduce)': {
                      transition: 'none',
                      '&:hover': { transform: 'none' },
                    },
                    '&:hover': {
                      transform: 'translateY(-2px)',
                      boxShadow: 4,
                    },
                  }}
                >
                  <CardActionArea
                    onClick={() => handleFormationClick(formation.id)}
                    sx={{
                      flexGrow: 1,
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'stretch',
                      justifyContent: 'flex-start',
                      p: 0,
                    }}
                  >
                    <CardContent sx={{ flexGrow: 1, width: '100%' }}>
                      <Typography
                        variant="h6"
                        component="h2"
                        gutterBottom
                        noWrap
                        title={formation.name}
                      >
                        {formation.name}
                      </Typography>

                      <Box sx={{ mt: 2, display: 'flex', flexDirection: 'column', gap: 1 }}>
                        <Typography variant="body2" color="text.secondary">
                          {chapterCount} chapitre{chapterCount > 1 ? 's' : ''} · {videoCount} vidéo
                          {videoCount > 1 ? 's' : ''}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Durée totale : {formatDurationCompact(totalDurationSeconds)}
                        </Typography>

                        <Box sx={{ mt: 1 }}>
                          {isLoadingProgress ? (
                            <CircularProgress size={20} />
                          ) : (
                            <>
                              <Box
                                sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}
                              >
                                <Typography variant="body2" color="text.primary" fontWeight="bold">
                                  {formatDurationCompact(doneDurationSeconds)} complétées
                                </Typography>
                                <Typography variant="body2" color="text.secondary">
                                  {progressPercentage.toFixed(0)}%
                                </Typography>
                              </Box>
                              <LinearProgress
                                variant="determinate"
                                value={progressPercentage}
                                sx={{ height: 8, borderRadius: 4 }}
                              />
                            </>
                          )}
                        </Box>
                      </Box>
                    </CardContent>
                  </CardActionArea>
                </Card>
              );
            })}
          </Box>
        </Container>
      )}
    </AuthGuard>
  );
}
