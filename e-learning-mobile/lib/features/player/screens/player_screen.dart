import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../config/constants.dart';
import '../../../data/models/models.dart';
import '../../../data/repositories/video_repository.dart';
import '../../documents/widgets/documents_list.dart';
import '../../notes/widgets/notes_panel.dart';
import '../../settings/widgets/settings_sheet.dart';
import '../../summary/providers/summary_provider.dart';
import '../../summary/widgets/summary_panel.dart';
import '../providers/media_controller.dart';
import '../providers/media_controller_provider.dart';
import '../providers/player_context_provider.dart';
import '../widgets/ai_action_bar.dart';
import '../widgets/media_player_view.dart';
import '../widgets/player_progress_bar.dart';

class PlayerScreen extends ConsumerWidget {
  const PlayerScreen({super.key, required this.videoId, this.formationId});

  final String videoId;
  final String? formationId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final args = (videoId: videoId, formationId: formationId);
    final ctx = ref.watch(playerContextProvider(args));

    // Les données précédentes priment sur l'état de rafraîchissement : le
    // polling des statuts IA ne doit jamais détruire le lecteur en cours.
    if (ctx.hasValue) {
      return _PlayerView(
        key: ValueKey(videoId),
        args: args,
        data: ctx.requireValue,
      );
    }

    if (ctx.hasError) {
      return Scaffold(
        appBar: AppBar(title: const Text('Lecteur')),
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text('${ctx.error}', textAlign: TextAlign.center),
                const SizedBox(height: 12),
                FilledButton(
                  onPressed: () => ref.invalidate(playerContextProvider(args)),
                  child: const Text('Réessayer'),
                ),
              ],
            ),
          ),
        ),
      );
    }

    return const Scaffold(body: Center(child: CircularProgressIndicator()));
  }
}

class _PlayerView extends ConsumerStatefulWidget {
  const _PlayerView({super.key, required this.args, required this.data});

  final PlayerArgs args;
  final PlayerContext data;

  @override
  ConsumerState<_PlayerView> createState() => _PlayerViewState();
}

