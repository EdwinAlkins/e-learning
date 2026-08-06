'use client';

import { useEffect, useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
} from '@mui/material';

interface ChapterDialogProps {
  open: boolean;
  mode: 'create' | 'edit';
  initialName?: string;
  onClose: () => void;
  onSubmit: (name: string) => Promise<void>;
}

export default function ChapterDialog({
  open,
  mode,
  initialName = '',
  onClose,
  onSubmit,
}: ChapterDialogProps) {
  const [name, setName] = useState(initialName);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setName(initialName);
      setError(null);
    }
  }, [open, initialName]);

  const handleSubmit = async () => {
    if (!name.trim()) {
      setError('Le nom du chapitre est requis');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      await onSubmit(name.trim());
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors de la sauvegarde');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onClose={loading ? undefined : onClose} maxWidth="sm" fullWidth>
      <DialogTitle>{mode === 'create' ? 'Ajouter un chapitre' : 'Modifier le chapitre'}</DialogTitle>
      <DialogContent>
        <TextField
          autoFocus
          fullWidth
          label="Nom du chapitre"
          value={name}
          onChange={(e) => setName(e.target.value)}
          margin="normal"
          error={Boolean(error)}
          helperText={error ?? 'Le numéro (ex. « 1. ») sera ajouté automatiquement à la création si absent'}
          disabled={loading}
          onKeyDown={(e) => {
            if (e.key === 'Enter') handleSubmit();
          }}
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={loading}>
          Annuler
        </Button>
        <Button onClick={handleSubmit} variant="contained" disabled={loading}>
          {mode === 'create' ? 'Ajouter' : 'Enregistrer'}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
