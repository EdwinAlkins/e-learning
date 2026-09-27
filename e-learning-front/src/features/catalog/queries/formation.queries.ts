'use client';

import { useQuery, useQueryClient, type QueryClient } from '@tanstack/react-query';
import type { Formation } from '../../../types';
import {
  removeFormationFromList,
  updateVideoInFormation,
  upsertFormationInList,
} from '../../../utils/studio-mutations';
import type { Video } from '../../../types';
import { catalogApi } from '../api/catalog.api';

export const formationKeys = {
  all: ['formations'] as const,
  detail: (formationId: string) => ['formation', formationId] as const,
};

export const getCachedFormation = (
  queryClient: QueryClient,
  formationId: string
): Formation | undefined =>
  queryClient.getQueryData<Formation>(formationKeys.detail(formationId)) ??
  queryClient
    .getQueryData<Formation[]>(formationKeys.all)
    ?.find((formation) => formation.id === formationId);

export const setFormationInCache = (
  queryClient: QueryClient,
  formation: Formation
): void => {
  queryClient.setQueryData(formationKeys.detail(formation.id), formation);
  queryClient.setQueryData<Formation[]>(formationKeys.all, (current) =>
    current ? upsertFormationInList(current, formation) : current
  );
};

export const updateFormationInCache = (
  queryClient: QueryClient,
  formationId: string,
  updater: (formation: Formation) => Formation
): Formation | undefined => {
  const current = getCachedFormation(queryClient, formationId);
  if (!current) return undefined;
  const updated = updater(current);
  setFormationInCache(queryClient, updated);
  return updated;
};

export const updateVideoInFormationCache = (
  queryClient: QueryClient,
  formationId: string,
  chapterId: string,
  videoId: string,
  video: Video
): Formation | undefined =>
  updateFormationInCache(queryClient, formationId, (formation) =>
    updateVideoInFormation(
      [formation],
      formationId,
      chapterId,
      videoId,
      video
    )[0]
  );

export const removeFormationFromCache = (
  queryClient: QueryClient,
  formationId: string
): void => {
  queryClient.removeQueries({ queryKey: formationKeys.detail(formationId), exact: true });
  queryClient.setQueryData<Formation[]>(formationKeys.all, (current) =>
    current ? removeFormationFromList(current, formationId) : current
  );
};

export const fetchFormationIntoCache = async (
  queryClient: QueryClient,
  formationId: string
): Promise<Formation> => {
  const formation = await queryClient.fetchQuery({
    queryKey: formationKeys.detail(formationId),
    queryFn: () => catalogApi.getFormation(formationId),
    staleTime: 0,
  });
  setFormationInCache(queryClient, formation);
  return formation;
};

export function useFormationsQuery() {
  return useQuery({
    queryKey: formationKeys.all,
    queryFn: catalogApi.getFormations,
  });
}

export function useFormationQuery(formationId: string) {
  const queryClient = useQueryClient();
  return useQuery({
    queryKey: formationKeys.detail(formationId),
    queryFn: () => catalogApi.getFormation(formationId),
    enabled: Boolean(formationId),
    initialData: () =>
      queryClient
        .getQueryData<Formation[]>(formationKeys.all)
        ?.find((formation) => formation.id === formationId),
    initialDataUpdatedAt: () =>
      queryClient.getQueryState(formationKeys.all)?.dataUpdatedAt,
  });
}
