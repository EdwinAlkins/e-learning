'use client';

import { useRouter, useParams } from 'next/navigation';
import { Alert, Box, Button, CircularProgress, Container } from '@mui/material';
import AuthGuard from '../../../../components/AuthGuard';
import FormationBuilderDialogs from '../../../../components/studio/formation-builder/FormationBuilderDialogs';
import FormationBuilderHeader from '../../../../components/studio/formation-builder/FormationBuilderHeader';
import {
  FormationBuilderProvider,
  useFormationBuilderContext,
} from '../../../../components/studio/formation-builder/FormationBuilderContext';
import StudioChapterList from '../../../../components/studio/formation-builder/StudioChapterList';

function FormationBuilderContent() {
  const router = useRouter();
  const builder = useFormationBuilderContext();

  if (builder.loading && !builder.formation) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (builder.error || (!builder.formation && !builder.loading)) {
    return (
      <>
        <Alert severity="error">{builder.error || 'Formation introuvable'}</Alert>
        <Button sx={{ mt: 2 }} onClick={() => router.push('/studio')}>
          Retour au studio
        </Button>
      </>
    );
  }

  const formation = builder.formation;
  if (!formation) return null;

  return (
    <>
      {builder.jobNotice ? (
        <Alert
          severity="error"
          sx={{ mb: 2 }}
          onClose={builder.clearJobNotice}
        >
          {builder.jobNotice}
        </Alert>
      ) : null}

      <FormationBuilderHeader
        formation={formation}
        formationName={builder.formationName}
        nameError={builder.nameError}
        savingName={builder.savingName}
        onBack={() => router.push('/studio')}
        onNameChange={builder.setFormationName}
        onSaveName={() => void builder.handleSaveFormationName()}
      />

      <StudioChapterList />
      <FormationBuilderDialogs />
    </>
  );
}

export default function FormationBuilderPage() {
  const params = useParams();
  const formationId = decodeURIComponent(params.id as string);

  return (
    <AuthGuard>
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <FormationBuilderProvider formationId={formationId}>
          <FormationBuilderContent />
        </FormationBuilderProvider>
      </Container>
    </AuthGuard>
  );
}
