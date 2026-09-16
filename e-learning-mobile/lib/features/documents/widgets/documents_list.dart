import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../../data/models/models.dart';
import '../../../data/repositories/video_repository.dart';

/// Liste de documents avec ouverture / téléchargement délégués au système.
class DocumentsList extends ConsumerWidget {
  const DocumentsList({
    super.key,
    required this.documents,
    this.emptyMessage = 'Aucun document.',
    this.padding = const EdgeInsets.only(bottom: 24),
  });

  final List<DocumentItem> documents;
  final String emptyMessage;
  final EdgeInsets padding;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    if (documents.isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Text(emptyMessage, textAlign: TextAlign.center),
        ),
      );
    }

    return ListView.builder(
      padding: padding,
      itemCount: documents.length,
      itemBuilder: (context, index) {
        final doc = documents[index];
        return ListTile(
          leading: Icon(documentIcon(doc)),
          title: Text(doc.title.isEmpty ? doc.filename : doc.title),
          subtitle: Text(
            [
              if (doc.filename.isNotEmpty) doc.filename,
              if (doc.mimeType != null && doc.mimeType!.isNotEmpty)
                doc.mimeType!,
            ].join(' · '),
          ),
          onTap: () => _launch(context, ref, doc, download: false),
          trailing: IconButton(
            tooltip: 'Télécharger',
            icon: const Icon(Icons.download_outlined),
            onPressed: () => _launch(context, ref, doc, download: true),
          ),
        );
      },
    );
  }

  Future<void> _launch(
    BuildContext context,
    WidgetRef ref,
    DocumentItem doc, {
    required bool download,
  }) async {
    final messenger = ScaffoldMessenger.of(context);
    final url = ref
        .read(documentRepositoryProvider)
        .fileUrl(doc.id, download: download);
    try {
      final ok = await launchUrl(
        Uri.parse(url),
        mode: LaunchMode.externalApplication,
      );
      if (!ok) {
        messenger.showSnackBar(
          SnackBar(
            content: Text(
              download
                  ? 'Impossible de télécharger le document'
                  : 'Impossible d’ouvrir le document',
            ),
          ),
        );
      }
    } catch (e) {
      messenger.showSnackBar(SnackBar(content: Text('Échec : $e')));
    }
  }
}

IconData documentIcon(DocumentItem doc) {
  final name = doc.filename.toLowerCase();
  final mime = (doc.mimeType ?? '').toLowerCase();
  if (mime.startsWith('image/') ||
      name.endsWith('.png') ||
      name.endsWith('.jpg') ||
      name.endsWith('.jpeg') ||
      name.endsWith('.webp') ||
      name.endsWith('.gif') ||
      name.endsWith('.svg')) {
    return Icons.image_outlined;
  }
  if (mime.contains('pdf') || name.endsWith('.pdf')) {
    return Icons.picture_as_pdf_outlined;
  }
  if (name.endsWith('.csv') ||
      name.endsWith('.xls') ||
      name.endsWith('.xlsx') ||
      name.endsWith('.ods')) {
    return Icons.table_chart_outlined;
  }
  if (name.endsWith('.ppt') ||
      name.endsWith('.pptx') ||
      name.endsWith('.odp')) {
    return Icons.slideshow_outlined;
  }
  if (name.endsWith('.md') || name.endsWith('.txt')) {
    return Icons.article_outlined;
  }
  return Icons.description_outlined;
}
