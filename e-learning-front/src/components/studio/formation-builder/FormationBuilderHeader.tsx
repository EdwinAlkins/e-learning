'use client';

import { Box, IconButton, TextField, Typography } from '@mui/material';
import { ArrowBack as ArrowBackIcon, Save as SaveIcon } from '@mui/icons-material';
import type { Formation } from '../../../types';
import {
  calculateFormationTotalDuration,
  formatDurationDetailed,
  sortChaptersByNumber,
} from '../../../utils/formation';

interface FormationBuilderHeaderProps {
  formation: Formation;
  formationName: string;
  nameError: string | null;
  savingName: boolean;
  onBack: () => void;
  onNameChange: (name: string) => void;
  onSaveName: () => void;
}

export default function FormationBuilderHeader({
  formation,
  formationName,
  nameError,
  savingName,
  onBack,
  onNameChange,
  onSaveName,
}: FormationBuilderHeaderProps) {
  const chapterCount = sortChaptersByNumber(formation.chapters).length;

  return (
    <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 3, gap: 2 }}>
      <IconButton onClick={onBack} aria-label="Retour au studio">
        <ArrowBackIcon />
      </IconButton>
      <Box sx={{ flexGrow: 1 }}>
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-start' }}>
          <TextField
            fullWidth
            label="Titre de la formation"
            value={formationName}
            onChange={(event) => onNameChange(event.target.value)}
            error={Boolean(nameError)}
            helperText={nameError}
            disabled={savingName}
          />
          <IconButton
            color="primary"
            onClick={onSaveName}
            disabled={savingName || formationName.trim() === formation.name}
            aria-label="Enregistrer le titre"
          >
            <SaveIcon />
          </IconButton>
        </Box>
        <Typography variant="subtitle2" color="text.secondary" sx={{ mt: 1 }}>
          {chapterCount} chapitres ·{' '}
          {formatDurationDetailed(calculateFormationTotalDuration(formation))}
        </Typography>
      </Box>
    </Box>
  );
}
