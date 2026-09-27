import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import '../../../data/models/models.dart';
import '../providers/usage_provider.dart';

/// Libellés des types d'appels LLM (alignés sur le front web).
const _kindLabels = {
  'chat': 'Assistant formation',
  'summary': 'Résumés de vidéos',
};

String usageKindLabel(String kind) => _kindLabels[kind] ?? kind;

final _tokens = NumberFormat.decimalPattern('fr');

Future<void> showUsageSheet(BuildContext context) {
  return showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    useSafeArea: true,
    showDragHandle: true,
    builder: (_) => const UsageSheet(),
  );
}

class UsageButton extends StatelessWidget {
  const UsageButton({super.key});

  @override
  Widget build(BuildContext context) {
    return IconButton(
      tooltip: 'Consommation IA',
      onPressed: () => showUsageSheet(context),
      icon: const Icon(Icons.insights_outlined),
    );
  }
}

/// Vue simplifiée de `GET /usage` : totaux, activité par jour, répartition.
class UsageSheet extends ConsumerStatefulWidget {
  const UsageSheet({super.key});

  @override
  ConsumerState<UsageSheet> createState() => _UsageSheetState();
}

class _UsageSheetState extends ConsumerState<UsageSheet> {
  static const _windows = [7, 30, 90];
  int _days = 30;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final usage = ref.watch(usageProvider(_days));

    return Padding(
      padding: const EdgeInsets.fromLTRB(24, 0, 24, 24),
      child: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          mainAxisSize: MainAxisSize.min,
          children: [
            Text('Consommation IA', style: theme.textTheme.titleLarge),
            const SizedBox(height: 4),
            Text(
              'Tokens consommés par l’assistant et les résumés que vous avez '
              'demandés.',
              style: theme.textTheme.bodySmall?.copyWith(
                color: theme.colorScheme.onSurfaceVariant,
              ),
            ),
            const SizedBox(height: 16),
            SegmentedButton<int>(
              segments: [
                for (final days in _windows)
                  ButtonSegment(value: days, label: Text('$days j')),
              ],
              selected: {_days},
              showSelectedIcon: false,
              onSelectionChanged: (selection) =>
                  setState(() => _days = selection.first),
            ),
            const SizedBox(height: 16),
            usage.when(
              // Garde la place du contenu : évite un saut de hauteur du panneau.
              loading: () => const SizedBox(
                height: 240,
                child: Center(child: CircularProgressIndicator()),
              ),
              error: (error, _) => _ErrorView(
                message: '$error',
                onRetry: () => ref.invalidate(usageProvider(_days)),
              ),
              data: (data) => _UsageContent(usage: data),
            ),
          ],
        ),
      ),
    );
  }
}

class _UsageContent extends StatelessWidget {
  const _UsageContent({required this.usage});

  final UserTokenUsage usage;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final period = usage.period;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Row(
          children: [
            Expanded(
              child: _StatTile(
                label: 'Sur ${usage.days} jours',
                value: _tokens.format(period.totalTokens),
                detail: '${_tokens.format(period.calls)} appel(s)',
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: _StatTile(
                label: 'Depuis le début',
                value: _tokens.format(usage.allTime.totalTokens),
                detail: '${_tokens.format(usage.allTime.calls)} appel(s)',
              ),
            ),
          ],
        ),
        if (period.totalTokens > 0) ...[
          const SizedBox(height: 8),
          Text(
            'Entrée ${_tokens.format(period.promptTokens)} · '
            'sortie ${_tokens.format(period.completionTokens)}',
            style: theme.textTheme.bodySmall?.copyWith(
              color: theme.colorScheme.onSurfaceVariant,
            ),
          ),
        ],
        const SizedBox(height: 24),
        if (period.calls == 0)
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 24),
            child: Text(
              'Aucune consommation sur les ${usage.days} derniers jours.',
              textAlign: TextAlign.center,
              style: theme.textTheme.bodyMedium?.copyWith(
                color: theme.colorScheme.onSurfaceVariant,
              ),
            ),
          )
        else ...[
          Text('Par jour', style: theme.textTheme.titleSmall),
          const SizedBox(height: 8),
          _DailyBars(daily: usage.daily),
          const SizedBox(height: 24),
          Text('Par usage', style: theme.textTheme.titleSmall),
          const SizedBox(height: 4),
          for (final entry in usage.byKind)
            _BreakdownRow(
              label: usageKindLabel(entry.key),
              tokens: entry.totals.totalTokens,
              share: period.totalTokens == 0
                  ? 0
                  : entry.totals.totalTokens / period.totalTokens,
            ),
        ],
      ],
    );
  }
}

