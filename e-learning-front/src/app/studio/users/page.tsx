'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Container,
  IconButton,
  Paper,
  Snackbar,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TablePagination,
  TableRow,
  Tooltip,
  Typography,
} from '@mui/material';
import {
  Add as AddIcon,
  ArrowBack as ArrowBackIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
} from '@mui/icons-material';
import AuthGuard from '../../../components/AuthGuard';
import ConfirmDeleteDialog from '../../../components/studio/ConfirmDeleteDialog';
import UserDialog from '../../../components/studio/UserDialog';
import {
  useUserMutations,
  useUsersQuery,
} from '../../../features/users/queries/user.queries';
import { apiErrorMessage } from '../../../shared/api/errors';
import { useAuthStore } from '../../../stores/auth.store';
import { SNACKBAR_DURATION_MS } from '../../../constants';
import type { AdminUser, CreateUserPayload, UpdateUserPayload } from '../../../types';

const PAGE_SIZE = 25;

export default function StudioUsers() {
  const router = useRouter();
  const me = useAuthStore((state) => state.user);
  const [page, setPage] = useState(0);
  const usersQuery = useUsersQuery(page, PAGE_SIZE);
  const { createUser, updateUser, deleteUser } = useUserMutations();
  const users = usersQuery.data?.items ?? [];
  const total = usersQuery.data?.total ?? 0;
  const loading = usersQuery.isLoading;
  const [actionError, setActionError] = useState<string | null>(null);
  const error =
    actionError ??
    (usersQuery.error
      ? apiErrorMessage(usersQuery.error, 'Chargement des comptes impossible.')
      : null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editTarget, setEditTarget] = useState<AdminUser | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<AdminUser | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);

  const openCreate = () => {
    setEditTarget(null);
    setDialogOpen(true);
  };

  const openEdit = (user: AdminUser) => {
    setEditTarget(user);
    setDialogOpen(true);
  };

  const handleCreate = async (payload: CreateUserPayload) => {
    try {
      await createUser.mutateAsync(payload);
    } catch (err) {
      throw new Error(apiErrorMessage(err, 'Création impossible.'));
    }
    setDialogOpen(false);
    setFeedback('Compte créé');
  };

  const handleUpdate = async (userId: string, payload: UpdateUserPayload) => {
    try {
      await updateUser.mutateAsync({ userId, payload });
    } catch (err) {
      throw new Error(apiErrorMessage(err, 'Modification impossible.'));
    }
    setDialogOpen(false);
    setFeedback('Compte modifié');
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    try {
      await deleteUser.mutateAsync(deleteTarget.id);
      setDeleteTarget(null);
      setFeedback('Compte supprimé');
      const lastPage = Math.max(0, Math.ceil((total - 1) / PAGE_SIZE) - 1);
      setPage(Math.min(page, lastPage));
    } catch (err) {
      setActionError(apiErrorMessage(err, 'Suppression impossible.'));
      setDeleteTarget(null);
    }
  };

  return (
    <AuthGuard>
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3, gap: 2 }}>
          <IconButton onClick={() => router.push('/studio')} aria-label="Retour au studio">
            <ArrowBackIcon />
          </IconButton>
          <Typography variant="h4" component="h1" sx={{ flexGrow: 1 }}>
            Comptes
          </Typography>
          <Button variant="contained" startIcon={<AddIcon />} onClick={openCreate}>
            Nouveau compte
          </Button>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setActionError(null)}>
            {error}
          </Alert>
        )}

        <Paper>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Email</TableCell>
                  <TableCell>Nom</TableCell>
                  <TableCell>Rôle</TableCell>
                  <TableCell>Statut</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {loading ? (
                  <TableRow>
                    <TableCell colSpan={5} align="center" sx={{ py: 6 }}>
                      <CircularProgress />
                    </TableCell>
                  </TableRow>
                ) : (
                  users.map((user) => {
                    const isSelf = user.id === me?.id;
                    return (
                      <TableRow key={user.id} hover>
                        <TableCell>
                          {user.email}
                          {isSelf && (
                            <Typography component="span" variant="body2" color="text.secondary">
                              {' '}
                              (vous)
                            </Typography>
                          )}
                        </TableCell>
                        <TableCell>{user.full_name ?? '—'}</TableCell>
                        <TableCell>
                          <Chip
                            size="small"
                            label={user.is_admin ? 'Admin' : 'Apprenant'}
                            color={user.is_admin ? 'primary' : 'default'}
                          />
                        </TableCell>
                        <TableCell>
                          <Chip
                            size="small"
                            variant="outlined"
                            label={user.is_active ? 'Actif' : 'Désactivé'}
                            color={user.is_active ? 'success' : 'default'}
                          />
                        </TableCell>
                        <TableCell align="right">
                          <IconButton aria-label="Modifier" onClick={() => openEdit(user)}>
                            <EditIcon />
                          </IconButton>
                          <Tooltip title={isSelf ? 'Vous ne pouvez pas supprimer votre compte' : ''}>
                            <span>
                              <IconButton
                                aria-label="Supprimer"
                                onClick={() => setDeleteTarget(user)}
                                disabled={isSelf}
                              >
                                <DeleteIcon />
                              </IconButton>
                            </span>
                          </Tooltip>
                        </TableCell>
                      </TableRow>
                    );
                  })
                )}
              </TableBody>
            </Table>
          </TableContainer>
          <TablePagination
            component="div"
            count={total}
            page={page}
            onPageChange={(_, nextPage) => setPage(nextPage)}
            rowsPerPage={PAGE_SIZE}
            rowsPerPageOptions={[PAGE_SIZE]}
            labelDisplayedRows={({ from, to, count }) => `${from}–${to} sur ${count}`}
          />
        </Paper>

        <UserDialog
          open={dialogOpen}
          user={editTarget}
          isSelf={editTarget !== null && editTarget.id === me?.id}
          onClose={() => setDialogOpen(false)}
          onCreate={handleCreate}
          onUpdate={handleUpdate}
        />

        <ConfirmDeleteDialog
          open={Boolean(deleteTarget)}
          title="Supprimer le compte"
          message={`Supprimer « ${deleteTarget?.email} » ? Ses notes et sa progression seront aussi supprimées. Cette action est irréversible.`}
          onClose={() => setDeleteTarget(null)}
          onConfirm={handleDelete}
          loading={deleteUser.isPending}
        />

        <Snackbar
          open={feedback !== null}
          autoHideDuration={SNACKBAR_DURATION_MS}
          onClose={() => setFeedback(null)}
          anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
        >
          <Alert onClose={() => setFeedback(null)} severity="success" sx={{ width: '100%' }}>
            {feedback}
          </Alert>
        </Snackbar>
      </Container>
    </AuthGuard>
  );
}
