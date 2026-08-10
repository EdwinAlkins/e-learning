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

export type ChapterSubmitData = {
  name: string;
  /** Position 1-based dans la formation (édition uniquement). */
  order?: number;
};

interface ChapterDialogProps {
  open: boolean;
  mode: 'create' | 'edit';
  initialName?: string;
  /** Position courante 1-based (édition). */
  initialOrder?: number;
  /** Nombre de chapitres de la formation (édition). */
  chapterCount?: number;
  onClose: () => void;
  onSubmit: (data: ChapterSubmitData) => Promise<void>;
}

export default function ChapterDialog({
  open,
  mode,
  initialName = '',
  initialOrder,
  chapterCount,
  onClose,
  onSubmit,
}: ChapterDialogProps) {
  const [name, setName] = useState(initialName);
  const [order, setOrder] = useState(String(initialOrder ?? 1));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const showOrderField = mode === 'edit' && chapterCount != null && chapterCount > 0;

  useEffect(() => {
    if (open) {
      setName(initialName);
      setOrder(String(initialOrder ?? 1));
      setError(null);
    }
  }, [open, initialName, initialOrder]);

  const handleSubmit = async () => {
    if (!name.trim()) {
      setError('Le nom du chapitre est requis');
      return;
    }

    let parsedOrder: number | undefined;
    if (showOrderField) {
      const n = Number.parseInt(order, 10);
      if (!Number.isFinite(n) || n < 1 || n > (chapterCount ?? 1)) {
        setError(`L'ordre doit être un entier entre 1 et ${chapterCount}`);
        return;
      }
      parsedOrder = n;
    }

    setLoading(true);
    setError(null);
    try {
      await onSubmit({ name: name.trim(), order: parsedOrder });
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors de la sauvegarde');
    } finally {
      setLoading(false);
    }
  };

  const nameError = error === 'Le nom du chapitre est requis' ? error : null;
  const orderError =
    error && error !== 'Le nom du chapitre est requis' ? error : null;

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
          error={Boolean(nameError)}
          helperText={
            nameError ??
            'Le numéro (ex. « 1. ») sera ajouté automatiquement à la création si absent'
          }
          disabled={loading}
          onKeyDown={(e) => {
            if (e.key === 'Enter') void handleSubmit();
          }}
        />

        {showOrderField ? (
          <TextField
            fullWidth
            type="number"
            label="Ordre dans la formation"
            value={order}
            onChange={(e) => setOrder(e.target.value)}
            margin="normal"
            disabled={loading}
            error={Boolean(orderError)}
            helperText={
              orderError ?? `Position de 1 (premier) à ${chapterCount} (dernier)`
            }
            inputProps={{ min: 1, max: chapterCount, step: 1 }}
            onKeyDown={(e) => {
              if (e.key === 'Enter') void handleSubmit();
            }}
          />
        ) : null}
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
