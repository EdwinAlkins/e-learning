import 'dart:async';
import 'dart:io' show Platform;

import 'package:audio_session/audio_session.dart';
import 'package:chewie/chewie.dart';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter/material.dart';
import 'package:just_audio/just_audio.dart';
import 'package:media_kit/media_kit.dart' as mk;
import 'package:media_kit_video/media_kit_video.dart' as mkv;
import 'package:video_player/video_player.dart';

import '../../../config/constants.dart';
import '../../../core/utils/debounce.dart';

/// `video_player` / `just_audio` n'ont pas d'implémentation desktop : sur
/// Linux, Windows et macOS la lecture passe par `media_kit` (libmpv).
bool get usesMediaKitBackend =>
    !kIsWeb && (Platform.isLinux || Platform.isWindows || Platform.isMacOS);

/// Ce que les panneaux (notes, barre de progression) attendent du lecteur,
/// sans dépendre de son implémentation vidéo ou audio.
abstract class PlaybackHandle implements Listenable {
  double get positionSeconds;
  double get durationSeconds;
  bool get isPlaying;
  Future<void> seekTo(double seconds);
}

/// Pilote la lecture d'un média (vidéo via `video_player`/`chewie`, audio via
/// `just_audio`) et la sauvegarde de progression associée.
class MediaController extends ChangeNotifier implements PlaybackHandle {
  MediaController({
    required this.videoId,
    required this.isAudio,
    required this.streamUrl,
    required this.headers,
    required this.onSaveProgress,
    this.fallbackDuration = 0,
  });

  final String videoId;
  final bool isAudio;
  final String streamUrl;
  final Map<String, String> headers;

  /// Persistance de la position (POST /progress/{videoId}).
  final Future<void> Function(double position) onSaveProgress;

  /// Durée connue via le catalogue, utilisée tant que le média n'est pas prêt.
  final double fallbackDuration;

  VideoPlayerController? _videoController;
  ChewieController? _chewieController;
  AudioPlayer? _audioPlayer;
  mk.Player? _mkPlayer;
  mkv.VideoController? _mkVideoController;
  final List<StreamSubscription<dynamic>> _subscriptions = [];

  // Debounce 500 ms, mais au plus 5 s sans écriture pendant une lecture continue.
  final _saveDebouncer = Debouncer(
    AppConstants.progressDebounce,
    maxWait: AppConstants.progressMaxWait,
  );

  bool _disposed = false;
  bool _initializing = true;
  String? _error;
  Duration _position = Duration.zero;
  Duration _duration = Duration.zero;
  bool _isPlaying = false;
  bool _isBuffering = false;
  double _speed = 1.0;

  bool get isInitializing => _initializing;
  String? get error => _error;
  bool get isReady => !_initializing && _error == null;
  bool get isBuffering => _isBuffering;
  double get speed => _speed;
  Duration get position => _position;
  Duration get duration => _duration;
  ChewieController? get chewieController => _chewieController;

  /// Non nul uniquement sur desktop : rendu via le widget `Video` de media_kit.
  mkv.VideoController? get mediaKitController => _mkVideoController;

  bool get usesMediaKit => usesMediaKitBackend;

  @override
  bool get isPlaying => _isPlaying;

  @override
  double get positionSeconds => _position.inMilliseconds / 1000.0;

  @override
  double get durationSeconds {
    final seconds = _duration.inMilliseconds / 1000.0;
    return seconds > 0 ? seconds : fallbackDuration;
  }

