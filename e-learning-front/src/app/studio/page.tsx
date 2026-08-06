'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  Container,
  Typography,
  Box,
  Paper,
  List,
  ListItem,
  ListItemText,
  CircularProgress,
  Alert,
  Button,
  IconButton,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  ArrowBack as ArrowBackIcon,
} from '@mui/icons-material';
import AuthGuard from '../../components/AuthGuard';
import ConfirmDeleteDialog from '../../components/studio/ConfirmDeleteDialog';
import { useStudioStore } from '../../stores/studio.store';
import {
  calculateFormationTotalDuration,
  formatDurationCompact,
} from '../../utils/formation';
import type { Formation } from '../../types';

export default function StudioDashboard() {
  const router = useRouter();
  const { formations, loading, error, fetchFormations, deleteFormation } = useStudioStore();
  const [deleteTarget, setDeleteTarget] = useState<Formation | null>(null);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    fetchFormations();
  }, [fetchFormations]);

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await deleteFormation(deleteTarget.id);
      setDeleteTarget(null);
    } catch (err) {
      console.error(err);
    } finally {
      setDeleting(false);
    }
  };

  return (
    <AuthGuard>
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3, gap: 2 }}>
          <IconButton onClick={() => router.push('/')} aria-label="Retour au catalogue">
            <ArrowBackIcon />
          </IconButton>
          <Typography variant="h4" component="h1" sx={{ flexGrow: 1 }}>
            Studio
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => router.push('/studio/formation/new')}
          >
            Nouvelle formation
          </Button>
        </Box>

        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
            <CircularProgress />
          </Box>
        ) : error ? (
          <Alert severity="error">{error}</Alert>
        ) : formations.length === 0 ? (
          <Paper sx={{ p: 4, textAlign: 'center' }}>
            <Typography color="text.secondary" gutterBottom>
              Aucune formation créée pour le moment.
            </Typography>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              sx={{ mt: 2 }}
              onClick={() => router.push('/studio/formation/new')}
            >
              Créer ma première formation
            </Button>
          </Paper>
        ) : (
          <Paper>
            <List>
              {formations.map((formation) => (
                <ListItem
                  key={formation.id}
                  secondaryAction={
                    <Box>
                      <IconButton
                        edge="end"
                        aria-label="Éditer"
                        onClick={() => router.push(`/studio/formation/${encodeURIComponent(formation.id)}`)}
                      >
                        <EditIcon />
                      </IconButton>
                      <IconButton
                        edge="end"
                        aria-label="Supprimer"
                        onClick={() => setDeleteTarget(formation)}
                      >
                        <DeleteIcon />
                      </IconButton>
                    </Box>
                  }
                >
                  <ListItemText
                    primary={formation.name}
                    secondary={`${formation.chapters.length} chapitre(s) · ${formatDurationCompact(calculateFormationTotalDuration(formation))}`}
                  />
                </ListItem>
              ))}
            </List>
          </Paper>
        )}

        <ConfirmDeleteDialog
          open={Boolean(deleteTarget)}
          title="Supprimer la formation"
          message={`Voulez-vous vraiment supprimer « ${deleteTarget?.name} » ? Cette action est irréversible.`}
          onClose={() => setDeleteTarget(null)}
          onConfirm={handleDelete}
          loading={deleting}
        />
      </Container>
    </AuthGuard>
  );
}
