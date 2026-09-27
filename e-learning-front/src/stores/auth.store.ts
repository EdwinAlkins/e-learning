import { create } from 'zustand';
import axios from 'axios';
import { authApi } from '../features/auth/api/auth.api';
import { setAuthErrorHandlers } from '../shared/api/http-client';
import type { CurrentUser } from '../types';

/** `unknown` tant que `GET /auth/me` n'a pas répondu (le cookie est illisible en JS). */
export type SessionStatus = 'unknown' | 'authenticated' | 'anonymous';

interface AuthState {
  user: CurrentUser | null;
  status: SessionStatus;
  /** Dernier 403 reçu : affiché en « accès refusé », sans déconnexion. */
  accessDenied: boolean;
  loadSession: () => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  clearSession: () => void;
  setAccessDenied: (value: boolean) => void;
}

let pendingSession: Promise<void> | null = null;

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  status: 'unknown',
  accessDenied: false,

  loadSession: () => {
    // Plusieurs composants peuvent demander la session au même moment.
    pendingSession ??= authApi
      .getMe()
      .then((user) => set({ user, status: 'authenticated' }))
      .catch((error: unknown) => {
        if (!axios.isAxiosError(error) || error.response?.status !== 401) {
          console.error('Session check failed:', error);
        }
        set({ user: null, status: 'anonymous' });
      })
      .finally(() => {
        pendingSession = null;
      });
    return pendingSession;
  },

  login: async (email, password) => {
    await authApi.login(email, password);
    const user = await authApi.getMe();
    set({ user, status: 'authenticated', accessDenied: false });
  },

  logout: async () => {
    try {
      await authApi.logout();
    } finally {
      set({ user: null, status: 'anonymous' });
    }
  },

  clearSession: () => set({ user: null, status: 'anonymous' }),

  setAccessDenied: (value) => set({ accessDenied: value }),
}));

setAuthErrorHandlers({
  onUnauthorized: () => useAuthStore.getState().clearSession(),
  onForbidden: () => useAuthStore.getState().setAccessDenied(true),
});
