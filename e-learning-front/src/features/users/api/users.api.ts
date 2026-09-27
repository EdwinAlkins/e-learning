import type {
  AdminUser,
  CreateUserPayload,
  UpdateUserPayload,
  UserListResponse,
} from '../../../types';
import { httpClient } from '../../../shared/api/http-client';

export const usersApi = {
  list: async (offset: number, limit: number): Promise<UserListResponse> => {
    const response = await httpClient.get<UserListResponse>('/admin/users', {
      params: { offset, limit },
    });
    return response.data;
  },

  create: async (payload: CreateUserPayload): Promise<AdminUser> => {
    const response = await httpClient.post<AdminUser>('/admin/users', payload);
    return response.data;
  },

  update: async (userId: string, payload: UpdateUserPayload): Promise<AdminUser> => {
    const response = await httpClient.patch<AdminUser>(`/admin/users/${userId}`, payload);
    return response.data;
  },

  delete: async (userId: string): Promise<void> => {
    await httpClient.delete(`/admin/users/${userId}`);
  },
};
