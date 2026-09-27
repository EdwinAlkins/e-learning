import axios from 'axios';
import type {
  AskFormationResponse,
  FormationProgress,
  FormationsProgressResponse,
} from '../../../types';
import { httpClient } from '../../../shared/api/http-client';

export const formationApi = {
  ask: async (formationId: string, question: string): Promise<AskFormationResponse> => {
    try {
      const response = await httpClient.post<AskFormationResponse>(
        `/formations/${encodeURIComponent(formationId)}/ask`,
        { question }
      );
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const detail = error.response?.data?.detail;
        if (typeof detail === 'string') throw new Error(detail);
      }
      throw error;
    }
  },

  index: async (formationId: string): Promise<void> => {
    await httpClient.post(`/formations/${encodeURIComponent(formationId)}/index`);
  },

  getProgress: async (formationId: string): Promise<FormationProgress> => {
    const response = await httpClient.get<FormationProgress>(
      `/progress/formation/${encodeURIComponent(formationId)}`
    );
    return response.data;
  },

  getAllProgress: async (): Promise<Record<string, FormationProgress>> => {
    const response = await httpClient.get<FormationsProgressResponse>('/progress/formations');
    return response.data.progress ?? {};
  },
};
