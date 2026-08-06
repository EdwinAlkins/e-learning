'use client';

import { useEffect, useRef, useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Box,
  MenuItem,
  LinearProgress,
  Typography,
} from '@mui/material';
import type { Video } from '../../types';
import {
  DOCUMENT_ACCEPT_ATTR,
  DOCUMENT_ACCEPT_EXTENSIONS,
  isAllowedDocumentFilename,
} from '../../constants';

interface DocumentUploadDialogProps {
  open: boolean;
  videos: Video[];
  uploadProgress?: number;
  onClose: () => void;
  onSubmit: (data: { title: string; file: File; videoId?: string | null }) => Promise<void>;
}

export default function DocumentUploadDialog({
  open,
  videos,
  uploadProgress,
  onClose,
  onSubmit,
}: DocumentUploadDialogProps) {
  const [title, setTitle] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [videoId, setVideoId] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (open) {
      setTitle('');
      setFile(null);
      setVideoId('');
      setError(null);
    }
  }, [open]);

  useEffect(() => {
    if (file) {
      setTitle((current) => current.trim() || file.name.replace(/\.[^.]+$/, ''));
    }
  }, [file]);

  const isUploading = loading && uploadProgress != null;

  const handleSubmit = async () => {
    if (!title.trim()) {
      setError('Le titre est requis');
      return;
    }
    if (!file) {
      setError('Sélectionnez un fichier');
      return;
    }
    if (!isAllowedDocumentFilename(file.name)) {
      setError(
        `Extension non autorisée. Acceptées : ${DOCUMENT_ACCEPT_EXTENSIONS.join(', ')}.`
      );
      return;
    }

    setLoading(true);
    setError(null);
    try {
      await onSubmit({
        title: title.trim(),
        file,
        videoId: videoId || null,
      });
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors de l’upload');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onClose={loading ? undefined : onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Ajouter un document</DialogTitle>
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

        <Box sx={{ mt: 2 }}>
          <input
            ref={fileInputRef}
            type="file"
            accept={DOCUMENT_ACCEPT_ATTR}
            hidden
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
          <Button
            variant="outlined"
            onClick={() => fileInputRef.current?.click()}
            disabled={loading}
            fullWidth
          >
            {file ? file.name : 'Choisir un fichier'}
          </Button>
        </Box>

        {isUploading && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Upload en cours… {uploadProgress}%
            </Typography>
            <LinearProgress variant="determinate" value={uploadProgress ?? 0} />
          </Box>
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
          Ajouter
        </Button>
      </DialogActions>
    </Dialog>
  );
}
