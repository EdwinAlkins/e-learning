'use client';

import { useState } from 'react';
import {
  Alert,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControlLabel,
  Switch,
  TextField,
} from '@mui/material';
import { useOpenReset } from '../../hooks/useOpenReset';
import { PASSWORD_MAX_LENGTH, PASSWORD_MIN_LENGTH } from '../../constants';
import type { AdminUser, CreateUserPayload, UpdateUserPayload } from '../../types';

interface UserDialogProps {
  open: boolean;
  /** `null` = création. */
  user: AdminUser | null;
  /** Compte de l'admin connecté : rôle et statut non modifiables sur soi-même. */
  isSelf: boolean;
  onClose: () => void;
  onCreate: (payload: CreateUserPayload) => Promise<void>;
  onUpdate: (userId: string, payload: UpdateUserPayload) => Promise<void>;
}

export default function UserDialog({
  open,
  user,
  isSelf,
  onClose,
  onCreate,
  onUpdate,
}: UserDialogProps) {
  const [email, setEmail] = useState('');
  const [fullName, setFullName] = useState('');
  const [password, setPassword] = useState('');
  const [isAdmin, setIsAdmin] = useState(false);
  const [isActive, setIsActive] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const editing = user !== null;

  useOpenReset(open, user?.id ?? 'new', () => {
    setEmail(user?.email ?? '');
    setFullName(user?.full_name ?? '');
    setPassword('');
    setIsAdmin(user?.is_admin ?? false);
    setIsActive(user?.is_active ?? true);
    setError(null);
  });

  const passwordInvalid = password.length > 0 && password.length < PASSWORD_MIN_LENGTH;
  const canSubmit =
    !loading &&
    !passwordInvalid &&
    (editing || (email.trim() !== '' && password.length >= PASSWORD_MIN_LENGTH));

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    const name = fullName.trim() || null;
    try {
      if (user) {
        const payload: UpdateUserPayload = {};
        if (name !== user.full_name) payload.full_name = name;
        if (!isSelf && isAdmin !== user.is_admin) payload.is_admin = isAdmin;
        if (!isSelf && isActive !== user.is_active) payload.is_active = isActive;
        if (password) payload.password = password;
        await onUpdate(user.id, payload);
      } else {
        await onCreate({ email: email.trim(), password, full_name: name, is_admin: isAdmin });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Enregistrement impossible.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onClose={loading ? undefined : onClose} maxWidth="xs" fullWidth>
      <form onSubmit={handleSubmit}>
        <DialogTitle>{editing ? 'Modifier le compte' : 'Nouveau compte'}</DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: '8px !important' }}>
          {error && <Alert severity="error">{error}</Alert>}
          <TextField
            label="Email"
            type="email"
            required={!editing}
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            disabled={loading || editing}
            helperText={editing ? "L'email ne peut pas être modifié" : ' '}
          />
          <TextField
            label="Nom"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            disabled={loading}
            slotProps={{ htmlInput: { maxLength: 255 } }}
          />
          <TextField
            label={editing ? 'Nouveau mot de passe' : 'Mot de passe'}
            type="password"
            autoComplete="new-password"
            required={!editing}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            error={passwordInvalid}
            helperText={
              editing
                ? `Laisser vide pour ne pas changer (${PASSWORD_MIN_LENGTH} à ${PASSWORD_MAX_LENGTH} caractères)`
                : `${PASSWORD_MIN_LENGTH} à ${PASSWORD_MAX_LENGTH} caractères`
            }
            slotProps={{ htmlInput: { maxLength: PASSWORD_MAX_LENGTH } }}
            disabled={loading}
          />
          <FormControlLabel
            control={
              <Switch
                checked={isAdmin}
                onChange={(e) => setIsAdmin(e.target.checked)}
                disabled={loading || isSelf}
              />
            }
            label="Administrateur (accès au studio et aux comptes)"
          />
          {editing && (
            <FormControlLabel
              control={
                <Switch
                  checked={isActive}
                  onChange={(e) => setIsActive(e.target.checked)}
                  disabled={loading || isSelf}
                />
              }
              label="Compte actif"
            />
          )}
          {isSelf && (
            <Alert severity="info">
              Vous ne pouvez ni retirer votre rôle administrateur ni désactiver votre propre compte.
            </Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose} disabled={loading}>
            Annuler
          </Button>
          <Button type="submit" variant="contained" disabled={!canSubmit}>
            {editing ? 'Enregistrer' : 'Créer'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
}