  static const List<double> speeds = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0];

  Future<void> initialize({double? startAt}) async {
    try {
      final start = (startAt != null && startAt > 0)
          ? Duration(milliseconds: (startAt * 1000).round())
          : Duration.zero;

      if (usesMediaKit) {
        await _initMediaKit(start);
      } else if (isAudio) {
        await _initAudio(start);
      } else {
        await _initVideo(start);
      }
      _position = start;
      _initializing = false;
      _notify();
    } catch (e) {
      _error = _readableError(e);
      _initializing = false;
      _notify();
    }
  }

  /// Backend desktop (libmpv) : gère indifféremment la vidéo et l'audio.
  Future<void> _initMediaKit(Duration start) async {
    final player = mk.Player();
    _mkPlayer = player;
    if (!isAudio) {
      _mkVideoController = mkv.VideoController(player);
    }

    _subscriptions.addAll([
      player.stream.position.listen((pos) {
        _position = pos;
        _notify();
        if (_isPlaying) _scheduleSave();
      }),
      player.stream.duration.listen((value) {
        _duration = value;
        _notify();
      }),
      player.stream.playing.listen((playing) {
        final wasPlaying = _isPlaying;
        _isPlaying = playing;
        if (wasPlaying && !playing) unawaited(flushProgress());
        _notify();
      }),
      player.stream.buffering.listen((buffering) {
        _isBuffering = buffering;
        _notify();
      }),
      player.stream.error.listen((message) {
        _error = _readableError(message);
        _notify();
      }),
    ]);

    await player.open(
      mk.Media(
        streamUrl,
        httpHeaders: headers.isEmpty ? null : headers,
        start: start > Duration.zero ? start : null,
      ),
      play: false,
    );
  }

  Future<void> _initAudio(Duration start) async {
    final session = await AudioSession.instance;
    // `music()` = catégorie playback : la lecture continue écran éteint / en fond.
    await session.configure(const AudioSessionConfiguration.music());

    final player = AudioPlayer();
    _audioPlayer = player;
    await player.setUrl(
      streamUrl,
      headers: headers.isEmpty ? null : headers,
      initialPosition: start == Duration.zero ? null : start,
    );

    _duration = player.duration ?? Duration.zero;
    _subscriptions.addAll([
      player.positionStream.listen((pos) {
        _position = pos;
        _notify();
        if (_isPlaying) _scheduleSave();
      }),
      player.durationStream.listen((value) {
        _duration = value ?? Duration.zero;
        _notify();
      }),
      player.playerStateStream.listen((state) {
        final wasPlaying = _isPlaying;
        _isPlaying = state.playing;
        _isBuffering =
            state.processingState == ProcessingState.loading ||
            state.processingState == ProcessingState.buffering;
        if (wasPlaying && !_isPlaying) {
          // PLAY-08 : écriture immédiate sur pause / fin de lecture.
          unawaited(flushProgress());
        }
        _notify();
      }),
    ]);
  }

  Future<void> _initVideo(Duration start) async {
    final controller = VideoPlayerController.networkUrl(
      Uri.parse(streamUrl),
      httpHeaders: headers,
      videoPlayerOptions: VideoPlayerOptions(allowBackgroundPlayback: false),
    );
    _videoController = controller;
    await controller.initialize();
    if (start > Duration.zero) {
      await controller.seekTo(start);
    }
    _duration = controller.value.duration;

    _chewieController = ChewieController(
      videoPlayerController: controller,
      autoPlay: false,
      looping: false,
      allowPlaybackSpeedChanging: true,
      playbackSpeeds: speeds,
      hideControlsTimer: const Duration(seconds: 3),
      errorBuilder: (context, message) => Center(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Text(message, textAlign: TextAlign.center),
        ),
      ),
    );
    controller.addListener(_onVideoTick);
  }

  void _onVideoTick() {
    final controller = _videoController;
    if (controller == null) return;
    final value = controller.value;

    if (value.hasError && _error == null) {
      _error = value.errorDescription ?? 'Lecture impossible';
      _notify();
      return;
    }

    final wasPlaying = _isPlaying;
    _position = value.position;
    _duration = value.duration;
    _isPlaying = value.isPlaying;
    _isBuffering = value.isBuffering;
    _speed = value.playbackSpeed;
    _notify();

    if (_isPlaying) {
      _scheduleSave();
    } else if (wasPlaying) {
      unawaited(flushProgress());
    }
  }

  void _scheduleSave() {
    _saveDebouncer(() => unawaited(_save(positionSeconds)));
  }

  /// Dernière position effectivement écrite, pour ne pas reposter la même.
  double? _lastSaved;

  Future<void> _save(double seconds) async {
    if (seconds <= 0 || seconds == _lastSaved) return;
    try {
      await onSaveProgress(seconds);
      _lastSaved = seconds;
    } catch (_) {
      // La progression n'est pas critique : on n'interrompt pas la lecture.
    }
  }

  /// Écrit la position courante sans attendre le debounce.
  Future<void> flushProgress() async {
    _saveDebouncer.cancel();
    await _save(positionSeconds);
  }

  @override
  Future<void> seekTo(double seconds) async {
    final max = durationSeconds;
    final clamped = max > 0
        ? seconds.clamp(0.0, max)
        : (seconds < 0 ? 0.0 : seconds);
    final target = Duration(milliseconds: (clamped * 1000).round());
    if (usesMediaKit) {
      await _mkPlayer?.seek(target);
    } else if (isAudio) {
      await _audioPlayer?.seek(target);
    } else {
      await _videoController?.seekTo(target);
    }
    _position = target;
    _notify();
  }

  Future<void> skip(Duration offset) =>
      seekTo(positionSeconds + offset.inSeconds);

  Future<void> togglePlay() async {
    if (usesMediaKit) {
      await _mkPlayer?.playOrPause();
      return;
    }
    if (isAudio) {
      final player = _audioPlayer;
      if (player == null) return;
      player.playing ? await player.pause() : unawaited(player.play());
    } else {
      final controller = _videoController;
      if (controller == null) return;
      controller.value.isPlaying
          ? await controller.pause()
          : await controller.play();
    }
  }

  Future<void> pause() async {
    if (usesMediaKit) {
      await _mkPlayer?.pause();
    } else if (isAudio) {
      await _audioPlayer?.pause();
    } else {
      await _videoController?.pause();
    }
  }

  Future<void> setSpeed(double value) async {
    _speed = value;
    if (usesMediaKit) {
      await _mkPlayer?.setRate(value);
    } else if (isAudio) {
      await _audioPlayer?.setSpeed(value);
    } else {
      await _videoController?.setPlaybackSpeed(value);
    }
    _notify();
  }

  void _notify() {
    if (_disposed) return;
    notifyListeners();
  }

  String _readableError(Object error) {
    final raw = error.toString();
    if (raw.contains('MissingPluginException')) {
      // video_player / just_audio n'ont pas d'implémentation desktop.
      return 'La lecture de médias n’est pas disponible sur cette plateforme. '
          'Testez sur Android ou iOS.';
    }
    if (raw.contains('SocketException') || raw.contains('Connection')) {
      return 'Média injoignable. Vérifiez votre connexion.';
    }
    return 'Impossible de lire ce média ($raw).';
  }

  @override
  void dispose() {
    _disposed = true;
    _saveDebouncer.dispose();
    for (final sub in _subscriptions) {
      unawaited(sub.cancel());
    }
    _subscriptions.clear();
    _videoController?.removeListener(_onVideoTick);
    _chewieController?.dispose();
    unawaited(_videoController?.dispose());
    unawaited(_audioPlayer?.dispose());
    unawaited(_mkPlayer?.dispose());
    super.dispose();
  }
}
