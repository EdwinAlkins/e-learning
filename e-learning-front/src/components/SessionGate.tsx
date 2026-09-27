'use client';

import { useEffect } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { Alert, Box, CircularProgress, Snackbar } from '@mui/material';
import { useAuthStore } from '../stores/auth.store';
import { SNACKBAR_DURATION_MS } from '../constants';

const PUBLIC_PATHS = new Set(['/auth']);

interface SessionGateProps {
  readonly children: React.ReactNode;
}

/**
 * Garde globale (layout racine) : toute page hors `/auth` exige une session.
 * Confort d'affichage uniquement, la sécurité réelle est côté API (401/403).
 */
export default function SessionGate({ children }: SessionGateProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { status, loadSession, accessDenied, setAccessDenied } = useAuthStore();
  const isPublic = PUBLIC_PATHS.has(pathname);

  useEffect(() => {
    if (status === 'unknown') {
      void loadSession();
    }
  }, [status, loadSession]);

  useEffect(() => {
    if (status === 'anonymous' && !isPublic) {
      router.replace(`/auth?next=${encodeURIComponent(pathname)}`);
    }
  }, [status, isPublic, pathname, router]);

  if (!isPublic && status !== 'authenticated') {
    return (
      <Box sx={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <>
      {children}
      <Snackbar
        open={accessDenied}
        autoHideDuration={SNACKBAR_DURATION_MS}
        onClose={() => setAccessDenied(false)}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        <Alert onClose={() => setAccessDenied(false)} severity="warning" sx={{ width: '100%' }}>
          Accès refusé : cette action est réservée aux administrateurs.
        </Alert>
      </Snackbar>
    </>
  );
}
