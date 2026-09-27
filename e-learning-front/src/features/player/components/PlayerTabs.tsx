'use client';

import { useState } from 'react';
import { Box, Tab, Tabs } from '@mui/material';
import type { Document } from '../../../types';
import DocumentsPanel from '../../../components/DocumentsPanel';
import NotesList from '../../../components/NotesList';
import NotesPanel from '../../../components/NotesPanel';

interface PlayerTabsProps {
  videoId: string;
  documents: Document[];
  documentsLoading: boolean;
  documentsError: string | null;
  onSeekTo: (time: number) => void;
}

export default function PlayerTabs({
  videoId,
  documents,
  documentsLoading,
  documentsError,
  onSeekTo,
}: PlayerTabsProps) {
  const [activeTab, setActiveTab] = useState(0);

  return (
    <Box sx={{ mb: 3 }}>
      <Tabs
        value={activeTab}
        onChange={(_, value: number) => setActiveTab(value)}
        sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}
      >
        <Tab label="Notes" />
        <Tab label={`Documents${documents.length ? ` (${documents.length})` : ''}`} />
      </Tabs>

      {activeTab === 0 && (
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 3 }}>
          <Box>
            <NotesPanel videoId={videoId} />
          </Box>
          <Box>
            <NotesList videoId={videoId} onSeekTo={onSeekTo} />
          </Box>
        </Box>
      )}

      {activeTab === 1 && (
        <DocumentsPanel
          documents={documents}
          loading={documentsLoading}
          error={documentsError}
        />
      )}
    </Box>
  );
}
