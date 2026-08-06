'use client';

import {
  Box,
  CircularProgress,
  IconButton,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Paper,
  Typography,
} from '@mui/material';
import {
  Description as DescriptionIcon,
  Download as DownloadIcon,
  Image as ImageIcon,
  OpenInNew as OpenInNewIcon,
  PictureAsPdf as PictureAsPdfIcon,
} from '@mui/icons-material';
import type { Document } from '../types';
import { apiService } from '../services/api';

interface DocumentsPanelProps {
  readonly documents: Document[];
  readonly loading?: boolean;
  readonly error?: string | null;
  /** Mode compact pour listes imbriquées (page formation). */
  readonly compact?: boolean;
  /** Ne rien rendre si la liste est vide (utile sous une vidéo). */
  readonly hideWhenEmpty?: boolean;
  readonly title?: string;
}

function documentIcon(mimeType?: string | null) {
  if (mimeType?.includes('pdf')) return <PictureAsPdfIcon color="action" />;
  if (mimeType?.startsWith('image/')) return <ImageIcon color="action" />;
  return <DescriptionIcon color="action" />;
}

export default function DocumentsPanel({
  documents,
  loading = false,
  error = null,
  compact = false,
  hideWhenEmpty = false,
  title,
}: DocumentsPanelProps) {
  if (loading) {
    return (
      <Paper sx={{ p: compact ? 1.5 : 3, display: 'flex', justifyContent: 'center' }}>
        <CircularProgress size={compact ? 20 : 28} />
      </Paper>
    );
  }

  if (error) {
    return (
      <Paper sx={{ p: 2 }}>
        <Typography color="error" variant={compact ? 'body2' : 'body1'}>
          {error}
        </Typography>
      </Paper>
    );
  }

  if (documents.length === 0) {
    if (hideWhenEmpty) return null;
    return (
      <Paper sx={{ p: compact ? 1.5 : 3 }}>
        <Typography color="text.secondary" variant={compact ? 'body2' : 'body1'}>
          Aucun document
        </Typography>
      </Paper>
    );
  }

  return (
    <Box>
      {title && (
        <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1, mt: compact ? 1 : 0 }}>
          {title}
        </Typography>
      )}
      <Paper sx={{ p: compact ? 0.5 : 1 }} variant={compact ? 'outlined' : 'elevation'}>
        <List dense={compact} disablePadding>
          {documents.map((document) => (
            <ListItem
              key={document.id}
              secondaryAction={
                <Box>
                  <IconButton
                    edge="end"
                    size={compact ? 'small' : 'medium'}
                    aria-label="Ouvrir"
                    component="a"
                    href={apiService.documentFileUrl(document.id)}
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={(event) => event.stopPropagation()}
                  >
                    <OpenInNewIcon fontSize={compact ? 'small' : 'medium'} />
                  </IconButton>
                  <IconButton
                    edge="end"
                    size={compact ? 'small' : 'medium'}
                    aria-label="Télécharger"
                    component="a"
                    href={apiService.documentFileUrl(document.id, true)}
                    download={document.filename || true}
                    onClick={(event) => event.stopPropagation()}
                  >
                    <DownloadIcon fontSize={compact ? 'small' : 'medium'} />
                  </IconButton>
                </Box>
              }
            >
              <ListItemIcon sx={compact ? { minWidth: 36 } : undefined}>
                {documentIcon(document.mime_type)}
              </ListItemIcon>
              <ListItemText
                primary={document.title}
                secondary={document.filename || document.mime_type || undefined}
                primaryTypographyProps={compact ? { variant: 'body2' } : undefined}
                secondaryTypographyProps={compact ? { variant: 'caption' } : undefined}
              />
            </ListItem>
          ))}
        </List>
      </Paper>
    </Box>
  );
}
