import 'package:e_learning_mobile/data/models/models.dart';
import 'package:e_learning_mobile/data/repositories/usage_repository.dart';
import 'package:e_learning_mobile/features/usage/widgets/usage_sheet.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

class _MockUsageRepository extends Mock implements UsageRepository {}

Map<String, dynamic> _totals(int calls, int prompt, int completion) => {
  'calls': calls,
  'prompt_tokens': prompt,
  'completion_tokens': completion,
  'total_tokens': prompt + completion,
};

/// Réponse `GET /usage` telle que l'API la produit.
Map<String, dynamic> _payload(int days, {bool empty = false}) {
  final today = DateTime.utc(2026, 9, 26);
  return {
    'days': days,
    'period': empty ? _totals(0, 0, 0) : _totals(3, 1000, 380),
    'all_time': empty ? _totals(0, 0, 0) : _totals(10, 5000, 1200),
    'by_kind': empty
        ? []
        : [
            {'key': 'summary', ..._totals(1, 900, 300)},
            {'key': 'chat', ..._totals(2, 100, 80)},
          ],
    'by_model': [],
    'daily': [
      for (var i = days - 1; i >= 0; i--)
        {
          'day': today
              .subtract(Duration(days: i))
              .toIso8601String()
              .substring(0, 10),
          ...(i == 0 && !empty ? _totals(3, 1000, 380) : _totals(0, 0, 0)),
        },
    ],
  };
}

void main() {
  late _MockUsageRepository repo;

  setUp(() {
    repo = _MockUsageRepository();
    when(() => repo.getUsage(any())).thenAnswer(
      (inv) async => UserTokenUsage.fromJson(
        _payload(inv.positionalArguments.first as int),
      ),
    );
  });

  Future<void> pumpSheet(WidgetTester tester, {Size? size}) async {
    if (size != null) {
      tester.view.devicePixelRatio = 1;
      tester.view.physicalSize = size;
      addTearDown(tester.view.reset);
    }
    await tester.pumpWidget(
      ProviderScope(
        overrides: [usageRepositoryProvider.overrideWithValue(repo)],
        child: const MaterialApp(home: Scaffold(body: UsageSheet())),
      ),
    );
    await tester.pumpAndSettle();
  }

  test('UserTokenUsage.fromJson lit totaux, ventilation et série', () {
    final usage = UserTokenUsage.fromJson(_payload(7));

    expect(usage.days, 7);
    expect(usage.period.totalTokens, 1380);
    expect(usage.allTime.calls, 10);
    expect(usage.byKind.map((b) => b.key), ['summary', 'chat']);
    expect(usage.daily, hasLength(7));
    expect(usage.daily.last.totals.totalTokens, 1380);
  });

  testWidgets('affiche les totaux et la répartition sur 30 jours', (
    tester,
  ) async {
    await pumpSheet(tester);

    verify(() => repo.getUsage(30)).called(1);
    expect(find.text('Sur 30 jours'), findsOneWidget);
    expect(find.text('1 380'), findsOneWidget);
    expect(find.text('Résumés de vidéos'), findsOneWidget);
    expect(find.text('Assistant formation'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('changer de fenêtre recharge la période', (tester) async {
    await pumpSheet(tester);

    await tester.tap(find.text('7 j'));
    await tester.pumpAndSettle();

    verify(() => repo.getUsage(7)).called(1);
    expect(find.text('Sur 7 jours'), findsOneWidget);
  });

  testWidgets('sans consommation : message dédié, pas de graphique', (
    tester,
  ) async {
    when(() => repo.getUsage(any())).thenAnswer(
      (_) async => UserTokenUsage.fromJson(_payload(30, empty: true)),
    );

    await pumpSheet(tester);

    expect(
      find.text('Aucune consommation sur les 30 derniers jours.'),
      findsOneWidget,
    );
    expect(find.text('Par jour'), findsNothing);
  });

  testWidgets('téléphone étroit, 90 jours : rien ne déborde', (tester) async {
    await pumpSheet(tester, size: const Size(320, 640));

    await tester.tap(find.text('90 j'));
    await tester.pumpAndSettle();

    expect(tester.takeException(), isNull);
  });
}
