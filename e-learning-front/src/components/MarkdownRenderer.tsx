'use client';

import { Box, useTheme } from '@mui/material';
import MDEditor from '@uiw/react-md-editor';
import '@uiw/react-md-editor/markdown-editor.css';

interface MarkdownRendererProps {
  readonly source: string;
}

export default function MarkdownRenderer({ source }: MarkdownRendererProps) {
  const theme = useTheme();
  const codeBg =
    theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.05)';

  return (
    <Box
      data-color-mode={theme.palette.mode}
      sx={{
        width: '100%',
        '& .w-md-editor-preview': {
          padding: '8px 12px',
          backgroundColor: 'transparent !important',
          color: `${theme.palette.text.primary} !important`,
        },
        '& .wmde-markdown': {
          backgroundColor: 'transparent !important',
          color: `${theme.palette.text.primary} !important`,
        },
        '& .wmde-markdown p': {
          color: `${theme.palette.text.primary} !important`,
        },
        '& .wmde-markdown h1, & .wmde-markdown h2, & .wmde-markdown h3, & .wmde-markdown h4, & .wmde-markdown h5, & .wmde-markdown h6':
          {
            color: `${theme.palette.text.primary} !important`,
          },
        '& .wmde-markdown pre': {
          backgroundColor: `${codeBg} !important`,
          color: `${theme.palette.text.primary} !important`,
        },
        '& .wmde-markdown code': {
          backgroundColor: `${codeBg} !important`,
          color: `${theme.palette.text.primary} !important`,
        },
        '& .wmde-markdown blockquote': {
          borderLeftColor: `${theme.palette.divider} !important`,
          color: `${theme.palette.text.secondary} !important`,
        },
        '& .wmde-markdown a': {
          color: `${theme.palette.primary.main} !important`,
        },
        '& .wmde-markdown table': {
          color: `${theme.palette.text.primary} !important`,
        },
        '& .wmde-markdown table th, & .wmde-markdown table td': {
          borderColor: `${theme.palette.divider} !important`,
        },
      }}
    >
      <MDEditor.Markdown source={source} />
    </Box>
  );
}
