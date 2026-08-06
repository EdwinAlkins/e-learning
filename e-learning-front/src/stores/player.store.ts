import { create } from 'zustand';
import { debounce } from '../utils/debounce';
import { apiService } from '../services/api';
import { PROGRESS_SAVE_DEBOUNCE_MS } from '../constants';

interface PlayerState {
  currentVideoId: string | null;
  currentTime: number;
  isPlaying: boolean;
  setVideo: (videoId: string | null) => void;
  setCurrentTime: (time: number) => void;
  setIsPlaying: (playing: boolean) => void;
  updateProgress: (time: number) => void;
}

type DebouncedSave = (videoId: string, position: number) => void;

/** Un debounce par videoId pour éviter d'enregistrer la progression sur la mauvaise vidéo. */
const debouncedSaveByVideoId = new Map<string, DebouncedSave>();

const getDebouncedSave = (videoId: string): DebouncedSave => {
  let fn = debouncedSaveByVideoId.get(videoId);
  if (!fn) {
    fn = debounce((id: string, position: number) => {
      apiService.saveProgress(id, position).catch((error) => {
        console.error('Failed to save progress:', error);
      });
    }, PROGRESS_SAVE_DEBOUNCE_MS);
    debouncedSaveByVideoId.set(videoId, fn);
  }
  return fn;
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
      getDebouncedSave(currentVideoId)(currentVideoId, time);
    }
  },
}));