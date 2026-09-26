'use client';

import { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  Alert,
  Box,
  CircularProgress,
  Container,
  IconButton,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  ToggleButton,
  ToggleButtonGroup,
  Tooltip,
  Typography,
  useMediaQuery,
} from '@mui/material';
import { alpha, useTheme } from '@mui/material/styles';
import { ArrowBack as ArrowBackIcon } from '@mui/icons-material';
import AuthGuard from '../../components/AuthGuard';
import { apiService } from '../../services/api';
import type { DailyTokenUsage, TokenBreakdown, UserTokenUsage } from '../../types';

const PERIODS = [7, 30, 90, 365] as const;

const periodLabel = (days: number) => (days === 365 ? '1 an' : `${days} jours`);
const lastPeriodLabel = (days: number) =>
  days === 365 ? '12 derniers mois' : `${days} derniers jours`;

// Détail entrée / sortie masqué sur mobile (reste dans l'info-bulle et les tuiles)
const DETAIL_COLUMN = { display: { xs: 'none', sm: 'table-cell' } } as const;

const KIND_LABELS: Record<string, string> = {
  chat: 'Assistant formation',
  summary: 'Résumés de vidéos',
};

const numberFormat = new Intl.NumberFormat('fr-FR');
const compactFormat = new Intl.NumberFormat('fr-FR', { notation: 'compact' });
const dayFormat = new Intl.DateTimeFormat('fr-FR', { day: 'numeric', month: 'short', timeZone: 'UTC' });

const formatDay = (isoDay: string) => dayFormat.format(new Date(`${isoDay}T00:00:00Z`));

function StatTile({ label, value, detail }: { label: string; value: string; detail?: string }) {
  return (
    <Paper variant="outlined" sx={{ p: 2, flex: '1 1 180px', minWidth: 0 }}>
      <Typography variant="body2" color="text.secondary">
        {label}
      </Typography>
      <Typography variant="h4" component="p" sx={{ fontWeight: 600, my: 0.5 }}>
        {value}
      </Typography>
      {detail && (
        <Typography variant="caption" color="text.secondary">
          {detail}
        </Typography>
      )}
    </Paper>
  );
}

function DailyChart({ daily }: { daily: DailyTokenUsage[] }) {
  const max = Math.max(...daily.map((d) => d.total_tokens), 0);
  const CHART_HEIGHT = 160;

  if (max === 0) {
    return (
      <Typography color="text.secondary" sx={{ py: 6, textAlign: 'center' }}>
        Aucune consommation sur la période.
      </Typography>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
        <Typography variant="caption" color="text.secondary">
          max {compactFormat.format(max)} tokens / jour
        </Typography>
      </Box>
      <Box
        role="img"
        aria-label="Tokens consommés par jour"
        sx={{
          display: 'flex',
          alignItems: 'flex-end',
          gap: '2px',
          height: CHART_HEIGHT,
          borderBottom: 1,
          borderColor: 'divider',
        }}
      >
        {daily.map((d) => (
          <Tooltip
            key={d.day}
            arrow
            title={
              <Box>
                <strong>{formatDay(d.day)}</strong>
                <br />
                {numberFormat.format(d.total_tokens)} tokens · {d.calls} appel(s)
                <br />
                entrée {numberFormat.format(d.prompt_tokens)} · sortie{' '}
                {numberFormat.format(d.completion_tokens)}
              </Box>
            }
          >
            {/* Cible de survol pleine hauteur, plus large que la barre */}
            <Box sx={{ flex: 1, height: '100%', display: 'flex', alignItems: 'flex-end', cursor: 'default' }}>
              <Box
                sx={{
                  width: '100%',
                  height: d.total_tokens > 0 ? `${Math.max((d.total_tokens / max) * 100, 2)}%` : 0,
                  bgcolor: 'primary.main',
                  borderRadius: '4px 4px 0 0',
                }}
              />
            </Box>
          </Tooltip>
        ))}
      </Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 0.5 }}>
        <Typography variant="caption" color="text.secondary">
          {formatDay(daily[0].day)}
        </Typography>
        <Typography variant="caption" color="text.secondary">
          {formatDay(daily[daily.length - 1].day)}
        </Typography>
      </Box>
    </Box>
  );
}

// Rampe séquentielle mono-teinte : 0 = case vide neutre, 1→4 = intensité croissante
const HEATMAP_ALPHAS = [0.3, 0.55, 0.8, 1] as const;
const HEATMAP_GAP = 3;
const WEEKDAY_LABELS = ['lun', '', 'mer', '', 'ven', '', ''];
const monthFormat = new Intl.DateTimeFormat('fr-FR', { month: 'short', timeZone: 'UTC' });

