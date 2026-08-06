'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  Container,
  Typography,
  Box,
  Paper,
  TextField,
  Button,
  IconButton,
  Alert,
} from '@mui/material';
import { ArrowBack as ArrowBackIcon } from '@mui/icons-material';
import AuthGuard from '../../../../components/AuthGuard';
import { useStudioStore } from '../../../../stores/studio.store';

export default function NewFormationPage() {
  const router = useRouter();
  const { createFormation } = useStudioStore();
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!name.trim()) {
      setError('Le titre est requis');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const formation = await createFormation(name.trim());
      router.push(`/studio/formation/${encodeURIComponent(formation.id)}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors de la création');
      setLoading(false);
    }
  };

  return (
    <AuthGuard>
      <Container maxWidth="sm" sx={{ py: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
          <IconButton onClick={() => router.push('/studio')} aria-label="Retour au studio">
            <ArrowBackIcon />
          </IconButton>
          <Typography variant="h5" component="h1" sx={{ ml: 1 }}>
            Nouvelle formation
          </Typography>
        </Box>

        <Paper sx={{ p: 3 }}>
          <Box component="form" onSubmit={handleSubmit}>
            <TextField
              autoFocus
              fullWidth
              label="Titre de la formation"
              value={name}
              onChange={(e) => setName(e.target.value)}
              disabled={loading}
              margin="normal"
            />

            {error && (
              <Alert severity="error" sx={{ mt: 2 }}>
                {error}
              </Alert>
            )}

            <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2, mt: 3 }}>
              <Button onClick={() => router.push('/studio')} disabled={loading}>
                Annuler
              </Button>
              <Button type="submit" variant="contained" disabled={loading}>
                Créer
              </Button>
            </Box>
          </Box>
        </Paper>
      </Container>
    </AuthGuard>
  );
}
