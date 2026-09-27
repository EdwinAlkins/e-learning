import { create } from 'zustand';
import { playerApi } from '../features/player/api/player.api';
import { PROGRESS_SAVE_INTERVAL_MS } from '../constants';

interface PlayerState {
  currentVideoId: string | null;
  currentTime: number;
  isPlaying: boolean;
  setVideo: (videoId: string | null) => void;
  setCurrentTime: (time: number) => void;
  setIsPlaying: (playing: boolean) => void;
  updateProgress: (time: number) => void;
}

/** Positions en attente, par videoId pour ne jamais enregistrer sur la mauvaise vidéo. */
const pendingSaves = new Map<string, { position: number; timer: ReturnType<typeof setTimeout> }>();
const inFlightSaves = new Set<Promise<void>>();

const sendProgress = (videoId: string, position: number) => {
  const request = playerApi.saveProgress(videoId, position).catch((error) => {
    console.error('Failed to save progress:', error);
  });
  inFlightSaves.add(request);
  void request.finally(() => inFlightSaves.delete(request));
};

// Throttle et non debounce : timeupdate tire toutes les ~250 ms, un debounce ne partirait qu'à la pause.
const scheduleProgressSave = (videoId: string, position: number) => {
  const pending = pendingSaves.get(videoId);
  if (pending) {
    pending.position = position;
    return;
  }
  const timer = setTimeout(() => {
    const latest = pendingSaves.get(videoId);
    pendingSaves.delete(videoId);
    if (latest) sendProgress(videoId, latest.position);
  }, PROGRESS_SAVE_INTERVAL_MS);
  pendingSaves.set(videoId, { position, timer });
};

/** Envoie immédiatement les positions en attente et attend la fin des sauvegardes en cours. */
export const flushProgressSaves = async (): Promise<void> => {
  for (const [videoId, { position, timer }] of pendingSaves) {
    clearTimeout(timer);
    sendProgress(videoId, position);
  }
  pendingSaves.clear();
  await Promise.all(inFlightSaves);
};

/** Abandonne les positions en attente : sans session valide, elles partiraient sous le mauvais compte. */
export const discardProgressSaves = (): void => {
  for (const { timer } of pendingSaves.values()) clearTimeout(timer);
  pendingSaves.clear();
};

export const usePlayerStore = create<PlayerState>((set, get) => ({
  currentVideoId: null,
  currentTime: 0,
  isPlaying: false,
  setVideo: (videoId: string | null) => {
    set({ currentVideoId: videoId, currentTime: 0, isPlaying: false });
  },
  setCurrentTime: (time: number) => {
    set({ currentTime: time });
  },
  setIsPlaying: (playing: boolean) => {
    set({ isPlaying: playing });
  },
  updateProgress: (time: number) => {
    const { currentVideoId } = get();
    set({ currentTime: time });
    if (currentVideoId) {
      scheduleProgressSave(currentVideoId, time);
    }
  },
}));
