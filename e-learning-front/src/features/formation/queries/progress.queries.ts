'use client';

import { useQuery } from '@tanstack/react-query';
import { formationApi } from '../api/formation.api';

export const formationProgressKeys = {
  all: ['formation-progress'] as const,
  detail: (formationId: string) => ['formation-progress', formationId] as const,
};

export function useAllFormationProgressQuery(enabled = true) {
  return useQuery({
    queryKey: formationProgressKeys.all,
    queryFn: formationApi.getAllProgress,
    enabled,
  });
}

export function useFormationProgressQuery(formationId: string) {
  return useQuery({
    queryKey: formationProgressKeys.detail(formationId),
    queryFn: () => formationApi.getProgress(formationId),
    enabled: Boolean(formationId),
  });
}
