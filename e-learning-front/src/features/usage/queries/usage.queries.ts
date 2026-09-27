'use client';

import { useQuery } from '@tanstack/react-query';
import { usageApi } from '../api/usage.api';

export const usageKeys = {
  detail: (days: number) => ['usage', days] as const,
};

export function useUsageQuery(days: number) {
  return useQuery({
    queryKey: usageKeys.detail(days),
    queryFn: () => usageApi.get(days),
    staleTime: 0,
    refetchOnWindowFocus: true,
  });
}
