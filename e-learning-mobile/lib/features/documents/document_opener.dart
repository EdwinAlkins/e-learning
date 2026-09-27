import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:open_filex/open_filex.dart';
import 'package:path_provider/path_provider.dart';

import '../../core/network/api_exception.dart';
import '../../data/repositories/video_repository.dart';

/// Récupère un document avec le jeton de session puis le confie à
/// l'application système.
///
/// [save] : copie durable (dossier Téléchargements de l'app) au lieu du cache.
Future<void> openDocument(
  BuildContext context,
  WidgetRef ref,
  String documentId, {
  bool save = false,
}) async {
  final messenger = ScaffoldMessenger.of(context);
  final repository = ref.read(documentRepositoryProvider);
  messenger.showSnackBar(
    SnackBar(
      content: Text(save ? 'Téléchargement…' : 'Ouverture…'),
      duration: const Duration(seconds: 1),
    ),
  );
  try {
    final directory = save
        ? (await getDownloadsDirectory() ??
              await getApplicationDocumentsDirectory())
        : Directory('${(await getTemporaryDirectory()).path}/documents');
    final path = await repository.downloadTo(documentId, directory);
    final result = await OpenFilex.open(path);
    messenger.hideCurrentSnackBar();
    if (save) {
      messenger.showSnackBar(SnackBar(content: Text('Enregistré : $path')));
    } else if (result.type != ResultType.done) {
      messenger.showSnackBar(
        const SnackBar(
          content: Text('Aucune application pour ouvrir ce document'),
        ),
      );
    }
  } on ApiException catch (e) {
    messenger.hideCurrentSnackBar();
    messenger.showSnackBar(SnackBar(content: Text(e.message)));
  } on FileSystemException catch (e) {
    messenger.hideCurrentSnackBar();
    messenger.showSnackBar(
      SnackBar(content: Text('Écriture du fichier impossible : ${e.message}')),
    );
  }
}