class _PlayerViewState extends ConsumerState<_PlayerView>
    with TickerProviderStateMixin, WidgetsBindingObserver {
  static const _summaryTab = 1;

  late final TabController _tabs;
  Timer? _pollTimer;
  bool _aiBusy = false;
  String? _aiError;

  VideoItem get _video => widget.data.video;

  /// Contrôleur courant s'il a fini de s'initialiser, sans l'observer : réservé
  /// aux callbacks hors `build` (lifecycle).
  MediaController? get _media =>
      ref.read(mediaControllerProvider(widget.args)).value;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _tabs = TabController(length: 3, vsync: this);
    _syncPolling();
  }

  @override
  void didUpdateWidget(_PlayerView oldWidget) {
    super.didUpdateWidget(oldWidget);
    final previous = oldWidget.data.video;

    // Le démarrage du lecteur quand la conversion se termine est porté par
    // `build` : il observe `mediaControllerProvider` dès que la vidéo est
    // lisible.
    // Résumé fraîchement généré → on recharge son contenu.
    if (previous.summaryStatus != _video.summaryStatus && _video.hasSummary) {
      ref.invalidate(summaryProvider(_video.id));
    }
    _syncPolling();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    switch (state) {
      case AppLifecycleState.resumed:
        _syncPolling();
      case AppLifecycleState.inactive:
      case AppLifecycleState.paused:
      case AppLifecycleState.detached:
      case AppLifecycleState.hidden:
        // Économie batterie : pas de polling en arrière-plan, et la position
        // est écrite immédiatement (PLAY-08).
        _pollTimer?.cancel();
        _pollTimer = null;
        unawaited(_media?.flushProgress());
    }
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _pollTimer?.cancel();
    _tabs.dispose();
    // Le flush puis la libération du média sont portés par le `ref.onDispose`
    // de `mediaControllerProvider`.
    super.dispose();
  }

  void _syncPolling() {
    final shouldPoll = _video.hasRunningAiJob;
    if (!shouldPoll) {
      _pollTimer?.cancel();
      _pollTimer = null;
      return;
    }
    _pollTimer ??= Timer.periodic(
      AppConstants.jobPollInterval,
      (_) => ref.invalidate(playerContextProvider(widget.args)),
    );
  }

  Future<void> _runAiAction(
    Future<VideoItem> Function() action,
    String failureLabel,
  ) async {
    setState(() {
      _aiBusy = true;
      _aiError = null;
    });
    try {
      await action();
      ref.invalidate(playerContextProvider(widget.args));
    } catch (e) {
      if (mounted) setState(() => _aiError = '$failureLabel : $e');
    } finally {
      if (mounted) setState(() => _aiBusy = false);
    }
  }

  void _transcribe() => _runAiAction(
    () => ref.read(videoRepositoryProvider).startTranscription(_video.id),
    'Échec du lancement de la transcription',
  );

  void _generateSummary() => _runAiAction(
    () => ref.read(videoRepositoryProvider).generateSummary(_video.id),
    'Échec de la génération du résumé',
  );

  void _retryConversion() => _runAiAction(
    () => ref.read(videoRepositoryProvider).startConversion(_video.id),
    'Échec du lancement de la conversion',
  );

  void _goToVideo(VideoItem target) {
    context.pushReplacement(
      '/player/${target.id}?formationId=${widget.data.formation.id}',
    );
  }

  void _goBack() {
    if (context.canPop()) {
      context.pop();
    } else {
      context.go('/formation/${widget.data.formation.id}');
    }
  }

  @override
  Widget build(BuildContext context) {
    final data = widget.data;
    final theme = Theme.of(context);
    // `Scaffold` retire l'inset clavier du `MediaQuery` de son body : la
    // détection doit donc se faire ici, au-dessus de lui.
    final keyboardOpen = MediaQuery.viewInsetsOf(context).bottom > 0;

    // Le lecteur n'est construit qu'une fois le média converti : observer le
    // provider ici suffit à le démarrer dès que la vidéo devient lisible.
    final media = data.video.isPlayable
        ? ref.watch(mediaControllerProvider(widget.args)).value
        : null;

    return Scaffold(
      appBar: AppBar(
        leading: BackButton(onPressed: _goBack),
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              data.formation.name,
              style: theme.textTheme.bodySmall,
              overflow: TextOverflow.ellipsis,
            ),
            Text(
              data.video.title,
              style: theme.textTheme.titleMedium,
              overflow: TextOverflow.ellipsis,
            ),
          ],
        ),
        actions: [
          IconButton(
            tooltip: 'Assistant de la formation',
            onPressed: () =>
                context.push('/formation/${data.formation.id}/assistant'),
            icon: const Icon(Icons.smart_toy_outlined),
          ),
          const SettingsButton(),
        ],
      ),
      body: SafeArea(
        child: OrientationBuilder(
          builder: (context, orientation) {
            final isWide =
                orientation == Orientation.landscape &&
                MediaQuery.sizeOf(context).width >= 600;
            if (isWide) {
              // Paysage : média à gauche, panneaux à droite (9.2).
              return Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    child: SingleChildScrollView(
                      child: Column(children: _mediaSection(media)),
                    ),
                  ),
                  const VerticalDivider(width: 1),
                  Expanded(child: _panels(media)),
                ],
              );
            }
            // Clavier ouvert (saisie d'une note) : le média est masqué pour
            // laisser la place aux panneaux, la lecture continue.
            return Column(
              children: [
                Offstage(
                  offstage: keyboardOpen,
                  child: Column(children: _mediaSection(media)),
                ),
                Expanded(child: _panels(media)),
              ],
            );
          },
        ),
      ),
      // Barre précédent/suivant escamotée pendant la saisie : elle mangerait
      // 64 px juste au-dessus du clavier.
      bottomNavigationBar:
          keyboardOpen || (data.previousVideo == null && data.nextVideo == null)
          ? null
          : _NavigationBar(
              previous: data.previousVideo,
              next: data.nextVideo,
              onSelect: _goToVideo,
            ),
    );
  }

  List<Widget> _mediaSection(MediaController? media) {
    return [
      _MediaArea(
        video: _video,
        controller: media,
        busy: _aiBusy,
        onRetryConversion: _retryConversion,
      ),
      PlayerProgressBar(controller: media, fallbackDuration: _video.duration),
      AiActionBar(
        video: _video,
        busy: _aiBusy,
        errorMessage: _aiError,
        onTranscribe: _transcribe,
        onGenerateSummary: _generateSummary,
        onOpenSummary: () => _tabs.animateTo(_summaryTab),
      ),
    ];
  }

  Widget _panels(MediaController? media) {
    final documents = widget.data.videoDocuments;

    return Column(
      children: [
        TabBar(
          controller: _tabs,
          tabs: [
            const Tab(text: 'Notes'),
            const Tab(text: 'Résumé'),
            Tab(
              text: documents.isEmpty
                  ? 'Documents'
                  : 'Documents (${documents.length})',
            ),
          ],
        ),
        Expanded(
          child: TabBarView(
            controller: _tabs,
            children: [
              NotesPanel(videoId: _video.id, playback: media),
              SummaryPanel(
                video: _video,
                busy: _aiBusy,
                onGenerate: _generateSummary,
              ),
              DocumentsList(
                documents: documents,
                emptyMessage: 'Aucun document associé à ce média.',
              ),
            ],
          ),
        ),
      ],
    );
  }
}

