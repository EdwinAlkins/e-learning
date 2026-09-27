import type { ReactNode } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act, renderHook } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { Chapter, Formation } from '../../../types';
import { formationKeys } from '../../../features/catalog/queries/formation.queries';
import { studioApi } from '../../../features/studio/api/studio.api';
import { useFormationBuilder } from './useFormationBuilder';

vi.mock('../../../features/studio/api/studio.api', () => ({
  studioApi: {
    reorderVideos: vi.fn(),
  },
}));

const chapter: Chapter = {
  id: 'chapter-1',
  name: 'Fondations',
  position: 0,
  videos: [
    { id: 'video-1', title: 'Introduction', duration: 60, position: 1 },
    { id: 'video-2', title: 'Composants', duration: 120, position: 2 },
  ],
};

const formation: Formation = {
  id: 'formation-1',
  name: 'Architecture',
  chapters: [chapter],
};

describe('useFormationBuilder', () => {
  it('marque comme occupée la vidéo réellement déplacée vers le haut', async () => {
    let resolveReorder!: (value: Chapter) => void;
    const reorderVideos = vi.mocked(studioApi.reorderVideos);
    reorderVideos.mockImplementation(
      () =>
        new Promise<Chapter>((resolve) => {
          resolveReorder = resolve;
        })
    );
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false, staleTime: Infinity } },
    });
    queryClient.setQueryData(formationKeys.all, [formation]);
    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );

    const { result } = renderHook(() => useFormationBuilder(formation.id), { wrapper });

    let movePromise!: Promise<void>;
    act(() => {
      movePromise = result.current.handleMoveUp(chapter, chapter.videos[1]);
    });

    expect(result.current.busyVideoId).toBe('video-2');
    expect(reorderVideos).toHaveBeenCalledWith(
      chapter.id,
      ['video-2', 'video-1']
    );

    await act(async () => {
      resolveReorder({ ...chapter, videos: [...chapter.videos].reverse() });
      await movePromise;
    });

    expect(result.current.busyVideoId).toBeNull();
  });
});
