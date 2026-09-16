import 'package:chewie/chewie.dart';
import 'package:flutter/material.dart';
import 'package:media_kit_video/media_kit_video.dart' as mkv;

import '../../../core/utils/time_format.dart';
import '../providers/media_controller.dart';

/// Rendu du média : `Chewie` (mobile) ou `media_kit` (desktop) pour la vidéo,
/// contrôles dédiés pour l'audio sur toutes les plateformes.
class MediaPlayerView extends StatelessWidget {
  const MediaPlayerView({
    super.key,
    required this.controller,
    required this.title,
    this.onRetry,
  });

  final MediaController controller;
  final String title;
  final VoidCallback? onRetry;

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: controller,
      builder: (context, _) {
        if (controller.isInitializing) {
          return const _PlayerSurface(
            child: Center(child: CircularProgressIndicator()),
          );
        }

        final error = controller.error;
        if (error != null) {
          return _PlayerSurface(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.error_outline, size: 32),
                  const SizedBox(height: 8),
                  Text(error, textAlign: TextAlign.center),
                  if (onRetry != null) ...[
                    const SizedBox(height: 8),
                    FilledButton.tonal(
                      onPressed: onRetry,
                      child: const Text('Réessayer'),
                    ),
                  ],
                ],
              ),
            ),
          );
        }

        if (controller.isAudio) {
          return _AudioControls(controller: controller, title: title);
        }

        // Desktop : rendu libmpv (media_kit), contrôles adaptatifs intégrés.
        final mediaKit = controller.mediaKitController;
        if (mediaKit != null) {
          return AspectRatio(
            aspectRatio: 16 / 9,
            child: mkv.Video(
              controller: mediaKit,
              controls: mkv.AdaptiveVideoControls,
            ),
          );
        }

        final chewie = controller.chewieController;
        if (chewie == null) {
          return const _PlayerSurface(
            child: Center(child: CircularProgressIndicator()),
          );
        }
        final ratio = chewie.videoPlayerController.value.aspectRatio;
        return AspectRatio(
          aspectRatio: ratio > 0 ? ratio : 16 / 9,
          child: Chewie(controller: chewie),
        );
      },
    );
  }
}

class _PlayerSurface extends StatelessWidget {
  const _PlayerSurface({required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context) {
    return AspectRatio(
      aspectRatio: 16 / 9,
      child: ColoredBox(
        color: Theme.of(context).colorScheme.surfaceContainerHighest,
        child: child,
      ),
    );
  }
}

class _AudioControls extends StatefulWidget {
  const _AudioControls({required this.controller, required this.title});

  final MediaController controller;
  final String title;

  @override
  State<_AudioControls> createState() => _AudioControlsState();
}

class _AudioControlsState extends State<_AudioControls> {
  /// Valeur locale pendant le glissement, sinon le flux de position la reprend.
  double? _dragSeconds;

  @override
  Widget build(BuildContext context) {
    final controller = widget.controller;
    final theme = Theme.of(context);
    final duration = controller.durationSeconds;
    final position = _dragSeconds ?? controller.positionSeconds;
    final max = duration > 0 ? duration : 1.0;

    return Card(
      margin: const EdgeInsets.all(12),
      child: Padding(
        padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
        child: Column(
          children: [
            Row(
              children: [
                CircleAvatar(
                  backgroundColor: theme.colorScheme.primaryContainer,
                  child: Icon(
                    Icons.audiotrack,
                    color: theme.colorScheme.onPrimaryContainer,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    widget.title,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: theme.textTheme.titleMedium,
                  ),
                ),
              ],
            ),
            Slider(
              value: position.clamp(0.0, max),
              max: max,
              onChanged: (value) => setState(() => _dragSeconds = value),
              onChangeEnd: (value) async {
                await controller.seekTo(value);
                if (mounted) setState(() => _dragSeconds = null);
              },
            ),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 8),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    formatDuration(position),
                    style: theme.textTheme.bodySmall,
                  ),
                  Text(
                    formatDuration(duration),
                    style: theme.textTheme.bodySmall,
                  ),
                ],
              ),
            ),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                IconButton(
                  tooltip: 'Reculer de 10 secondes',
                  onPressed: () =>
                      controller.skip(const Duration(seconds: -10)),
                  icon: const Icon(Icons.replay_10),
                ),
                const SizedBox(width: 8),
                IconButton.filled(
                  iconSize: 32,
                  tooltip: controller.isPlaying ? 'Pause' : 'Lecture',
                  onPressed: controller.togglePlay,
                  icon: controller.isBuffering
                      ? const SizedBox(
                          width: 24,
                          height: 24,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : Icon(
                          controller.isPlaying ? Icons.pause : Icons.play_arrow,
                        ),
                ),
                const SizedBox(width: 8),
                IconButton(
                  tooltip: 'Avancer de 10 secondes',
                  onPressed: () => controller.skip(const Duration(seconds: 10)),
                  icon: const Icon(Icons.forward_10),
                ),
                const SizedBox(width: 8),
                PopupMenuButton<double>(
                  tooltip: 'Vitesse de lecture',
                  initialValue: controller.speed,
                  onSelected: controller.setSpeed,
                  itemBuilder: (context) => [
                    for (final speed in MediaController.speeds)
                      PopupMenuItem(value: speed, child: Text('${speed}x')),
                  ],
                  child: Chip(
                    label: Text('${controller.speed}x'),
                    visualDensity: VisualDensity.compact,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
