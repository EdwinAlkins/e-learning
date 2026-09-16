import { spawn } from 'node:child_process';
import { access, mkdir, readFile, writeFile } from 'node:fs/promises';
import { openAsBlob } from 'node:fs';
import { createHash } from 'node:crypto';
import { join } from 'node:path';
import {
  API, FFMPEG, SEED_MEDIA_DIR, STATE_FILE, OUT, api, fail,
} from './config.mjs';
import { DOCUMENTS, FORMATIONS, MAIN_FORMATION } from './seed-content.mjs';

// Crée les formations de démonstration via l'API, comme le ferait le studio :
// médias (cartons titres générés par ffmpeg), résumés, documents, notes et
// progression d'un apprenant de démo. Rejouable : une formation déjà présente
// est laissée telle quelle, sauf avec SEED_RESET=1.

const RESET = process.env.SEED_RESET === '1';

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

async function uploadDocument(uid, chapterId, doc, videoId) {
  const form = new FormData();
  form.append('title', doc.title);
  form.append('file', new Blob([DOCUMENTS[doc.file]], { type: 'text/markdown' }), `${doc.title}.md`);
  if (videoId) form.append('video_id', videoId);
  await api(`/chapters/${chapterId}/docs`, { uid, method: 'POST', form });
}

async function seedFormation(uid, font, spec) {
  const formation = await api('/formations', { uid, method: 'POST', body: { name: spec.name } });
  console.log(`+ ${spec.name}`);

  for (const [index, chapterSpec] of spec.chapters.entries()) {
    const chapter = await api(`/formations/${formation.id}/chapters`, {
      uid, method: 'POST', body: { name: chapterSpec.name },
    });
    console.log(`  + ${chapterSpec.name}`);

    for (const lesson of chapterSpec.lessons) {
      const file = await ensureMedia(font, spec, chapterSpec, index, lesson);
      const form = new FormData();
      form.append('title', lesson.title);
      form.append('file', await openAsBlob(file), file.split('/').pop());
      const video = await api(`/chapters/${chapter.id}/videos`, { uid, method: 'POST', form });

      if (lesson.summary) {
        await api(`/videos/${video.id}/summary`, { uid, method: 'PUT', body: { summary: lesson.summary } });
      }
      if (lesson.progress > 0) {
        await api(`/progress/${video.id}`, {
          uid, method: 'POST', body: { last_position: Math.floor(lesson.duration * lesson.progress) },
        });
      }
      for (const note of lesson.notes ?? []) {
        await api(`/notes/${video.id}`, { uid, method: 'POST', body: { timecode: note.at, content: note.content } });
      }
      for (const doc of lesson.documents ?? []) {
        await uploadDocument(uid, chapter.id, doc, video.id);
      }
      console.log(`    + ${lesson.title}`);
    }

    for (const doc of chapterSpec.documents ?? []) {
      await uploadDocument(uid, chapter.id, doc);
    }
  }
  return formation;
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

const uid = process.env.DEMO_UID
  ?? state.uid
  ?? (await api('/auth/generate', { method: 'POST' })).uid;

const font = await findFont();
const { formations: existing } = await api('/formations', { uid });
let main = existing.find((f) => f.name === MAIN_FORMATION);

for (const spec of FORMATIONS) {
  const found = existing.find((f) => f.name === spec.name);
  if (found && !RESET) {
    console.log(`= ${spec.name} (déjà présente, SEED_RESET=1 pour la recréer)`);
    continue;
  }
  if (found) {
    await api(`/formations/${found.id}`, { uid, method: 'DELETE' });
    console.log(`- ${spec.name}`);
  }
  const created = await seedFormation(uid, font, spec);
  if (spec.name === MAIN_FORMATION) main = created;
}

if (main) {
  try {
    await api(`/formations/${main.id}/index`, { uid, method: 'POST' });
    console.log('~ indexation de l\'assistant lancée (worker, Qdrant et embeddings requis)');
  } catch (error) {
    console.warn(`! indexation non lancée : ${error.message}`);
  }
}

const lesson = FORMATIONS.find((f) => f.name === MAIN_FORMATION)
  .chapters.flatMap((c) => c.lessons).find((l) => l.lesson).title;

await mkdir(OUT, { recursive: true });
await writeFile(STATE_FILE, `${JSON.stringify({ api: API, uid, formation: MAIN_FORMATION, lesson }, null, 2)}\n`);
console.log(`\n✓ démo prête — UID ${uid}\n  état écrit dans ${STATE_FILE}`);
