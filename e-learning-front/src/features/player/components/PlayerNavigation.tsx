'use client';

import { Box, Button, IconButton, Typography } from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  SkipNext as SkipNextIcon,
  SkipPrevious as SkipPreviousIcon,
} from '@mui/icons-material';
import type { Formation, Video } from '../../../types';

interface PlayerNavigationProps {
  formation: Formation | null;
  video: Video;
  previousVideo: Video | null;
  nextVideo: Video | null;
  onBack: () => void;
  onNavigate: (video: Video) => void;
}

export default function PlayerNavigation({
  formation,
  video,
  previousVideo,
  nextVideo,
  onBack,
  onNavigate,
}: PlayerNavigationProps) {
  return (
    <>
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
          <IconButton onClick={onBack} sx={{ mr: 1 }} aria-label="Retour">
            <ArrowBackIcon />
          </IconButton>
          <Box sx={{ minWidth: 0 }}>
            {formation && (
              <Typography variant="caption" color="text.secondary" noWrap sx={{ display: 'block' }}>
                {formation.name}
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
            disabled={!previousVideo}
            onClick={() => previousVideo && onNavigate(previousVideo)}
            sx={{ display: { xs: 'none', sm: 'flex' } }}
          >
            Précédent
          </Button>
          <IconButton
            color="primary"
            disabled={!previousVideo}
            onClick={() => previousVideo && onNavigate(previousVideo)}
            sx={{ display: { xs: 'flex', sm: 'none' } }}
            aria-label="Vidéo précédente"
          >
            <SkipPreviousIcon />
          </IconButton>

          <Button
            variant="contained"
            endIcon={<SkipNextIcon />}
            disabled={!nextVideo}
            onClick={() => nextVideo && onNavigate(nextVideo)}
            sx={{ display: { xs: 'none', sm: 'flex' } }}
          >
            Suivant
          </Button>
          <IconButton
            color="primary"
            disabled={!nextVideo}
            onClick={() => nextVideo && onNavigate(nextVideo)}
            sx={{ display: { xs: 'flex', sm: 'none' } }}
            aria-label="Vidéo suivante"
          >
            <SkipNextIcon />
          </IconButton>
        </Box>
      </Box>

      {(previousVideo || nextVideo) && (
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            gap: 2,
            mb: 2,
            flexDirection: { xs: 'column', sm: 'row' },
          }}
        >
          {previousVideo ? (
            <Typography
              variant="caption"
              color="text.secondary"
              sx={{ cursor: 'pointer', '&:hover': { color: 'primary.main' } }}
              onClick={() => onNavigate(previousVideo)}
            >
              ← {previousVideo.title}
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
              onClick={() => onNavigate(nextVideo)}
            >
              {nextVideo.title} →
            </Typography>
          )}
        </Box>
      )}
    </>
  );
}
