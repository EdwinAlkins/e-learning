import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { playerApi } from '../features/player/api/player.api';
import { PROGRESS_SAVE_INTERVAL_MS } from '../constants';
import { flushProgressSaves, usePlayerStore } from './player.store';

describe('player store progress saves', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.spyOn(playerApi, 'saveProgress').mockResolvedValue(undefined);
    usePlayerStore.getState().setVideo('video-1');
  });

  afterEach(async () => {
    await flushProgressSaves();
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  it('saves during continuous playback instead of waiting for a pause', () => {
    const { updateProgress } = usePlayerStore.getState();
    for (let t = 0; t <= 6; t += 0.25) {
      updateProgress(t);
      vi.advanceTimersByTime(250);
    }

    expect(playerApi.saveProgress).toHaveBeenCalledTimes(1);
    expect(playerApi.saveProgress).toHaveBeenCalledWith('video-1', expect.any(Number));
  });

  it('sends the latest pending position immediately on flush', async () => {
    usePlayerStore.getState().updateProgress(12);
    usePlayerStore.getState().updateProgress(13);

    await flushProgressSaves();

    expect(playerApi.saveProgress).toHaveBeenCalledOnce();
    expect(playerApi.saveProgress).toHaveBeenCalledWith('video-1', 13);

    vi.advanceTimersByTime(PROGRESS_SAVE_INTERVAL_MS);
    expect(playerApi.saveProgress).toHaveBeenCalledOnce();
  });
});
