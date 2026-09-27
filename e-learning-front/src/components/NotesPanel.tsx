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
import { useNoteMutations } from '../features/player/queries/player.queries';
import { formatTime } from '../utils/time';
import { SNACKBAR_DURATION_MS } from '../constants';

interface NotesPanelProps {
  readonly videoId: string;
}

export default function NotesPanel({ videoId }: NotesPanelProps) {
  const [content, setContent] = useState('');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const { currentTime } = usePlayerStore();
  const { createNote } = useNoteMutations(videoId);
  const theme = useTheme();

  const handleCreateNote = async () => {
    if (!content.trim()) {
      return;
    }

    try {
      await createNote.mutateAsync({ timecode: currentTime, content: content.trim() });
      setContent('');
    } catch (error) {
      console.error('Failed to create note:', error);
      setErrorMessage('Échec de la création de la note. Réessayez.');
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
          disabled={createNote.isPending || !content.trim()}
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
