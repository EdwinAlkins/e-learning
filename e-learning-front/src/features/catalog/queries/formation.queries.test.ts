import { QueryClient } from '@tanstack/react-query';
import { describe, expect, it } from 'vitest';
import type { Formation } from '../../../types';
import {
  formationKeys,
  removeFormationFromCache,
  setFormationInCache,
  updateFormationInCache,
  updateVideoInFormationCache,
} from './formation.queries';

const formation: Formation = {
  id: 'formation-1',
  name: 'Architecture',
  chapters: [],
};

describe('formation query cache', () => {
  it('maintient la liste et le détail sur la même version', () => {
    const queryClient = new QueryClient();
    queryClient.setQueryData(formationKeys.all, [formation]);
    queryClient.setQueryData(formationKeys.detail(formation.id), formation);

    updateFormationInCache(queryClient, formation.id, (current) => ({
      ...current,
      name: 'Architecture hexagonale',
    }));

    expect(queryClient.getQueryData<Formation[]>(formationKeys.all)?.[0].name).toBe(
      'Architecture hexagonale'
    );
    expect(queryClient.getQueryData<Formation>(formationKeys.detail(formation.id))?.name).toBe(
      'Architecture hexagonale'
    );
  });

  it('ne transforme pas un détail isolé en catalogue incomplet', () => {
    const queryClient = new QueryClient();

    setFormationInCache(queryClient, formation);

    expect(queryClient.getQueryData(formationKeys.all)).toBeUndefined();
    expect(queryClient.getQueryData(formationKeys.detail(formation.id))).toEqual(formation);
  });

  it('supprime la formation de toutes les entrées existantes', () => {
    const queryClient = new QueryClient();
    queryClient.setQueryData(formationKeys.all, [formation]);
    queryClient.setQueryData(formationKeys.detail(formation.id), formation);

    removeFormationFromCache(queryClient, formation.id);

    expect(queryClient.getQueryData(formationKeys.all)).toEqual([]);
    expect(queryClient.getQueryData(formationKeys.detail(formation.id))).toBeUndefined();
  });

  it('propage une vidéo mise à jour dans la liste et le détail', () => {
    const queryClient = new QueryClient();
    const withVideo: Formation = {
      ...formation,
      chapters: [
        {
          id: 'chapter-1',
          name: 'Fondations',
          videos: [{ id: 'video-1', title: 'Introduction', duration: 60 }],
        },
      ],
    };
    queryClient.setQueryData(formationKeys.all, [withVideo]);
    queryClient.setQueryData(formationKeys.detail(formation.id), withVideo);

    updateVideoInFormationCache(
      queryClient,
      formation.id,
      'chapter-1',
      'video-1',
      {
        id: 'video-1',
        title: 'Introduction',
        duration: 60,
        transcription_status: 'processing',
      }
    );

    const listVideo = queryClient.getQueryData<Formation[]>(formationKeys.all)?.[0]
      .chapters[0].videos[0];
    const detailVideo = queryClient.getQueryData<Formation>(
      formationKeys.detail(formation.id)
    )?.chapters[0].videos[0];
    expect(listVideo?.transcription_status).toBe('processing');
    expect(detailVideo?.transcription_status).toBe('processing');
  });
});
