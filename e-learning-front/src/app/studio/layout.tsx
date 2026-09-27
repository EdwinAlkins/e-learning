'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '../../stores/auth.store';

/**
 * Garde admin sur `/studio/*` : un apprenant est renvoyé à l'accueil.
 * Confort uniquement, l'API refuse de toute façon les écritures (403).
 */
export default function StudioLayout({ children }: { readonly children: React.ReactNode }) {
  const router = useRouter();
  const user = useAuthStore((state) => state.user);
  const isAdmin = user?.is_admin === true;

  useEffect(() => {
    if (user && !user.is_admin) {
      router.replace('/');
    }
  }, [user, router]);

  return isAdmin ? children : null;
}
