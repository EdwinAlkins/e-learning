'use client';

import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query';
import type {
  AdminUser,
  CreateUserPayload,
  UpdateUserPayload,
  UserListResponse,
} from '../../../types';
import { usersApi } from '../api/users.api';

export const userKeys = {
  all: ['users'] as const,
  page: (offset: number, limit: number) => ['users', { offset, limit }] as const,
};

export function useUsersQuery(page: number, pageSize: number) {
  const offset = page * pageSize;
  return useQuery({
    queryKey: userKeys.page(offset, pageSize),
    queryFn: () => usersApi.list(offset, pageSize),
    placeholderData: keepPreviousData,
  });
}

export function useUserMutations() {
  const queryClient = useQueryClient();

  const createUser = useMutation({
    mutationFn: (payload: CreateUserPayload) => usersApi.create(payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: userKeys.all }),
  });

  const updateUser = useMutation({
    mutationFn: ({
      userId,
      payload,
    }: {
      userId: string;
      payload: UpdateUserPayload;
    }) => usersApi.update(userId, payload),
    onSuccess: (updated) => {
      queryClient.setQueriesData<UserListResponse>(
        { queryKey: userKeys.all },
        (current) =>
          current
            ? {
                ...current,
                items: current.items.map((user) =>
                  user.id === updated.id ? updated : user
                ),
              }
            : current
      );
    },
  });

  const deleteUser = useMutation({
    mutationFn: (userId: AdminUser['id']) => usersApi.delete(userId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: userKeys.all }),
  });

  return { createUser, updateUser, deleteUser };
}
