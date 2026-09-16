import 'package:flutter/material.dart';

import '../../../core/utils/time_format.dart';
import '../providers/media_controller.dart';

/// `02:30 / 12:00 — 25%` + barre linéaire (PLAY-09).
class PlayerProgressBar extends StatelessWidget {
  const PlayerProgressBar({
    super.key,
    required this.controller,
    required this.fallbackDuration,
  });

  final MediaController? controller;
  final double fallbackDuration;

  @override
  Widget build(BuildContext context) {
    final controller = this.controller;
    if (controller == null) {
      return _bar(context, 0, fallbackDuration);
    }
    return ListenableBuilder(
      listenable: controller,
      builder: (context, _) => _bar(
        context,
        controller.positionSeconds,
        controller.durationSeconds > 0
            ? controller.durationSeconds
            : fallbackDuration,
      ),
    );
  }

  Widget _bar(BuildContext context, double position, double duration) {
    final theme = Theme.of(context);
    final percent = percentOf(position, duration);

    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 4),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                '${formatDuration(position)} / ${formatDuration(duration)}',
                style: theme.textTheme.bodySmall,
              ),
              Text('$percent%', style: theme.textTheme.bodySmall),
            ],
          ),
          const SizedBox(height: 6),
          Semantics(
            label: 'Progression de lecture : $percent%',
            child: LinearProgressIndicator(
              value: percent / 100,
              minHeight: 4,
              borderRadius: BorderRadius.circular(4),
            ),
          ),
        ],
      ),
    );
  }
}
