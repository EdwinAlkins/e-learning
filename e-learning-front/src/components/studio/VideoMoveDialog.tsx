'use client';

import { useEffect, useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Typography,
} from '@mui/material';
import type { Chapter } from '../../types';
import { sortVideosByNumber } from '../../utils/formation';

interface VideoMoveDialogProps {
  open: boolean;
  chapters: Chapter[];
  currentChapterId: string;
  videoTitle: string;
  onClose: () => void;
  onSubmit: (toChapterId: string, toIndex?: number) => Promise<void>;
}

export default function VideoMoveDialog({
  open,
  chapters,
  currentChapterId,
  videoTitle,
  onClose,
  onSubmit,
}: VideoMoveDialogProps) {
  const [targetChapterId, setTargetChapterId] = useState(currentChapterId);
  const [targetPosition, setTargetPosition] = useState<number>(-1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const targetChapter = chapters.find((chapter) => chapter.id === targetChapterId);
  const targetVideos = targetChapter ? sortVideosByNumber(targetChapter.videos) : [];
  const isSameChapter = targetChapterId === currentChapterId;
  const maxPosition = isSameChapter
    ? Math.max(0, targetVideos.length - 1)
    : targetVideos.length;

  useEffect(() => {
    if (open) {
      setTargetChapterId(currentChapterId);
      setTargetPosition(-1);
      setError(null);
    }
  }, [open, currentChapterId]);

  useEffect(() => {
    setTargetPosition(-1);
  }, [targetChapterId]);

  const handleSubmit = async () => {
    setLoading(true);
    setError(null);
    try {
      const toIndex = targetPosition === -1 ? undefined : targetPosition;
      await onSubmit(targetChapterId, toIndex);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors du déplacement');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onClose={loading ? undefined : onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Déplacer la vidéo</DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          « {videoTitle} »
        </Typography>

        <FormControl fullWidth margin="normal">
          <InputLabel id="move-chapter-label">Chapitre de destination</InputLabel>
          <Select
            labelId="move-chapter-label"
            label="Chapitre de destination"
            value={targetChapterId}
            onChange={(e) => setTargetChapterId(e.target.value)}
            disabled={loading}
          >
            {chapters.map((chapter) => (
              <MenuItem key={chapter.id} value={chapter.id}>
                {chapter.name}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        <FormControl fullWidth margin="normal">
          <InputLabel id="move-position-label">Position</InputLabel>
          <Select
            labelId="move-position-label"
            label="Position"
            value={targetPosition}
            onChange={(e) => setTargetPosition(Number(e.target.value))}
            disabled={loading}
          >
            <MenuItem value={-1}>À la fin</MenuItem>
            {Array.from({ length: maxPosition + 1 }, (_, index) => (
              <MenuItem key={index} value={index}>
                Position {index + 1}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

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
          Déplacer
        </Button>
      </DialogActions>
    </Dialog>
  );
}
