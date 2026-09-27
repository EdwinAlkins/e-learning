import type { CurrentUser } from '../../../types';
import { httpClient } from '../../../shared/api/http-client';

export const authApi = {
  login: async (email: string, password: string): Promise<void> => {
    await httpClient.post(
      '/auth/login',
      new URLSearchParams({ username: email, password }),
      { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
    );
  },

  logout: async (): Promise<void> => {
    await httpClient.post('/auth/logout');
  },

  getMe: async (): Promise<CurrentUser> => {
    const response = await httpClient.get<CurrentUser>('/auth/me');
    return response.data;
  },

  changePassword: async (currentPassword: string, newPassword: string): Promise<void> => {
    await httpClient.patch('/auth/me/password', {
      current_password: currentPassword,
      new_password: newPassword,
    });
  },
};
