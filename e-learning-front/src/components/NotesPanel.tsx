'use client';

import { useState } from 'react';
import {
  Button,
  Box,
  Paper,
  Typography,
  Alert,
  Snackbar,
  useTheme,
} from '@mui/material';
import { Add as AddIcon } from '@mui/icons-material';
import MDEditor from '@uiw/react-md-editor';
import '@uiw/react-md-editor/markdown-editor.css';
import { usePlayerStore } from '../stores/player.store';
import { apiService } from '../services/api';
import { formatTime } from '../utils/time';
import { SNACKBAR_DURATION_MS } from '../constants';

interface NotesPanelProps {
  readonly videoId: string;
  readonly onNoteCreated: () => void;
}

export default function NotesPanel({ videoId, onNoteCreated }: NotesPanelProps) {
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const { currentTime } = usePlayerStore();
  const theme = useTheme();

  const handleCreateNote = async () => {
    if (!content.trim()) {
      return;
    }

    setLoading(true);
    try {
      await apiService.createNote(videoId, currentTime, content.trim());
      setContent('');
      onNoteCreated();
    } catch (error) {
      console.error('Failed to create note:', error);
      setErrorMessage('Échec de la création de la note. Réessayez.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Paper sx={{ p: 2, mb: 2 }}>
      <Typography variant="h6" gutterBottom>
        Ajouter une note
      </Typography>
      <Box sx={{ mb: 2 }}>
        <MDEditor
          value={content}
          onChange={(value) => setContent(value || '')}
          preview="edit"
          hideToolbar={false}
          visibleDragbar={false}
          data-color-mode={theme.palette.mode}
          height={300}
        />
      </Box>
      <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', justifyContent: 'space-between' }}>
        <Typography variant="caption" color="text.secondary">
          Temps actuel : {formatTime(currentTime)}
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => void handleCreateNote()}
          disabled={loading || !content.trim()}
          sx={{ minWidth: 180 }}
        >
          Lier au temps actuel
        </Button>
      </Box>

      <Snackbar
        open={errorMessage !== null}
        autoHideDuration={SNACKBAR_DURATION_MS}
        onClose={() => setErrorMessage(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert severity="error" onClose={() => setErrorMessage(null)} sx={{ width: '100%' }}>
          {errorMessage}
        </Alert>
      </Snackbar>
    </Paper>
  );
}
