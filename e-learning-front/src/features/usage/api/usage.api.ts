import { httpClient } from '../../../shared/api/http-client';
import type { UserTokenUsage } from '../../../types';

export const usageApi = {
  get: async (days: number): Promise<UserTokenUsage> => {
    const response = await httpClient.get<UserTokenUsage>('/usage', { params: { days } });
    return response.data;
  },
};
