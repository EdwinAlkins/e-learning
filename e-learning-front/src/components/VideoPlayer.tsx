'use client';

import { forwardRef, useImperativeHandle, useRef, useEffect, useMemo } from 'react';
import videojs from 'video.js';
import 'video.js/dist/video-js.css';
import { usePlayerStore } from '../stores/player.store';
import { API_BASE_URL } from '../services/api';

type Player = ReturnType<typeof videojs>;

export interface VideoPlayerRef {
  seekTo: (time: number) => void;
}

interface VideoPlayerProps {
  videoId: string;
}

const VideoPlayer = forwardRef<VideoPlayerRef, VideoPlayerProps>(({ videoId }, ref) => {
  const videoContainer = useRef<HTMLDivElement>(null);
  const player = useRef<Player | null>(null);
  const pendingSeekRef = useRef<number | null>(null);
  const isReadyRef = useRef(false);
  const skipNextSourceUpdate = useRef(true);
  const { setCurrentTime, setIsPlaying, updateProgress } = usePlayerStore();
  const videoUrl = `${API_BASE_URL}/videos/${videoId}/stream`;

  const options = useMemo(
    () => ({
      controls: true,
      responsive: true,
      fluid: true,
      playbackRates: [0.5, 1, 1.25, 1.5, 2],
      // Obligatoire : l'URL /stream n'a pas d'extension, video.js ne peut pas
      // déduire le type sinon → "No compatible source was found for this media."
      sources: [{ src: videoUrl, type: 'video/mp4' }],
    }),
    [videoUrl]
  );

  const flushPendingSeek = () => {
    isReadyRef.current = true;
    if (pendingSeekRef.current === null || !player.current || player.current.isDisposed()) {
      return;
    }
    const time = pendingSeekRef.current;
    pendingSeekRef.current = null;
    player.current.currentTime(time);
    setCurrentTime(time);
  };

  useImperativeHandle(ref, () => ({
    seekTo: (time: number) => {
      if (isReadyRef.current && player.current && !player.current.isDisposed()) {
        player.current.currentTime(time);
        setCurrentTime(time);
      } else {
        pendingSeekRef.current = time;
      }
    },
  }));

  // Init + dispose (une seule fois)
  useEffect(() => {
    if (!videoContainer.current || player.current) return;

    const videoElement = document.createElement('video-js');
    videoElement.classList.add('vjs-big-play-centered');
    videoContainer.current.appendChild(videoElement);

    skipNextSourceUpdate.current = true;

    player.current = videojs(videoElement, options, () => {
      const instance = player.current;
      if (!instance) return;

      instance.on('timeupdate', () => {
        const currentTime = instance.currentTime();
        if (typeof currentTime === 'number' && !Number.isNaN(currentTime)) {
          updateProgress(currentTime);
        }
      });
      instance.on('play', () => setIsPlaying(true));
      instance.on('pause', () => setIsPlaying(false));
      instance.one('loadedmetadata', flushPendingSeek);
      if (instance.readyState() >= 1) {
        flushPendingSeek();
      }
    });

    return () => {
      isReadyRef.current = false;
      pendingSeekRef.current = null;
      if (player.current && !player.current.isDisposed()) {
        player.current.dispose();
      }
      player.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- mount/dispose only
  }, []);

  // Mise à jour de source quand videoId / URL change (pas au premier mount)
  useEffect(() => {
    if (!player.current || player.current.isDisposed()) return;

    if (skipNextSourceUpdate.current) {
      skipNextSourceUpdate.current = false;
      return;
    }

    isReadyRef.current = false;
    player.current.src(options.sources);
    player.current.one('loadedmetadata', flushPendingSeek);
  }, [options, setCurrentTime]);

  return <div ref={videoContainer} style={{ width: '100%', maxWidth: '100%' }} />;
});

VideoPlayer.displayName = 'VideoPlayer';

export default VideoPlayer;
