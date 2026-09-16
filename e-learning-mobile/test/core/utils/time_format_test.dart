import 'package:e_learning_mobile/core/utils/time_format.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('formatDuration', () {
    test('formate en mm:ss et hh:mm:ss', () {
      expect(formatDuration(65), '01:05');
      expect(formatDuration(3661), '01:01:01');
    });

    test('borne les valeurs négatives et non finies', () {
      expect(formatDuration(-10), '00:00');
      expect(formatDuration(double.nan), '00:00');
      expect(formatDuration(double.infinity), '00:00');
    });
  });

  group('formatCompactDuration', () {
    test('formate en secondes, minutes et heures', () {
      expect(formatCompactDuration(45), '45 s');
      expect(formatCompactDuration(2700), '45 min');
      expect(formatCompactDuration(7500), '2h05');
    });
  });

  group('percentOf', () {
    test('calcule et borne le pourcentage', () {
      expect(percentOf(30, 120), 25);
      expect(percentOf(150, 120), 100);
      expect(percentOf(10, 0), 0);
    });
  });

  test('formatDateTime rend une date lisible et tolère null', () {
    final date = DateTime.utc(2025, 3, 12, 14, 5).toLocal();
    expect(
      formatDateTime(date),
      '12/03/2025 ${date.hour.toString().padLeft(2, '0')}:05',
    );
    expect(formatDateTime(null), '');
  });
}
