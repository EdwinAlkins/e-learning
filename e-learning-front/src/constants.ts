/** Intervalle de polling pour les jobs (conversion, transcription, résumé). */
export const POLLING_INTERVAL_MS = 3000;

/** Durée d'affichage des snackbars de feedback. */
export const SNACKBAR_DURATION_MS = 2000;

/** Intervalle maximal entre deux sauvegardes de progression lecteur. */
export const PROGRESS_SAVE_INTERVAL_MS = 5000;

/** Extensions documents acceptées (aligné API ``DOCUMENT_EXTS``). */
export const DOCUMENT_ACCEPT_EXTENSIONS = [
  '.pdf',
  '.md',
  '.txt',
  '.csv',
  '.doc',
  '.docx',
  '.ppt',
  '.pptx',
  '.xls',
  '.xlsx',
  '.odt',
  '.ods',
  '.odp',
  '.png',
  '.jpg',
  '.jpeg',
  '.webp',
  '.gif',
  '.svg',
] as const;

export const DOCUMENT_ACCEPT_ATTR = [
  ...DOCUMENT_ACCEPT_EXTENSIONS,
  'application/pdf',
  'image/png',
  'image/jpeg',
  'image/webp',
  'image/gif',
  'image/svg+xml',
].join(',');

export function isAllowedDocumentFilename(filename: string): boolean {
  const lower = filename.toLowerCase();
  return DOCUMENT_ACCEPT_EXTENSIONS.some((ext) => lower.endsWith(ext));
}

/** Politique de mot de passe (alignée API ``application/user/passwords.py``). */
export const PASSWORD_MIN_LENGTH = 8;
export const PASSWORD_MAX_LENGTH = 128;
