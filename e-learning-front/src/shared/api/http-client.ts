import axios from 'axios';
import type { AxiosInstance } from 'axios';

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface AuthErrorHandlers {
  /** 401 : pas de session ou session expirée → retour à la connexion. */
  onUnauthorized?: () => void;
  /** 403 : session valide, droits insuffisants → refus sans déconnexion. */
  onForbidden?: () => void;
}

let authErrorHandlers: AuthErrorHandlers = {};

/** Branché par le store d'auth sans créer de dépendance client HTTP → store. */
export function setAuthErrorHandlers(handlers: AuthErrorHandlers): void {
  authErrorHandlers = handlers;
}

export const httpClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
    'X-Requested-With': 'XMLHttpRequest',
  },
});

httpClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status;
    const url: string = error.config?.url ?? '';

    if (status === 401 && url !== '/auth/login') {
      authErrorHandlers.onUnauthorized?.();
    } else if (status === 403) {
      authErrorHandlers.onForbidden?.();
    }

    return Promise.reject(error);
  }
);
