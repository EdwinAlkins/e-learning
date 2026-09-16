import 'dart:async';

/// Debounce avec [maxWait] optionnel.
///
/// L'action est retardée de [delay] après le dernier appel, mais jamais
/// repoussée au-delà de [maxWait] depuis le premier appel en attente. Sans
/// [maxWait], la sauvegarde de progression ne partirait jamais pendant une
/// lecture continue (le lecteur émet une position toutes les ~200 ms).
class Debouncer {
  Debouncer(this.delay, {this.maxWait});

  final Duration delay;
  final Duration? maxWait;

  Timer? _timer;
  DateTime? _pendingSince;

  void call(void Function() action) {
    final now = DateTime.now();
    _pendingSince ??= now;

    final wait = maxWait;
    if (wait != null && now.difference(_pendingSince!) >= wait) {
      _run(action);
      return;
    }

    _timer?.cancel();
    _timer = Timer(delay, () => _run(action));
  }

  void _run(void Function() action) {
    cancel();
    action();
  }

  void cancel() {
    _timer?.cancel();
    _timer = null;
    _pendingSince = null;
  }

  void dispose() => cancel();
}
