'use client';

import { useEffect, useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  MenuItem,
  Typography,
} from '@mui/material';
import type { Document, Video } from '../../types';

interface DocumentEditDialogProps {
  open: boolean;
  document: Document;
  videos: Video[];
  onClose: () => void;
  onSubmit: (data: { title: string; videoId: string | null }) => Promise<void>;
}

export default function DocumentEditDialog({
  open,
  document,
  videos,
  onClose,
  onSubmit,
}: DocumentEditDialogProps) {
  const [title, setTitle] = useState(document.title);
  const [videoId, setVideoId] = useState(document.video_id ?? '');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setTitle(document.title);
      setVideoId(document.video_id ?? '');
      setError(null);
    }
  }, [open, document]);

  const handleSubmit = async () => {
    if (!title.trim()) {
      setError('Le titre est requis');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      await onSubmit({
        title: title.trim(),
        videoId: videoId || null,
      });
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors de la sauvegarde');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onClose={loading ? undefined : onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Modifier le document</DialogTitle>
      <DialogContent>
        <TextField
          autoFocus
          fullWidth
          label="Titre"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          margin="normal"
          disabled={loading}
        />

        <TextField
          select
          fullWidth
          label="Associé à"
          value={videoId}
          onChange={(e) => setVideoId(e.target.value)}
          margin="normal"
          disabled={loading}
          helperText="Chapitre entier, ou une vidéo spécifique"
        >
          <MenuItem value="">Tout le chapitre</MenuItem>
          {videos.map((video) => (
            <MenuItem key={video.id} value={video.id}>
              {video.title}
            </MenuItem>
          ))}
        </TextField>

        {document.filename && (
          <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1 }}>
            Fichier : {document.filename}
          </Typography>
        )}

        {error && (
          <Typography variant="body2" color="error" sx={{ mt: 2 }}>
            {error}
          </Typography>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={loading}>
          Annuler
        </Button>
        <Button onClick={handleSubmit} variant="contained" disabled={loading}>
          Enregistrer
        </Button>
      </DialogActions>
    </Dialog>
  );
}
