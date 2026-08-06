'use client';

import { forwardRef, useEffect, useImperativeHandle, useRef } from 'react';
import { Box, Paper, Typography } from '@mui/material';
import { usePlayerStore } from '../stores/player.store';
import { API_BASE_URL } from '../services/api';
import type { VideoPlayerRef } from './VideoPlayer';

interface AudioPlayerProps {
  videoId: string;
}

const AudioPlayer = forwardRef<VideoPlayerRef, AudioPlayerProps>(({ videoId }, ref) => {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const pendingSeekRef = useRef<number | null>(null);
  const { setCurrentTime, setIsPlaying, updateProgress } = usePlayerStore();
  // URL dérivée de videoId ; la clé force le remount du <audio> à chaque média
  const audioUrl = `${API_BASE_URL}/videos/${videoId}/stream`;

  useImperativeHandle(ref, () => ({
    seekTo: (time: number) => {
      const el = audioRef.current;
      if (el && el.readyState >= 1) {
        el.currentTime = time;
        setCurrentTime(time);
      } else {
        pendingSeekRef.current = time;
      }
    },
  }));

  useEffect(() => {
    const el = audioRef.current;
    if (!el) return;

    pendingSeekRef.current = null;

    const onTimeUpdate = () => updateProgress(el.currentTime);
    const onPlay = () => setIsPlaying(true);
    const onPause = () => setIsPlaying(false);
    const onLoadedMetadata = () => {
      if (pendingSeekRef.current !== null) {
        el.currentTime = pendingSeekRef.current;
        setCurrentTime(pendingSeekRef.current);
        pendingSeekRef.current = null;
      }
    };

    el.addEventListener('timeupdate', onTimeUpdate);
    el.addEventListener('play', onPlay);
    el.addEventListener('pause', onPause);
    el.addEventListener('loadedmetadata', onLoadedMetadata);
    return () => {
      el.removeEventListener('timeupdate', onTimeUpdate);
      el.removeEventListener('play', onPlay);
      el.removeEventListener('pause', onPause);
      el.removeEventListener('loadedmetadata', onLoadedMetadata);
    };
  }, [setIsPlaying, updateProgress, setCurrentTime, videoId]);

  return (
    <Paper
      variant="outlined"
      sx={{
        p: 3,
        display: 'flex',
        flexDirection: 'column',
        gap: 2,
        bgcolor: 'background.default',
      }}
    >
      <Typography variant="subtitle1" color="text.secondary">
        Lecteur audio
      </Typography>
      <Box
        component="audio"
        key={videoId}
        ref={audioRef}
        src={audioUrl}
        controls
        preload="metadata"
        sx={{ width: '100%' }}
      />
    </Paper>
  );
});

AudioPlayer.displayName = 'AudioPlayer';

export default AudioPlayer;