/// Zone média : lecteur, ou message de conversion / d'échec (PLAY-19, PLAY-20).
class _MediaArea extends StatelessWidget {
  const _MediaArea({
    required this.video,
    required this.controller,
    required this.busy,
    required this.onRetryConversion,
  });

  final VideoItem video;
  final MediaController? controller;
  final bool busy;
  final VoidCallback onRetryConversion;

  @override
  Widget build(BuildContext context) {
    if (video.isConverting) {
      final job = video.activeJob(JobKind.mediaConversion);
      return _Placeholder(
        icon: Icons.hourglass_top,
        title:
            job?.label('Conversion du média en cours…') ??
            'Conversion du média en cours…',
        message: job?.message,
        showSpinner: true,
      );
    }

    if (video.conversionFailed) {
      return _Placeholder(
        icon: Icons.error_outline,
        title: 'La conversion du média a échoué.',
        message: 'Le média n’est pas lisible pour le moment.',
        action: FilledButton.tonalIcon(
          onPressed: busy ? null : onRetryConversion,
          icon: const Icon(Icons.refresh),
          label: const Text('Relancer la conversion'),
        ),
      );
    }

    final controller = this.controller;
    if (controller == null) {
      return const AspectRatio(
        aspectRatio: 16 / 9,
        child: Center(child: CircularProgressIndicator()),
      );
    }

    return MediaPlayerView(controller: controller, title: video.title);
  }
}

class _Placeholder extends StatelessWidget {
  const _Placeholder({
    required this.icon,
    required this.title,
    this.message,
    this.action,
    this.showSpinner = false,
  });

  final IconData icon;
  final String title;
  final String? message;
  final Widget? action;
  final bool showSpinner;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return AspectRatio(
      aspectRatio: 16 / 9,
      child: ColoredBox(
        color: theme.colorScheme.surfaceContainerHighest,
        child: Center(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                if (showSpinner)
                  const CircularProgressIndicator()
                else
                  Icon(icon, size: 32),
                const SizedBox(height: 12),
                Text(
                  title,
                  textAlign: TextAlign.center,
                  style: theme.textTheme.titleSmall,
                ),
                if (message != null && message!.isNotEmpty) ...[
                  const SizedBox(height: 4),
                  Text(
                    message!,
                    textAlign: TextAlign.center,
                    style: theme.textTheme.bodySmall,
                  ),
                ],
                if (action != null) ...[const SizedBox(height: 12), action!],
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _NavigationBar extends StatelessWidget {
  const _NavigationBar({
    required this.previous,
    required this.next,
    required this.onSelect,
  });

  final VideoItem? previous;
  final VideoItem? next;
  final void Function(VideoItem video) onSelect;

  @override
  Widget build(BuildContext context) {
    final previous = this.previous;
    final next = this.next;

    return BottomAppBar(
      height: 64,
      padding: const EdgeInsets.symmetric(horizontal: 8),
      child: Row(
        children: [
          Expanded(
            child: TextButton.icon(
              onPressed: previous == null ? null : () => onSelect(previous),
              icon: const Icon(Icons.skip_previous),
              label: Text(
                previous?.title ?? 'Précédent',
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
            ),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: FilledButton.icon(
              onPressed: next == null ? null : () => onSelect(next),
              iconAlignment: IconAlignment.end,
              icon: const Icon(Icons.skip_next),
              label: Text(
                next?.title ?? 'Suivant',
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
