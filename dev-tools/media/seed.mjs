import { spawn } from 'node:child_process';
import { access, mkdir, readFile, writeFile } from 'node:fs/promises';
import { openAsBlob } from 'node:fs';
import { createHash, randomBytes } from 'node:crypto';
import { join } from 'node:path';
import {
  API, FFMPEG, SEED_MEDIA_DIR, STATE_FILE, OUT, api, fail, login,
} from './config.mjs';
import { DOCUMENTS, FORMATIONS, MAIN_FORMATION } from './seed-content.mjs';

// Crée les formations de démonstration via l'API, comme le ferait le studio :
// médias (cartons titres générés par ffmpeg), résumés, documents, notes et
// progression d'un compte de démo. Rejouable : une formation déjà présente
// est laissée telle quelle, sauf avec SEED_RESET=1.
//
// Le compte de démo (administrateur, pour filmer le studio) est créé avec les
// identifiants d'un administrateur existant, ADMIN_EMAIL et ADMIN_PASSWORD, lus
// dans l'environnement et jamais écrits. Son mot de passe, tiré au hasard, est
// conservé dans out/demo.json.
//
// Un historique de consommation IA fictif est enfin écrit directement en base
// (docker exec psql), pour que la page Consommation ait quelque chose à montrer.

const env = process.env;
const RESET = env.SEED_RESET === '1';
const DEMO_EMAIL = env.DEMO_EMAIL ?? 'demo@cladese.example';
const DEMO_NAME = 'Compte de démo';
const PG_CONTAINER = env.PG_CONTAINER ?? 'e-learning-postgres-1';
const USAGE_DAYS = Number(env.USAGE_DAYS ?? 90);

const FONT_CANDIDATES = [
  process.env.FONT,
  '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
  '/usr/share/fonts/TTF/DejaVuSans.ttf',
  '/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf',
  '/System/Library/Fonts/Supplemental/Arial.ttf',
  '/Library/Fonts/Arial.ttf',
].filter(Boolean);

async function exists(path) {
  try {
    await access(path);
    return true;
  } catch {
    return false;
  }
}

async function findFont() {
  for (const candidate of FONT_CANDIDATES) {
    if (await exists(candidate)) return candidate;
  }
  return fail('Aucune police TrueType trouvée pour les cartons titres. Passez FONT=/chemin/police.ttf.');
}

function run(command, args) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, { stdio: ['ignore', 'ignore', 'pipe'] });
    let stderr = '';
    child.stderr.on('data', (chunk) => { stderr += chunk; });
    child.on('error', (error) => reject(error.code === 'ENOENT'
      ? new Error(`${command} introuvable. Installez ffmpeg ou définissez FFMPEG.`)
      : error));
    child.on('close', (code) => (code === 0
      ? resolve()
      : reject(new Error(`${command} a échoué (${code}) :\n${stderr.slice(-1500)}`))));
  });
}

const slug = (text) => text.normalize('NFD').replace(/[̀-ͯ]/g, '')
  .toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');

// Les textes passent par des fichiers : aucun échappement de filtre ffmpeg à
// gérer pour les apostrophes, deux-points ou accents.
async function writeText(dir, name, text) {
  const path = join(dir, name);
  await writeFile(path, text, 'utf8');
  return path;
}

/** Génère (ou réutilise) le média d'une leçon. */
async function ensureMedia(font, formation, chapter, index, lesson) {
  const key = createHash('sha1')
    .update(JSON.stringify([formation.name, chapter.name, lesson.title, lesson.duration, lesson.audio]))
    .digest('hex').slice(0, 10);
  const ext = lesson.audio ? 'mp3' : 'mp4';
  const file = join(SEED_MEDIA_DIR, `${slug(lesson.title)}-${key}.${ext}`);
  if (await exists(file)) return file;

  const seconds = String(lesson.duration);
  if (lesson.audio) {
    await run(FFMPEG, [
      '-y', '-loglevel', 'error',
      '-f', 'lavfi', '-i', 'anullsrc=r=22050:cl=mono',
      '-t', seconds, '-c:a', 'libmp3lame', '-b:a', '32k', file,
    ]);
    return file;
  }

  const texts = join(SEED_MEDIA_DIR, `${key}-txt`);
  await mkdir(texts, { recursive: true });
  const top = await writeText(texts, 'top.txt', formation.name.toUpperCase());
  const title = await writeText(texts, 'title.txt', lesson.title);
  const sub = await writeText(texts, 'sub.txt', `Chapitre ${index + 1} · ${chapter.name}`);
  const clock = await writeText(texts, 'clock.txt', '%{eif:trunc(t/60):d:2}:%{eif:mod(t,60):d:2}');
  const titleSize = lesson.title.length > 30 ? 50 : 64;
  const q = (path) => `'${path.replace(/'/g, "'\\''")}'`;

  const filter = [
    'drawbox=x=0:y=0:w=16:h=ih:color=0x00c6fb:t=fill',
    'drawbox=x=90:y=ih-130:w=180:h=4:color=0x005bea:t=fill',
    `drawtext=fontfile=${q(font)}:textfile=${q(top)}:fontsize=26:fontcolor=0x7fb8ff:x=90:y=90`,
    `drawtext=fontfile=${q(font)}:textfile=${q(title)}:fontsize=${titleSize}:fontcolor=white:x=90:y=(h/2)-80`,
    `drawtext=fontfile=${q(font)}:textfile=${q(sub)}:fontsize=32:fontcolor=0xa9b8cc:x=90:y=(h/2)+20`,
    `drawtext=fontfile=${q(font)}:textfile=${q(clock)}:fontsize=28:fontcolor=0x7f8ea3:x=w-tw-90:y=h-110`,
  ].join(',');

  await run(FFMPEG, [
    '-y', '-loglevel', 'error',
    '-f', 'lavfi', '-i', `color=c=0x0b1f3a:s=1280x720:r=10:d=${seconds}`,
    '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo',
    '-vf', filter,
    '-t', seconds,
    '-c:v', 'libx264', '-preset', 'veryfast', '-tune', 'stillimage', '-crf', '30', '-pix_fmt', 'yuv420p',
    '-c:a', 'aac', '-b:a', '32k',
    '-movflags', '+faststart',
    file,
  ]);
  return file;
}

