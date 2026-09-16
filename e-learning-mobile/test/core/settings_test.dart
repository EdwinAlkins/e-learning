import 'package:e_learning_mobile/core/settings/settings_controller.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('normalizeApiUrl', () {
    test('complète le schéma manquant', () {
      expect(normalizeApiUrl('192.168.1.10:8000'), 'http://192.168.1.10:8000');
    });

    test('retire les slashs finaux et les espaces', () {
      expect(normalizeApiUrl('  https://api.test/// '), 'https://api.test');
    });

    test('conserve un chemin de préfixe', () {
      expect(normalizeApiUrl('https://api.test/v1'), 'https://api.test/v1');
    });

    test('rejette une saisie vide ou sans hôte', () {
      expect(normalizeApiUrl(''), isNull);
      expect(normalizeApiUrl('   '), isNull);
      expect(normalizeApiUrl('http://'), isNull);
    });

    test('rejette un schéma non HTTP', () {
      expect(normalizeApiUrl('ftp://api.test'), isNull);
    });
  });
}