function heatLevel(tokens: number, max: number): number {
  if (tokens <= 0 || max <= 0) return 0;
  return Math.min(HEATMAP_ALPHAS.length, Math.ceil((tokens / max) * HEATMAP_ALPHAS.length));
}

function HeatCell({ level, size }: { level: number; size: number }) {
  const theme = useTheme();
  return (
    <Box
      sx={{
        width: size,
        height: size,
        borderRadius: '3px',
        bgcolor:
          level === 0 ? 'action.hover' : alpha(theme.palette.primary.main, HEATMAP_ALPHAS[level - 1]),
      }}
    />
  );
}

function DailyHeatmap({ daily }: { daily: DailyTokenUsage[] }) {
  const theme = useTheme();
  const wide = useMediaQuery(theme.breakpoints.up('md'));
  // Sur un an (53 semaines), cases réduites pour tenir dans le panneau desktop
  const yearly = daily.length > 120;
  const cell = yearly ? (wide ? 16 : 12) : wide ? 24 : 16;

  // Si la grille défile, afficher d'abord les semaines les plus récentes
  const scrollRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollLeft = el.scrollWidth;
  }, [daily, cell]);
  const max = Math.max(...daily.map((d) => d.total_tokens), 0);

  // Colonnes = semaines (lundi en haut), cases vides avant le premier jour de la fenêtre
  const utcDay = (d: DailyTokenUsage) => new Date(`${d.day}T00:00:00Z`);
  const offset = (utcDay(daily[0]).getUTCDay() + 6) % 7;
  const cells: (DailyTokenUsage | null)[] = [...Array<null>(offset).fill(null), ...daily];
  const weeks: (DailyTokenUsage | null)[][] = [];
  for (let i = 0; i < cells.length; i += 7) weeks.push(cells.slice(i, i + 7));

  // Libellé de mois au-dessus de la première semaine qui contient un nouveau mois,
  // omis si le mois suivant commence moins de 3 colonnes plus loin (chevauchement)
  let lastMonth = -1;
  const monthLabels = weeks.map((week) => {
    const first = week.find((d): d is DailyTokenUsage => d !== null);
    if (!first) return '';
    const month = utcDay(first).getUTCMonth();
    if (month === lastMonth) return '';
    lastMonth = month;
    return monthFormat.format(utcDay(first));
  });
  monthLabels.forEach((label, w) => {
    if (label && monthLabels.slice(w + 1, w + 3).some(Boolean)) monthLabels[w] = '';
  });

  return (
    <Box ref={scrollRef} sx={{ overflowX: 'auto' }}>
      {/* Conteneur à la largeur de la grille : la légende s'aligne sur son bord droit */}
      <Box sx={{ display: 'inline-flex', flexDirection: 'column' }}>
        <Box sx={{ display: 'inline-flex', gap: `${HEATMAP_GAP}px` }}>
          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              gap: `${HEATMAP_GAP}px`,
              pt: '20px',
              pr: 0.5,
              // Jours de la semaine visibles quand la grille défile (mobile, 1 an)
              position: 'sticky',
              left: 0,
              zIndex: 1,
              bgcolor: 'background.paper',
            }}
          >
            {WEEKDAY_LABELS.map((label, i) => (
              <Typography
                key={i}
                variant="caption"
                color="text.secondary"
                sx={{ height: `${cell}px`, lineHeight: `${cell}px`, fontSize: 11 }}
              >
                {label}
              </Typography>
            ))}
          </Box>
          {weeks.map((week, w) => (
            <Box key={w} sx={{ display: 'flex', flexDirection: 'column', gap: `${HEATMAP_GAP}px` }}>
              <Typography
                variant="caption"
                color="text.secondary"
                sx={{ height: 17, fontSize: 11, whiteSpace: 'nowrap', width: cell, overflow: 'visible' }}
              >
                {monthLabels[w]}
              </Typography>
              {week.map((d, i) =>
                d === null ? (
                  <Box key={i} sx={{ width: cell, height: cell }} />
                ) : (
                  <Tooltip
                    key={d.day}
                    arrow
                    title={
                      <Box>
                        <strong>{formatDay(d.day)}</strong>
                        <br />
                        {d.total_tokens > 0
                          ? `${numberFormat.format(d.total_tokens)} tokens · ${d.calls} appel(s)`
                          : 'Aucune consommation'}
                      </Box>
                    }
                  >
                    <Box aria-label={`${formatDay(d.day)} : ${d.total_tokens} tokens`}>
                      <HeatCell level={heatLevel(d.total_tokens, max)} size={cell} />
                    </Box>
                  </Tooltip>
                )
              )}
            </Box>
          ))}
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: `${HEATMAP_GAP}px`, mt: 1.5 }}>
          <Typography variant="caption" color="text.secondary" sx={{ mr: 0.5 }}>
            Moins
          </Typography>
          {[0, 1, 2, 3, 4].map((level) => (
            <HeatCell key={level} level={level} size={Math.min(cell, 16)} />
          ))}
          <Typography variant="caption" color="text.secondary" sx={{ ml: 0.5 }}>
            Plus
          </Typography>
        </Box>
      </Box>
    </Box>
  );
}

