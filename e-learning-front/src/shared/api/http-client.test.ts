import { http, HttpResponse } from 'msw';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { authApi } from '../../features/auth/api/auth.api';
import { usersApi } from '../../features/users/api/users.api';
import { server } from '../../test/server';
import { API_BASE_URL, setAuthErrorHandlers } from './http-client';

afterEach(() => setAuthErrorHandlers({}));

describe('httpClient auth errors', () => {
  it('signale une session expirée sur 401 hors login', async () => {
    const onUnauthorized = vi.fn();
    setAuthErrorHandlers({ onUnauthorized });
    server.use(
      http.get(`${API_BASE_URL}/auth/me`, () =>
        HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 })
      )
    );

    await expect(authApi.getMe()).rejects.toMatchObject({ response: { status: 401 } });
    expect(onUnauthorized).toHaveBeenCalledOnce();
  });

  it('distingue un refus 403 d’une expiration de session', async () => {
    const onUnauthorized = vi.fn();
    const onForbidden = vi.fn();
    setAuthErrorHandlers({ onUnauthorized, onForbidden });
    server.use(
      http.get(`${API_BASE_URL}/admin/users`, () =>
        HttpResponse.json({ detail: 'Forbidden' }, { status: 403 })
      )
    );

    await expect(usersApi.list(0, 20)).rejects.toMatchObject({
      response: { status: 403 },
    });
    expect(onForbidden).toHaveBeenCalledOnce();
    expect(onUnauthorized).not.toHaveBeenCalled();
  });
});