class _StatTile extends StatelessWidget {
  const _StatTile({
    required this.label,
    required this.value,
    required this.detail,
  });

  final String label;
  final String value;
  final String detail;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final muted = theme.colorScheme.onSurfaceVariant;
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label,
            style: theme.textTheme.labelMedium?.copyWith(color: muted),
          ),
          const SizedBox(height: 4),
          FittedBox(
            fit: BoxFit.scaleDown,
            alignment: Alignment.centerLeft,
            child: Text(
              value,
              style: theme.textTheme.headlineSmall?.copyWith(
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
          Text(
            'tokens',
            style: theme.textTheme.bodySmall?.copyWith(color: muted),
          ),
          const SizedBox(height: 4),
          Text(
            detail,
            style: theme.textTheme.bodySmall?.copyWith(color: muted),
          ),
        ],
      ),
    );
  }
}

/// Histogramme minimal : une barre par jour, hauteur relative au maximum.
class _DailyBars extends StatelessWidget {
  const _DailyBars({required this.daily});

  final List<DailyTokenUsage> daily;

  static const _height = 72.0;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final peak = daily.fold<int>(
      0,
      (max, d) => math.max(max, d.totals.totalTokens),
    );
    final dates = DateFormat('dd/MM');
    final labelStyle = theme.textTheme.labelSmall?.copyWith(
      color: theme.colorScheme.onSurfaceVariant,
    );

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Semantics(
          label: 'Pic : ${_tokens.format(peak)} tokens sur une journée',
          child: SizedBox(
            height: _height,
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                for (final day in daily)
                  Expanded(
                    child: Tooltip(
                      message:
                          '${dates.format(day.day)} : '
                          '${_tokens.format(day.totals.totalTokens)} tokens',
                      child: Container(
                        margin: EdgeInsets.symmetric(
                          horizontal: daily.length > 40 ? 0.5 : 1.5,
                        ),
                        height: peak == 0 || day.totals.totalTokens == 0
                            ? 2
                            : math.max(
                                3,
                                _height * day.totals.totalTokens / peak,
                              ),
                        decoration: BoxDecoration(
                          color: day.totals.totalTokens == 0
                              ? theme.colorScheme.outlineVariant
                              : theme.colorScheme.primary,
                          borderRadius: BorderRadius.circular(2),
                        ),
                      ),
                    ),
                  ),
              ],
            ),
          ),
        ),
        if (daily.isNotEmpty) ...[
          const SizedBox(height: 4),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(dates.format(daily.first.day), style: labelStyle),
              Text('pic ${_tokens.format(peak)}', style: labelStyle),
              Text(dates.format(daily.last.day), style: labelStyle),
            ],
          ),
        ],
      ],
    );
  }
}

class _BreakdownRow extends StatelessWidget {
  const _BreakdownRow({
    required this.label,
    required this.tokens,
    required this.share,
  });

  final String label;
  final int tokens;
  final double share;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              Expanded(child: Text(label, style: theme.textTheme.bodyMedium)),
              Text(
                '${_tokens.format(tokens)} · ${(share * 100).round()} %',
                style: theme.textTheme.bodySmall,
              ),
            ],
          ),
          const SizedBox(height: 4),
          LinearProgressIndicator(
            value: share.clamp(0, 1).toDouble(),
            minHeight: 6,
            borderRadius: BorderRadius.circular(3),
          ),
        ],
      ),
    );
  }
}

class _ErrorView extends StatelessWidget {
  const _ErrorView({required this.message, required this.onRetry});

  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 24),
      child: Column(
        children: [
          Text(message, textAlign: TextAlign.center),
          const SizedBox(height: 12),
          FilledButton.tonal(
            onPressed: onRetry,
            child: const Text('Réessayer'),
          ),
        ],
      ),
    );
  }
}
