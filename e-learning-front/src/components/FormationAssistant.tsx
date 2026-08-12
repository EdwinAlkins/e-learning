'use client';

import { useState } from 'react';
import type { FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Divider,
  IconButton,
  Link,
  Paper,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import {
  AutoAwesome as AutoAwesomeIcon,
  Refresh as RefreshIcon,
  Send as SendIcon,
} from '@mui/icons-material';
import { apiService } from '../services/api';
import type { RagCitation } from '../types';
import MarkdownRenderer from './MarkdownRenderer';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  citations?: RagCitation[];
}

interface FormationAssistantProps {
  formationId: string;
  formationName: string;
}

export default function FormationAssistant({
  formationId,
  formationName,
}: FormationAssistantProps) {
  const router = useRouter();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [indexing, setIndexing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAsk = async (event: FormEvent) => {
    event.preventDefault();
    const trimmed = question.trim();
    if (!trimmed || loading) return;

    setError(null);
    setQuestion('');
    setMessages((prev) => [...prev, { role: 'user', content: trimmed }]);
    setLoading(true);
    try {
      const result = await apiService.askFormation(formationId, trimmed);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: result.answer,
          citations: result.citations,
        },
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Échec de l'assistant");
    } finally {
      setLoading(false);
    }
  };

  const handleReindex = async () => {
    setIndexing(true);
    setError(null);
    try {
      await apiService.indexFormation(formationId);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content:
            "Indexation démarrée en arrière-plan. Assurez-vous que le serveur d'embeddings "
            + '(APP_EMBEDDING_BASE_URL, ex. LM Studio sur :1234) est démarré avec un modèle '
            + "d'embeddings chargé, puis réessayez une question dans quelques secondes.",
        },
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Échec de l'indexation");
    } finally {
      setIndexing(false);
    }
  };

  return (
    <Paper sx={{ p: 2, mb: 4 }} variant="outlined">
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
        <AutoAwesomeIcon color="primary" fontSize="small" />
        <Typography variant="h6" sx={{ flexGrow: 1 }}>
          Assistant — {formationName}
        </Typography>
        <Button
          size="small"
          startIcon={indexing ? <CircularProgress size={14} /> : <RefreshIcon />}
          onClick={() => void handleReindex()}
          disabled={indexing || loading}
        >
          Réindexer
        </Button>
      </Box>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Posez une question sur le contenu transcrit et les documents de cette formation.
      </Typography>

      {error ? (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      ) : null}

      <Stack spacing={1.5} sx={{ maxHeight: 360, overflowY: 'auto', mb: 2 }}>
        {messages.length === 0 ? (
          <Typography variant="body2" color="text.secondary">
            Exemple : « Quels sont les points clés du chapitre 1 ? »
          </Typography>
        ) : (
          messages.map((message, index) => (
            <Box
              key={`${message.role}-${index}`}
              sx={{
                alignSelf: message.role === 'user' ? 'flex-end' : 'flex-start',
                maxWidth: '92%',
                bgcolor: message.role === 'user' ? 'primary.main' : 'action.hover',
                color: message.role === 'user' ? 'primary.contrastText' : 'text.primary',
                px: 1.5,
                py: 1,
                borderRadius: 2,
              }}
            >
              {message.role === 'assistant' ? (
                <Box
                  sx={{
                    '& .w-md-editor-preview': { padding: '0 !important' },
                    '& .wmde-markdown': {
                      fontSize: '0.875rem',
                      lineHeight: 1.5,
                    },
                    '& .wmde-markdown > :first-of-type': { mt: 0 },
                    '& .wmde-markdown > :last-child': { mb: 0 },
                    '& .wmde-markdown p, & .wmde-markdown li': {
                      fontSize: '0.875rem',
                    },
                    '& .wmde-markdown ul, & .wmde-markdown ol': {
                      my: 0.75,
                      pl: 2.5,
                    },
                    '& .wmde-markdown h1, & .wmde-markdown h2, & .wmde-markdown h3, & .wmde-markdown h4':
                      {
                        fontSize: '1rem',
                        fontWeight: 600,
                        mt: 1,
                        mb: 0.5,
                      },
                  }}
                >
                  <MarkdownRenderer source={message.content} />
                </Box>
              ) : (
                <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                  {message.content}
                </Typography>
              )}
              {message.citations && message.citations.length > 0 ? (
                <Box sx={{ mt: 1 }}>
                  <Divider sx={{ mb: 1, borderColor: 'divider' }} />
                  <Typography variant="caption" display="block" sx={{ mb: 0.5, opacity: 0.85 }}>
                    Sources
                  </Typography>
                  {message.citations.map((citation) => {
                    const citationKey = `${citation.document_id ?? ''}-${citation.video_id ?? ''}-${citation.source}`;
                    const openCitation = () => {
                      if (citation.document_id) {
                        window.open(
                          apiService.documentFileUrl(citation.document_id),
                          '_blank',
                          'noopener,noreferrer'
                        );
                        return;
                      }
                      if (citation.video_id) {
                        router.push(`/player/${citation.video_id}`);
                      }
                    };
                    const canOpen = Boolean(citation.document_id || citation.video_id);
                    return (
                      <Box key={citationKey} sx={{ mb: 0.5 }}>
                        {canOpen ? (
                          <Link
                            component="button"
                            type="button"
                            variant="caption"
                            onClick={openCitation}
                            sx={{ textAlign: 'left' }}
                          >
                            {citation.title} ({citation.source})
                          </Link>
                        ) : (
                          <Typography variant="caption" display="block">
                            {citation.title} ({citation.source})
                          </Typography>
                        )}
                        <Typography variant="caption" display="block" color="text.secondary">
                          {citation.excerpt}
                        </Typography>
                      </Box>
                    );
                  })}
                </Box>
              ) : null}
            </Box>
          ))
        )}
        {loading ? (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <CircularProgress size={18} />
            <Typography variant="body2" color="text.secondary">
              Recherche dans le cours…
            </Typography>
          </Box>
        ) : null}
      </Stack>

      <Box component="form" onSubmit={(event) => void handleAsk(event)} sx={{ display: 'flex', gap: 1 }}>
        <TextField
          fullWidth
          size="small"
          placeholder="Votre question…"
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          disabled={loading}
        />
        <IconButton type="submit" color="primary" disabled={loading || !question.trim()} aria-label="Envoyer">
          <SendIcon />
        </IconButton>
      </Box>
    </Paper>
  );
}
