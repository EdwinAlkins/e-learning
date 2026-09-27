import { act, render } from '@testing-library/react';
import { useQueryClient, type QueryClient } from '@tanstack/react-query';
import { beforeEach, describe, expect, it } from 'vitest';
import { useAuthStore } from '../stores/auth.store';
import QueryProvider from './query-provider';

const user = (id: string) => ({ id, email: `${id}@test.fr`, full_name: null, is_admin: false });

function renderProvider(): QueryClient {
  let client: QueryClient | undefined;
  function Capture() {
    client = useQueryClient();
    return null;
  }
  render(
    <QueryProvider>
      <Capture />
    </QueryProvider>
  );
  return client!;
}

describe('QueryProvider session cleanup', () => {
  beforeEach(() => {
    useAuthStore.setState({ user: null, status: 'unknown' });
  });

  it('keeps the cache when a session starts', () => {
    const client = renderProvider();
    client.setQueryData(['formations'], ['kept']);

    act(() => useAuthStore.setState({ user: user('a'), status: 'authenticated' }));

    expect(client.getQueryData(['formations'])).toEqual(['kept']);
  });

  it('clears the cache when the session ends', () => {
    useAuthStore.setState({ user: user('a'), status: 'authenticated' });
    const client = renderProvider();
    client.setQueryData(['formation-progress'], { f1: 42 });

    act(() => useAuthStore.getState().clearSession());

    expect(client.getQueryData(['formation-progress'])).toBeUndefined();
  });

  it('clears the cache when another account takes over', () => {
    useAuthStore.setState({ user: user('a'), status: 'authenticated' });
    const client = renderProvider();
    client.setQueryData(['usage', 30], { total: 10 });

    act(() => useAuthStore.setState({ user: user('b') }));

    expect(client.getQueryData(['usage', 30])).toBeUndefined();
  });
});
