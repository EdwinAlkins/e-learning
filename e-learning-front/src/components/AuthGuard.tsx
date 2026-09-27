'use client';

import { Box } from '@mui/material';
import { useAuthStore } from '../stores/auth.store';
import Header from './Header';

interface AuthGuardProps {
  readonly children: React.ReactNode;
}

/** Cadre des pages connectées. La redirection vers `/auth` est faite par `SessionGate`. */
export default function AuthGuard({ children }: AuthGuardProps) {
  const status = useAuthStore((state) => state.status);

  if (status !== 'authenticated') {
    return null;
  }

  return (
    <Box>
      <Header />
      {children}
    </Box>
  );
}
