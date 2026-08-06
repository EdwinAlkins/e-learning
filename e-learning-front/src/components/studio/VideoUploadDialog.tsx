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
  LinearProgress,
  Typography,
} from '@mui/material';
import { API_BASE_URL } from '../../services/api';

interface VideoUploadDialogProps {
  open: boolean;
  mode: 'create' | 'edit';
  videoId?: string;
  initialTitle?: string;
  uploadProgress?: number;
  onClose: () => void;
  onSubmit: (data: { title: string; file?: File }) => Promise<void>;
}

function isAudioFile(file: File | null): boolean {
  if (!file) return false;
  return file.type.startsWith('audio/') || /\.(mp3|wav|m4a|aac|ogg|opus)$/i.test(file.name);
}

export default function VideoUploadDialog({
  open,
  mode,
  videoId,
  initialTitle = '',
  uploadProgress,
  onClose,
  onSubmit,
}: VideoUploadDialogProps) {
  const [title, setTitle] = useState(initialTitle);
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const objectUrlRef = useRef<string | null>(null);

  useEffect(() => {
    if (open) {
      setTitle(initialTitle);
      setFile(null);
      setError(null);
      if (objectUrlRef.current) {
        URL.revokeObjectURL(objectUrlRef.current);
        objectUrlRef.current = null;
      }
      setPreviewUrl(
        mode === 'edit' && videoId ? `${API_BASE_URL}/videos/${videoId}/stream` : null
      );
    }
  }, [open, initialTitle, mode, videoId]);

  useEffect(() => {
    return () => {
      if (objectUrlRef.current) {
        URL.revokeObjectURL(objectUrlRef.current);
      }
    };
  }, []);

  const isUploading = loading && uploadProgress != null;
  const previewIsAudio = isAudioFile(file);

  const handleFileChange = (nextFile: File | null) => {
    setFile(nextFile);
    if (objectUrlRef.current) {
      URL.revokeObjectURL(objectUrlRef.current);
      objectUrlRef.current = null;
    }
    if (nextFile) {
      const url = URL.createObjectURL(nextFile);
      objectUrlRef.current = url;
      setPreviewUrl(url);
    } else if (mode === 'edit' && videoId) {
      setPreviewUrl(`${API_BASE_URL}/videos/${videoId}/stream`);
    } else {
      setPreviewUrl(null);
    }
  };

  const handleSubmit = async () => {
    if (!title.trim()) {
      setError('Le titre est requis');
      return;
    }

    if (mode === 'create' && !file) {
      setError('Sélectionnez un fichier vidéo ou audio');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      await onSubmit({ title: title.trim(), file: file ?? undefined });
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors de la sauvegarde');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onClose={loading ? undefined : onClose} maxWidth="md" fullWidth>
      <DialogTitle>{mode === 'create' ? 'Ajouter un média' : 'Modifier le média'}</DialogTitle>
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

        {previewUrl && (
          <Box sx={{ mt: 2, bgcolor: 'black', borderRadius: 1, overflow: 'hidden', p: previewIsAudio ? 2 : 0 }}>
            {previewIsAudio ? (
              <Box
                component="audio"
                key={previewUrl}
                src={previewUrl}
                controls
                sx={{ width: '100%', display: 'block' }}
              />
            ) : (
              <Box
                component="video"
                key={previewUrl}
                src={previewUrl}
                controls
                sx={{ width: '100%', maxHeight: 360, display: 'block' }}
              />
            )}
          </Box>
        )}

        <Box sx={{ mt: 2 }}>
          <input
            ref={fileInputRef}
            type="file"
            accept="video/*,audio/*"
            hidden
            onChange={(e) => handleFileChange(e.target.files?.[0] ?? null)}
          />
          <Button
            variant="outlined"
            onClick={() => fileInputRef.current?.click()}
            disabled={loading}
            fullWidth
          >
            {file
              ? file.name
              : mode === 'create'
                ? 'Choisir un fichier vidéo ou audio'
                : 'Remplacer le fichier (optionnel)'}
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
          {mode === 'create' ? 'Ajouter' : 'Enregistrer'}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