function BreakdownTable({
  title,
  rows,
  labelOf,
}: {
  title: string;
  rows: TokenBreakdown[];
  labelOf?: (key: string) => string;
}) {
  return (
    <Paper variant="outlined" sx={{ p: 2, flex: '1 1 320px', minWidth: 0, overflowX: 'auto' }}>
      <Typography variant="h6" component="h2" gutterBottom>
        {title}
      </Typography>
      {rows.length === 0 ? (
        <Typography color="text.secondary">Aucune donnée.</Typography>
      ) : (
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell />
              <TableCell align="right">Appels</TableCell>
              <TableCell align="right" sx={DETAIL_COLUMN}>Entrée</TableCell>
              <TableCell align="right" sx={DETAIL_COLUMN}>Sortie</TableCell>
              <TableCell align="right">Total</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {rows.map((row) => (
              <TableRow key={row.key}>
                <TableCell sx={{ whiteSpace: 'nowrap' }}>{labelOf ? labelOf(row.key) : row.key}</TableCell>
                <TableCell align="right">{numberFormat.format(row.calls)}</TableCell>
                <TableCell align="right" sx={DETAIL_COLUMN}>
                  {numberFormat.format(row.prompt_tokens)}
                </TableCell>
                <TableCell align="right" sx={DETAIL_COLUMN}>
                  {numberFormat.format(row.completion_tokens)}
                </TableCell>
                <TableCell align="right" sx={{ fontWeight: 600 }}>
                  {numberFormat.format(row.total_tokens)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </Paper>
  );
}

export default function UsagePage() {
  const router = useRouter();
  const [days, setDays] = useState<number>(30);
  const [usage, setUsage] = useState<UserTokenUsage | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    apiService
      .getTokenUsage(days)
      .then((data) => {
        if (!cancelled) {
          setUsage(data);
          setError(null);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Impossible de charger la consommation');
        }
      });
    return () => {
      cancelled = true;
    };
  }, [days]);

  return (
    <AuthGuard>
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 2, mb: 3 }}>
          <IconButton onClick={() => router.push('/')} aria-label="Retour au catalogue">
            <ArrowBackIcon />
          </IconButton>
          <Typography variant="h4" component="h1" sx={{ flexGrow: 1 }}>
            Consommation IA
          </Typography>
          <ToggleButtonGroup
            size="small"
            exclusive
            value={days}
            onChange={(_, value: number | null) => value && setDays(value)}
            aria-label="Période"
          >
            {PERIODS.map((p) => (
              <ToggleButton key={p} value={p}>
                {periodLabel(p)}
              </ToggleButton>
            ))}
          </ToggleButtonGroup>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        {!usage && !error && (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
            <CircularProgress />
          </Box>
        )}

        {usage && (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
              <StatTile
                label={`Tokens · ${lastPeriodLabel(usage.days)}`}
                value={numberFormat.format(usage.period.total_tokens)}
                detail={`entrée ${numberFormat.format(usage.period.prompt_tokens)} · sortie ${numberFormat.format(usage.period.completion_tokens)}`}
              />
              <StatTile
                label={`Appels · ${lastPeriodLabel(usage.days)}`}
                value={numberFormat.format(usage.period.calls)}
              />
              <StatTile
                label="Tokens · depuis le début"
                value={numberFormat.format(usage.all_time.total_tokens)}
                detail={`${numberFormat.format(usage.all_time.calls)} appel(s)`}
              />
            </Box>

            <Paper variant="outlined" sx={{ p: 2 }}>
              <Typography variant="h6" component="h2" gutterBottom>
                Tokens par jour
              </Typography>
              {usage.days >= 90 ? (
                <DailyHeatmap daily={usage.daily} />
              ) : (
                <DailyChart daily={usage.daily} />
              )}
            </Paper>

            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
              <BreakdownTable
                title="Par fonctionnalité"
                rows={usage.by_kind}
                labelOf={(key) => KIND_LABELS[key] ?? key}
              />
              <BreakdownTable title="Par modèle" rows={usage.by_model} />
            </Box>

            <Typography variant="caption" color="text.secondary">
              Seuls les appels qui renvoient un décompte de tokens sont comptés : l&apos;assistant
              et les résumés via l&apos;API OpenAI-compatible. Les résumés Gemini CLI et les
              embeddings ne sont pas comptabilisés.
            </Typography>
          </Box>
        )}
      </Container>
    </AuthGuard>
  );
}
