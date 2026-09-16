import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../core/auth/auth_controller.dart';
import '../features/assistant/widgets/assistant_sheet.dart';
import '../features/auth/screens/auth_screen.dart';
import '../features/catalog/screens/catalog_screen.dart';
import '../features/formation_detail/screens/formation_detail_screen.dart';
import '../features/player/screens/player_screen.dart';

final _rootNavigatorKey = GlobalKey<NavigatorState>();

final routerProvider = Provider<GoRouter>((ref) {
  final auth = ref.watch(authControllerProvider);

  return GoRouter(
    navigatorKey: _rootNavigatorKey,
    initialLocation: '/',
    refreshListenable: _AuthRefresh(ref),
    redirect: (context, state) {
      final loggingIn = state.matchedLocation == '/auth';
      if (auth.isLoading) return null;
      if (!auth.isAuthenticated && !loggingIn) return '/auth';
      if (auth.isAuthenticated && loggingIn) return '/';
      return null;
    },
    routes: [
      GoRoute(path: '/auth', builder: (context, state) => const AuthScreen()),
      GoRoute(path: '/', builder: (context, state) => const CatalogScreen()),
      GoRoute(
        path: '/formation/:formationId',
        builder: (context, state) {
          final id = state.pathParameters['formationId']!;
          return FormationDetailScreen(formationId: id);
        },
        routes: [
          GoRoute(
            path: 'assistant',
            builder: (context, state) {
              final id = state.pathParameters['formationId']!;
              return AssistantScreen(formationId: id);
            },
          ),
        ],
      ),
      GoRoute(
        path: '/player/:videoId',
        builder: (context, state) {
          final videoId = state.pathParameters['videoId']!;
          final formationId = state.uri.queryParameters['formationId'];
          return PlayerScreen(videoId: videoId, formationId: formationId);
        },
      ),
    ],
  );
});

class _AuthRefresh extends ChangeNotifier {
  _AuthRefresh(this.ref) {
    ref.listen(authControllerProvider, (_, _) => notifyListeners());
  }

  final Ref ref;
}
