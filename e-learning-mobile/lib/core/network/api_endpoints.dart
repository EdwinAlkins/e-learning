class ApiEndpoints {
  static const health = '/health';
  static const authGenerate = '/auth/generate';
  static const authRestore = '/auth/restore';
  static const formations = '/formations';
  static String formation(String id) => '/formations/$id';
  static String formationAsk(String id) => '/formations/$id/ask';
  static String formationIndex(String id) => '/formations/$id/index';
  static String videoStream(String id) => '/videos/$id/stream';
  static String videoSummary(String id) => '/videos/$id/summary';
  static String videoSummaryGenerate(String id) =>
      '/videos/$id/summary/generate';
  static String videoTranscription(String id) => '/videos/$id/transcription';
  static String videoConversion(String id) => '/videos/$id/conversion';
  static String notes(String videoId) => '/notes/$videoId';
  static String note(String noteId) => '/notes/$noteId';
  static String progress(String videoId) => '/progress/$videoId';
  static String formationProgress(String formationId) =>
      '/progress/formation/$formationId';
  static const formationsProgress = '/progress/formations';
  static String chapterDocuments(String chapterId) =>
      '/docs/chapters/$chapterId';
  static String documentFile(String documentId, {bool download = false}) =>
      '/docs/$documentId/file${download ? '?download=true' : ''}';
}
