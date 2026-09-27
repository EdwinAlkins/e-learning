'use client';

import { Alert, Box, Collapse, IconButton, Paper, Typography, useTheme } from '@mui/material';
import {
  Cancel as CancelIcon,
  Edit as EditIcon,
  Save as SaveIcon,
} from '@mui/icons-material';
import MDEditor from '@uiw/react-md-editor';
import '@uiw/react-md-editor/markdown-editor.css';
import MarkdownRenderer from '../../../components/MarkdownRenderer';

interface VideoSummaryPanelProps {
  summary: string | null;
  loading: boolean;
  error: string | null;
  visible: boolean;
  editing: boolean;
  draft: string;
  saving: boolean;
  canEdit: boolean;
  onDraftChange: (value: string) => void;
  onEdit: () => void;
  onSave: () => void;
  onCancel: () => void;
}

export default function VideoSummaryPanel({
  summary,
  loading,
  error,
  visible,
  editing,
  draft,
  saving,
  canEdit,
  onDraftChange,
  onEdit,
  onSave,
  onCancel,
}: VideoSummaryPanelProps) {
  const theme = useTheme();

  return (
    <>
      {error && (
        <Box sx={{ mb: 3 }}>
          <Alert severity="error">{error}</Alert>
        </Box>
      )}
      <Collapse in={visible && !loading && !error}>
        <Box sx={{ mb: 3 }}>
          {summary && (
            <Paper sx={{ p: 2, backgroundColor: 'background.default' }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6">Résumé</Typography>
                <Box>
                  {editing ? (
                    <>
                      <IconButton
                        size="small"
                        aria-label="Enregistrer"
                        onClick={onSave}
                        disabled={saving}
                        color="primary"
                      >
                        <SaveIcon />
                      </IconButton>
                      <IconButton
                        size="small"
                        aria-label="Annuler"
                        onClick={onCancel}
                        disabled={saving}
                      >
                        <CancelIcon />
                      </IconButton>
                    </>
                  ) : canEdit ? (
                    <IconButton size="small" aria-label="Modifier" onClick={onEdit}>
                      <EditIcon />
                    </IconButton>
                  ) : null}
                </Box>
              </Box>
              <Collapse in={editing}>
                <Box sx={{ mb: 2 }}>
                  <MDEditor
                    value={draft}
                    onChange={(value) => onDraftChange(value || '')}
                    preview="edit"
                    hideToolbar={false}
                    visibleDragbar={false}
                    data-color-mode={theme.palette.mode}
                    height={400}
                  />
                </Box>
              </Collapse>
              {!editing && <MarkdownRenderer source={summary} />}
            </Paper>
          )}
        </Box>
      </Collapse>
    </>
  );
}
