import { fileURLToPath } from 'node:url';
import { dirname, isAbsolute, join, resolve } from 'node:path';
import { readFile } from 'node:fs/promises';

// Configuration partagée par les scripts. Rien ici n'est lié à un déploiement :
// FRONT_URL et API_URL désignent l'instance à filmer (un `npm run dev` local,
// un `docker compose up` jetable, une préproduction).
const HERE = dirname(fileURLToPath(import.meta.url));
const env = process.env;

const trimSlash = (url) => url.replace(/\/+$/, '');

export const FRONT = trimSlash(env.FRONT_URL ?? 'http://localhost:3000');
export const API = trimSlash(env.API_URL ?? 'http://localhost:8000');
export const MODE = env.MODE === 'video' ? 'video' : 'shots';
export const THEME = env.THEME === 'dark' ? 'dark' : 'light';
export const SCALE = Number(env.SCALE ?? 2);
export const FFMPEG = env.FFMPEG ?? 'ffmpeg';

// Question posée à l'assistant pendant la capture. ASK= (vide) pour sauter
// l'étape, par exemple sur une instance sans modèle de langage.
export const ASK = env.ASK ?? 'Que faut-il vérifier avant de passer en production ?';
export const ASK_TIMEOUT_MS = Number(env.ASK_TIMEOUT ?? 120) * 1000;

// Note tapée dans le lecteur pendant la capture vidéo, puis retirée via l'API :
// elle sert à filmer la prise de notes, pas à rester en base. Adaptez-la au
// sujet filmé, sinon la scène raconte autre chose que la formation à l'écran.
export const NOTE = env.NOTE
  ?? '**Rappel** : monter un volume pour tout ce qui doit survivre au conteneur.';

// Les sorties restent hors de l'index git (voir .gitignore).
const requestedOut = env.OUT ?? 'out';
export const OUT = isAbsolute(requestedOut) ? requestedOut : resolve(HERE, requestedOut);
export const SHOTS_DIR = join(OUT, 'shots');
export const VIDEO_DIR = join(OUT, 'video');
export const SEED_MEDIA_DIR = join(OUT, 'seed-media');
export const STATE_FILE = join(OUT, 'demo.json');
export const DOCS_MEDIA_DIR = resolve(HERE, '../../docs/assets/media');

export function fail(message) {
  console.error(`✗ ${message}`);
  process.exit(1);
}

/**
 * Compte et cible de la capture. L'environnement l'emporte sur l'état écrit
 * par `npm run seed`, ce qui permet de filmer une instance déjà peuplée :
 * DEMO_EMAIL, DEMO_PASSWORD, FORMATION (nom exact) et, facultatif, LESSON
 * (titre de la leçon). Le compte doit être administrateur pour filmer le studio.
 */
export async function loadDemo() {
  let state = {};
  try {
    state = JSON.parse(await readFile(STATE_FILE, 'utf8'));
  } catch {
    // pas encore de seed : l'environnement doit tout fournir
  }
  const email = env.DEMO_EMAIL ?? state.email;
  const password = env.DEMO_PASSWORD ?? state.password;
  const formation = env.FORMATION ?? state.formation;
  const lesson = env.LESSON ?? state.lesson;
  if (!email || !password || !formation) {
    fail('Aucune donnée de démo. Lancez `npm run seed`, ou passez DEMO_EMAIL, DEMO_PASSWORD et FORMATION.');
  }
  return { email, password, formation, lesson };
}

/** Connexion par compte : renvoie le jeton à passer à `api()`. */
export async function login(email, password) {
  const { access_token: token } = await api('/auth/login', {
    method: 'POST',
    urlencoded: { username: email, password },
  });
  return token;
}

/** Appel JSON à l'API, authentifié par le jeton de `login()`. */
export async function api(path, { token, method = 'GET', body, form, urlencoded } = {}) {
  const headers = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  let payload;
  if (form) {
    payload = form;
  } else if (urlencoded) {
    payload = new URLSearchParams(urlencoded);
  } else if (body !== undefined) {
    headers['Content-Type'] = 'application/json';
    payload = JSON.stringify(body);
  }
  let response;
  try {
    response = await fetch(`${API}${path}`, { method, headers, body: payload });
  } catch (error) {
    fail(`API injoignable sur ${API} (${error.cause?.code ?? error.message}). Définissez API_URL.`);
  }
  if (!response.ok) {
    const detail = await response.text().catch(() => '');
    const error = new Error(`${method} ${path} → ${response.status} ${detail.slice(0, 300)}`);
    error.status = response.status;
    throw error;
  }
  if (response.status === 204) return null;
  const type = response.headers.get('content-type') ?? '';
  return type.includes('application/json') ? response.json() : response.text();
}

/** Toutes les vidéos d'une formation, dans l'ordre d'affichage. */
export function lessonsOf(formation) {
  return [...formation.chapters]
    .sort((a, b) => a.position - b.position)
    .flatMap((chapter) => [...chapter.videos].sort((a, b) => a.position - b.position)
      .map((video) => ({ ...video, chapter })));
}
