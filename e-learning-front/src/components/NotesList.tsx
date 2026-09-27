'use client';

import { useState } from 'react';
import {
  List,
  ListItem,
  IconButton,
  Paper,
  Typography,
  Box,
  Collapse,
  Alert,
  Snackbar,
  useTheme,
} from '@mui/material';
import {
  Delete as DeleteIcon,
  Edit as EditIcon,
  Save as SaveIcon,
  Cancel as CancelIcon,
} from '@mui/icons-material';
import MDEditor from '@uiw/react-md-editor';
import '@uiw/react-md-editor/markdown-editor.css';
import type { Note } from '../types';
import {
  useNoteMutations,
  useVideoNotesQuery,
} from '../features/player/queries/player.queries';
import { formatTimecode } from '../utils/time';
import { SNACKBAR_DURATION_MS } from '../constants';
import ConfirmDeleteDialog from './studio/ConfirmDeleteDialog';
import MarkdownRenderer from './MarkdownRenderer';

interface NotesListProps {
  readonly videoId: string;
  readonly onSeekTo: (time: number) => void;
}

export default function NotesList({ videoId, onSeekTo }: NotesListProps) {
  const notesQuery = useVideoNotesQuery(videoId);
  const { updateNote, deleteNote } = useNoteMutations(videoId);
  const notes = notesQuery.data ?? [];
  const [editingNoteId, setEditingNoteId] = useState<string | null>(null);
  const [editContent, setEditContent] = useState<string>('');
  const [noteToDelete, setNoteToDelete] = useState<Note | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const theme = useTheme();

  const handleConfirmDelete = async () => {
    if (!noteToDelete) return;
    try {
      await deleteNote.mutateAsync(noteToDelete.id);
      setNoteToDelete(null);
    } catch (error) {
      console.error('Failed to delete note:', error);
      setErrorMessage('Échec de la suppression. Réessayez.');
    }
  };

  const handleEditNote = (note: Note) => {
    setEditingNoteId(note.id);
    setEditContent(note.content);
  };

  const handleSaveNote = async (noteId: string) => {
    if (!editContent.trim()) {
      setErrorMessage('Le contenu de la note ne peut pas être vide');
      return;
    }

    try {
      await updateNote.mutateAsync({ noteId, content: editContent.trim() });
      setEditingNoteId(null);
      setEditContent('');
    } catch (error) {
      console.error('Failed to update note:', error);
      setErrorMessage('Échec de la mise à jour. Réessayez.');
    }
  };

  const handleCancelEdit = () => {
    setEditingNoteId(null);
    setEditContent('');
  };

  const handleNoteClick = (timecode: number) => {
    if (editingNoteId === null) {
      onSeekTo(timecode);
    }
  };

  if (notesQuery.isLoading) {
    return (
      <Paper sx={{ p: 2 }}>
        <Typography>Chargement des notes…</Typography>
      </Paper>
    );
  }

  if (notesQuery.error) {
    return (
      <Paper sx={{ p: 2 }}>
        <Alert severity="error">Échec du chargement des notes.</Alert>
      </Paper>
    );
  }

  if (notes.length === 0) {
    return (
      <Paper sx={{ p: 2 }}>
        <Typography color="text.secondary">Aucune note pour le moment.</Typography>
      </Paper>
    );
  }

  return (
    <>
      <Paper
        sx={{
          p: 2,
          display: 'flex',
          flexDirection: 'column',
          height: { xs: '60vh', md: '70vh' },
          maxHeight: { xs: '60vh', md: '70vh' },
          overflow: 'hidden',
        }}
      >
        <Typography variant="h6" gutterBottom sx={{ flexShrink: 0 }}>
          Notes ({notes.length})
        </Typography>
        <Box
          sx={{
            overflowY: 'auto',
            overflowX: 'hidden',
            flex: 1,
            minHeight: 0,
            pr: 1,
            '&::-webkit-scrollbar': {
              width: '8px',
            },
            '&::-webkit-scrollbar-track': {
              backgroundColor: 'rgba(0, 0, 0, 0.05)',
              borderRadius: '4px',
            },
            '&::-webkit-scrollbar-thumb': {
              backgroundColor: 'rgba(0, 0, 0, 0.2)',
              borderRadius: '4px',
              '&:hover': {
                backgroundColor: 'rgba(0, 0, 0, 0.3)',
              },
            },
          }}
        >
          <List>
            {notes.map((note) => (
              <ListItem
                key={note.id}
                sx={{
                  borderBottom: '1px solid',
                  borderColor: 'divider',
                  flexDirection: 'column',
                  alignItems: 'stretch',
                  cursor: editingNoteId === note.id ? 'default' : 'pointer',
                  '&:hover': {
                    backgroundColor:
                      editingNoteId === note.id ? 'transparent' : 'action.hover',
                  },
                }}
                onClick={() => handleNoteClick(note.timecode)}
              >
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    width: '100%',
                    mb: 1,
                  }}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography variant="body2" color="primary" sx={{ fontWeight: 'bold' }}>
                      {formatTimecode(note.timecode)}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {new Date(note.created_at).toLocaleDateString()}
                    </Typography>
                  </Box>
                  <Box>
                    {editingNoteId === note.id ? (
                      <>
                        <IconButton
                          size="small"
                          aria-label="Enregistrer"
                          onClick={(e) => {
                            e.stopPropagation();
                            void handleSaveNote(note.id);
                          }}
                          disabled={updateNote.isPending}
                          color="primary"
                        >
                          <SaveIcon />
                        </IconButton>
                        <IconButton
                          size="small"
                          aria-label="Annuler"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleCancelEdit();
                          }}
                          disabled={updateNote.isPending}
                        >
                          <CancelIcon />
                        </IconButton>
                      </>
                    ) : (
                      <>
                        <IconButton
                          size="small"
                          edge="end"
                          aria-label="Modifier"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleEditNote(note);
                          }}
                        >
                          <EditIcon />
                        </IconButton>
                        <IconButton
                          size="small"
                          edge="end"
                          aria-label="supprimer"
                          onClick={(e) => {
                            e.stopPropagation();
                            setNoteToDelete(note);
                          }}
                        >
                          <DeleteIcon />
                        </IconButton>
                      </>
                    )}
                  </Box>
                </Box>
                <Collapse in={editingNoteId === note.id}>
                  <Box sx={{ width: '100%', mb: 2 }}>
                    <MDEditor
                      value={editContent}
                      onChange={(value) => setEditContent(value || '')}
                      preview="edit"
                      hideToolbar={false}
                      visibleDragbar={false}
                      data-color-mode={theme.palette.mode}
                      height={250}
                    />
                  </Box>
                </Collapse>
                {editingNoteId !== note.id && <MarkdownRenderer source={note.content} />}
              </ListItem>
            ))}
          </List>
        </Box>
      </Paper>

      <ConfirmDeleteDialog
        open={noteToDelete !== null}
        title="Supprimer la note"
        message="Êtes-vous sûr de vouloir supprimer cette note ?"
        onClose={() => setNoteToDelete(null)}
        onConfirm={() => void handleConfirmDelete()}
        loading={deleteNote.isPending}
      />

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
    </>
  );
}
