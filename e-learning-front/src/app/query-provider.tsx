'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useEffect, useState } from 'react';
import { useAuthStore } from '../stores/auth.store';
import { discardProgressSaves, usePlayerStore } from '../stores/player.store';

export default function QueryProvider({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 30_000,
            retry: 1,
            refetchOnWindowFocus: false,
          },
        },
      })
  );

  // Fin de session (déconnexion, expiration, changement de compte) : rien du compte précédent ne doit survivre.
  useEffect(() => {
    let previousUserId = useAuthStore.getState().user?.id ?? null;
    return useAuthStore.subscribe((state) => {
      const userId = state.user?.id ?? null;
      if (userId === previousUserId) return;
      const sessionEnded = previousUserId !== null;
      previousUserId = userId;
      if (!sessionEnded) return;
      discardProgressSaves();
      usePlayerStore.getState().setVideo(null);
      queryClient.clear();
    });
  }, [queryClient]);

  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}