async function uploadDocument(token, chapterId, doc, videoId) {
  const form = new FormData();
  form.append('title', doc.title);
  form.append('file', new Blob([DOCUMENTS[doc.file]], { type: 'text/markdown' }), `${doc.title}.md`);
  if (videoId) form.append('video_id', videoId);
  await api(`/chapters/${chapterId}/docs`, { token, method: 'POST', form });
}

async function seedFormation(token, font, spec) {
  const formation = await api('/formations', { token, method: 'POST', body: { name: spec.name } });
  console.log(`+ ${spec.name}`);

  for (const [index, chapterSpec] of spec.chapters.entries()) {
    const chapter = await api(`/formations/${formation.id}/chapters`, {
      token, method: 'POST', body: { name: chapterSpec.name },
    });
    console.log(`  + ${chapterSpec.name}`);

    for (const lesson of chapterSpec.lessons) {
      const file = await ensureMedia(font, spec, chapterSpec, index, lesson);
      const form = new FormData();
      form.append('title', lesson.title);
      form.append('file', await openAsBlob(file), file.split('/').pop());
      const video = await api(`/chapters/${chapter.id}/videos`, { token, method: 'POST', form });

      if (lesson.summary) {
        await api(`/videos/${video.id}/summary`, { token, method: 'PUT', body: { summary: lesson.summary } });
      }
      if (lesson.progress > 0) {
        await api(`/progress/${video.id}`, {
          token, method: 'POST', body: { last_position: Math.floor(lesson.duration * lesson.progress) },
        });
      }
      for (const note of lesson.notes ?? []) {
        await api(`/notes/${video.id}`, { token, method: 'POST', body: { timecode: note.at, content: note.content } });
      }
      for (const doc of lesson.documents ?? []) {
        await uploadDocument(token, chapter.id, doc, video.id);
      }
      console.log(`    + ${lesson.title}`);
    }

    for (const doc of chapterSpec.documents ?? []) {
      await uploadDocument(token, chapter.id, doc);
    }
  }
  return formation;
}

/**
 * Renvoie un jeton du compte de démo, en le créant (ou en réinitialisant son
 * mot de passe) avec les identifiants administrateur si nécessaire.
 */
async function ensureDemoAccount(state) {
  let password = env.DEMO_PASSWORD ?? (state.email === DEMO_EMAIL ? state.password : undefined);
  if (password) {
    try {
      return { password, token: await login(DEMO_EMAIL, password) };
    } catch (error) {
      if (error.status !== 401) throw error;
    }
  }
  if (!env.ADMIN_EMAIL || !env.ADMIN_PASSWORD) {
    fail(`Compte ${DEMO_EMAIL} inaccessible. Passez ADMIN_EMAIL et ADMIN_PASSWORD (un administrateur existant) pour le créer.`);
  }
  const admin = await login(env.ADMIN_EMAIL, env.ADMIN_PASSWORD);
  password = env.DEMO_PASSWORD ?? randomBytes(18).toString('base64url');
  const { items: users } = await api('/admin/users?limit=200', { token: admin });
  const found = users.find((u) => u.email === DEMO_EMAIL);
  if (found) {
    await api(`/admin/users/${found.id}`, {
      token: admin, method: 'PATCH', body: { password, is_admin: true, is_active: true },
    });
    console.log(`~ ${DEMO_EMAIL} : mot de passe réinitialisé`);
  } else {
    await api('/admin/users', {
      token: admin,
      method: 'POST',
      body: { email: DEMO_EMAIL, password, full_name: DEMO_NAME, is_admin: true },
    });
    console.log(`+ compte ${DEMO_EMAIL}`);
  }
  return { password, token: await login(DEMO_EMAIL, password) };
}

