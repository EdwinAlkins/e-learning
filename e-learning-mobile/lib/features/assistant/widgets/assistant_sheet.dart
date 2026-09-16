import 'package:flutter/material.dart';
import 'package:flutter_markdown_plus/flutter_markdown_plus.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../../data/models/models.dart';
import '../../../data/repositories/formation_repository.dart';
import '../../../data/repositories/video_repository.dart';
import '../../settings/widgets/settings_sheet.dart';

class AssistantScreen extends ConsumerStatefulWidget {
  const AssistantScreen({super.key, required this.formationId});

  final String formationId;

  @override
  ConsumerState<AssistantScreen> createState() => _AssistantScreenState();
}

class _AssistantScreenState extends ConsumerState<AssistantScreen> {
  final _controller = TextEditingController();
  AskFormationResponse? _response;
  bool _loading = false;
  String? _error;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _ask() async {
    final question = _controller.text.trim();
    if (question.isEmpty) return;
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final response = await ref
          .read(formationRepositoryProvider)
          .ask(widget.formationId, question);
      setState(() => _response = response);
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Assistant IA'),
        actions: const [SettingsButton()],
      ),
      body: Column(
        children: [
          Expanded(
            child: ListView(
              keyboardDismissBehavior: ScrollViewKeyboardDismissBehavior.onDrag,
              padding: const EdgeInsets.all(16),
              children: [
                if (_error != null)
                  Material(
                    color: Theme.of(context).colorScheme.errorContainer,
                    borderRadius: BorderRadius.circular(12),
                    child: Padding(
                      padding: const EdgeInsets.all(12),
                      child: Text(_error!),
                    ),
                  ),
                if (_response != null) ...[
                  MarkdownBody(data: _response!.answer, selectable: true),
                  const SizedBox(height: 16),
                  if (_response!.citations.isNotEmpty)
                    Text(
                      'Sources',
                      style: Theme.of(context).textTheme.titleSmall,
                    ),
                  ..._response!.citations.map((c) {
                    return ListTile(
                      contentPadding: EdgeInsets.zero,
                      title: Text(c.title),
                      subtitle: Text(c.excerpt, maxLines: 3),
                      onTap: () async {
                        if (c.videoId != null) {
                          context.push(
                            '/player/${c.videoId}?formationId=${widget.formationId}',
                          );
                        } else if (c.documentId != null) {
                          final url = ref
                              .read(documentRepositoryProvider)
                              .fileUrl(c.documentId!);
                          await launchUrl(
                            Uri.parse(url),
                            mode: LaunchMode.externalApplication,
                          );
                        }
                      },
                    );
                  }),
                ] else if (!_loading)
                  const Text(
                    'Posez une question sur le contenu de la formation.',
                  ),
                if (_loading)
                  const Padding(
                    padding: EdgeInsets.all(24),
                    child: Center(child: CircularProgressIndicator()),
                  ),
              ],
            ),
          ),
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _controller,
                      decoration: const InputDecoration(
                        hintText: 'Votre question…',
                        border: OutlineInputBorder(),
                      ),
                      minLines: 1,
                      maxLines: 4,
                      onSubmitted: (_) => _ask(),
                    ),
                  ),
                  const SizedBox(width: 8),
                  IconButton.filled(
                    onPressed: _loading ? null : _ask,
                    icon: const Icon(Icons.send),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
