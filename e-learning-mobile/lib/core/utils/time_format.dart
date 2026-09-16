import 'package:intl/intl.dart';

/// `04:35` / `01:01:01` — durée de lecture.
String formatDuration(num seconds) {
  final total = seconds.isFinite ? seconds.round().clamp(0, 86400 * 7) : 0;
  final h = total ~/ 3600;
  final m = (total % 3600) ~/ 60;
  final s = total % 60;
  if (h > 0) {
    return '${h.toString().padLeft(2, '0')}:'
        '${m.toString().padLeft(2, '0')}:'
        '${s.toString().padLeft(2, '0')}';
  }
  return '${m.toString().padLeft(2, '0')}:'
      '${s.toString().padLeft(2, '0')}';
}

String formatTimecode(num seconds) => formatDuration(seconds);

/// `2h05` / `45 min` — durée cumulée (listes, chapitres).
String formatCompactDuration(num seconds) {
  final total = seconds.isFinite ? seconds.round().clamp(0, 86400 * 7) : 0;
  if (total < 60) return '$total s';
  final h = total ~/ 3600;
  final m = (total % 3600) ~/ 60;
  if (h > 0) return '${h}h${m.toString().padLeft(2, '0')}';
  return '$m min';
}

final _dateFormat = DateFormat('dd/MM/yyyy HH:mm');

/// `12/03/2025 14:05` — date de création d'une note.
String formatDateTime(DateTime? value) {
  if (value == null) return '';
  return _dateFormat.format(value.toLocal());
}

/// Pourcentage borné 0-100 affiché sans décimale.
int percentOf(num position, num total) {
  if (total <= 0) return 0;
  return ((position / total) * 100).round().clamp(0, 100);
}
