import axios from 'axios';
import type { ZodError } from 'zod';

export class ContractViolationError extends Error {
  readonly endpoint: string;
  readonly issues: ZodError['issues'];

  constructor(endpoint: string, error: ZodError) {
    super(`Réponse API invalide pour ${endpoint}`);
    this.name = 'ContractViolationError';
    this.endpoint = endpoint;
    this.issues = error.issues;
  }
}

/** Message lisible pour une erreur d'API (`detail` FastAPI, sinon `fallback`). */
export function apiErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof ContractViolationError) {
    return 'La réponse du serveur ne respecte pas le contrat attendu.';
  }

  if (axios.isAxiosError(error)) {
    if (error.response?.status === 429) {
      const retryAfter = Number(error.response.headers['retry-after']);
      const minutes = Number.isFinite(retryAfter) ? Math.ceil(retryAfter / 60) : null;
      return minutes
        ? `Trop de tentatives. Réessayez dans ${minutes} min.`
        : 'Trop de tentatives. Réessayez plus tard.';
    }
    const detail = error.response?.data?.detail;
    if (typeof detail === 'string') return detail;
    if (!error.response) return "Impossible de joindre l'API.";
  }
  return fallback;
}
