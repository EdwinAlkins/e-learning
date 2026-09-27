'use client';

import { useState } from 'react';
import {
  Alert,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  TextField,
} from '@mui/material';
import { authApi } from '../features/auth/api/auth.api';
import { apiErrorMessage } from '../shared/api/errors';
import { PASSWORD_MAX_LENGTH, PASSWORD_MIN_LENGTH } from '../constants';
import { useOpenReset } from '../hooks/useOpenReset';

interface ChangePasswordDialogProps {
  open: boolean;
  onClose: () => void;
  onChanged: () => void;
}

export default function ChangePasswordDialog({ open, onClose, onChanged }: ChangePasswordDialogProps) {
  const [current, setCurrent] = useState('');
  const [next, setNext] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useOpenReset(open, 'change-password', () => {
    setCurrent('');
    setNext('');
    setConfirm('');
    setError(null);
  });

  const tooShort = next.length > 0 && next.length < PASSWORD_MIN_LENGTH;
  const mismatch = confirm.length > 0 && confirm !== next;

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await authApi.changePassword(current, next);
      onChanged();
    } catch (err) {
      setError(apiErrorMessage(err, 'Changement de mot de passe impossible.'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onClose={loading ? undefined : onClose} maxWidth="xs" fullWidth>
      <form onSubmit={handleSubmit}>
        <DialogTitle>Changer le mot de passe</DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: '8px !important' }}>
          {error && <Alert severity="error">{error}</Alert>}
          <TextField
            label="Mot de passe actuel"
            type="password"
            autoComplete="current-password"
            required
            value={current}
            onChange={(e) => setCurrent(e.target.value)}
            disabled={loading}
          />
          <TextField
            label="Nouveau mot de passe"
            type="password"
            autoComplete="new-password"
            required
            value={next}
            onChange={(e) => setNext(e.target.value)}
            error={tooShort}
            helperText={`${PASSWORD_MIN_LENGTH} à ${PASSWORD_MAX_LENGTH} caractères`}
            slotProps={{ htmlInput: { maxLength: PASSWORD_MAX_LENGTH } }}
            disabled={loading}
          />
          <TextField
            label="Confirmer le nouveau mot de passe"
            type="password"
            autoComplete="new-password"
            required
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            error={mismatch}
            helperText={mismatch ? 'Les mots de passe ne correspondent pas' : ' '}
            disabled={loading}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose} disabled={loading}>
            Annuler
          </Button>
          <Button
            type="submit"
            variant="contained"
            disabled={loading || !current || next.length < PASSWORD_MIN_LENGTH || next !== confirm}
          >
            Enregistrer
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
}