function runWithInput(command, args, input) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, { stdio: ['pipe', 'ignore', 'pipe'] });
    let stderr = '';
    child.stderr.on('data', (chunk) => { stderr += chunk; });
    child.on('error', reject);
    child.on('close', (code) => (code === 0
      ? resolve()
      : reject(new Error(`${command} a échoué (${code}) : ${stderr.slice(-800)}`))));
    child.stdin.end(input);
  });
}

// Générateur pseudo-aléatoire à graine fixe : le même historique à chaque seed.
function mulberry32(seed) {
  return () => {
    seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/**
 * Historique fictif de consommation sur USAGE_DAYS jours, hors aujourd'hui :
 * questions à l'assistant en semaine, quelques résumés. Les lignes du jour
 * (vraies questions posées pendant la capture) ne sont pas touchées. Le modèle
 * affiché est le dernier réellement utilisé sur l'instance, pour ne pas faire
 * apparaître deux modèles dans le tableau.
 */
async function seedUsage(userId) {
  const rand = mulberry32(42);
  const between = (min, max) => Math.round(min + rand() * (max - min));
  const rows = [];
  for (let ago = USAGE_DAYS - 1; ago >= 1; ago -= 1) {
    const weekday = new Date(Date.now() - ago * 86400000).getDay();
    const weekend = weekday === 0 || weekday === 6;
    // Activité croissante sur la période, creuse le week-end.
    const ramp = 0.4 + 0.6 * (1 - ago / USAGE_DAYS);
    const questions = rand() < (weekend ? 0.2 : 0.8) ? between(1, weekend ? 3 : 9 * ramp + 1) : 0;
    const summaries = rand() < 0.18 ? between(1, 2) : 0;
    const at = () => `(current_date - ${ago}) + interval '${between(8 * 60, 21 * 60)} minutes'`;
    for (let i = 0; i < questions; i += 1) rows.push(['chat', between(1500, 3800), between(120, 480), at()]);
    for (let i = 0; i < summaries; i += 1) rows.push(['summary', between(5000, 12000), between(450, 950), at()]);
  }
  const values = rows.map(([kind, prompt, completion, at]) =>
    `(gen_random_uuid(), '${userId}', '${kind}', (select model from m), ${prompt}, ${completion}, ${at})`);
  const sql = `
begin;
delete from token_usage where user_id = '${userId}' and created_at < current_date;
with m as (select coalesce((select model from token_usage order by created_at desc limit 1), 'mistral-small') as model)
insert into token_usage (id, user_id, kind, model, prompt_tokens, completion_tokens, created_at)
values ${values.join(',\n')};
commit;
`;
  try {
    await runWithInput('docker', [
      'exec', '-i', PG_CONTAINER, 'sh', '-c',
      'psql -q -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"',
    ], sql);
    console.log(`~ consommation IA : ${rows.length} appels fictifs sur ${USAGE_DAYS} jours`);
  } catch (error) {
    console.warn(`! consommation non écrite (PG_CONTAINER=${PG_CONTAINER}) : ${error.message}`);
  }
}

// ── main ────────────────────────────────────────────────────────────────────
await mkdir(SEED_MEDIA_DIR, { recursive: true });
await api('/health');

let state = {};
try {
  state = JSON.parse(await readFile(STATE_FILE, 'utf8'));
} catch {
  // premier seed
}

const { password, token } = await ensureDemoAccount(state);
await mkdir(OUT, { recursive: true });
const lesson = FORMATIONS.find((f) => f.name === MAIN_FORMATION)
  .chapters.flatMap((c) => c.lessons).find((l) => l.lesson).title;
// Écrit dès maintenant : un seed interrompu ne perd pas le mot de passe.
await writeFile(STATE_FILE, `${JSON.stringify({
  api: API, email: DEMO_EMAIL, password, formation: MAIN_FORMATION, lesson,
}, null, 2)}\n`, { mode: 0o600 });

const font = await findFont();
const { formations: existing } = await api('/formations', { token });
let main = existing.find((f) => f.name === MAIN_FORMATION);

for (const spec of FORMATIONS) {
  const found = existing.find((f) => f.name === spec.name);
  if (found && !RESET) {
    console.log(`= ${spec.name} (déjà présente, SEED_RESET=1 pour la recréer)`);
    continue;
  }
  if (found) {
    await api(`/formations/${found.id}`, { token, method: 'DELETE' });
    console.log(`- ${spec.name}`);
  }
  const created = await seedFormation(token, font, spec);
  if (spec.name === MAIN_FORMATION) main = created;
}

if (main) {
  try {
    await api(`/formations/${main.id}/index`, { token, method: 'POST' });
    console.log('~ indexation de l\'assistant lancée (worker, Qdrant et embeddings requis)');
  } catch (error) {
    console.warn(`! indexation non lancée : ${error.message}`);
  }
}

const me = await api('/auth/me', { token });
await seedUsage(me.id);

console.log(`\n✓ démo prête — compte ${DEMO_EMAIL}\n  identifiants écrits dans ${STATE_FILE}`);
