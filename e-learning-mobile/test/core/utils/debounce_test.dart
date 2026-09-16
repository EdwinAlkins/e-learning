import 'package:e_learning_mobile/core/utils/debounce.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('n’exécute qu’après le délai suivant le dernier appel', () async {
    final debouncer = Debouncer(const Duration(milliseconds: 50));
    var calls = 0;

    debouncer(() => calls++);
    debouncer(() => calls++);
    expect(calls, 0);

    await Future<void>.delayed(const Duration(milliseconds: 80));
    expect(calls, 1);
    debouncer.dispose();
  });

  test('maxWait force l’exécution pendant des appels continus', () async {
    final debouncer = Debouncer(
      const Duration(milliseconds: 50),
      maxWait: const Duration(milliseconds: 100),
    );
    var calls = 0;

    // Appels répétés plus rapides que le délai : sans maxWait, rien ne partirait.
    for (var i = 0; i < 12; i++) {
      debouncer(() => calls++);
      await Future<void>.delayed(const Duration(milliseconds: 20));
    }

    expect(calls, greaterThanOrEqualTo(1));
    debouncer.dispose();
  });

  test('cancel annule l’exécution en attente', () async {
    final debouncer = Debouncer(const Duration(milliseconds: 30));
    var calls = 0;

    debouncer(() => calls++);
    debouncer.cancel();

    await Future<void>.delayed(const Duration(milliseconds: 60));
    expect(calls, 0);
    debouncer.dispose();
  });
}
