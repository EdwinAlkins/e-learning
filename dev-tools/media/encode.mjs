import { spawn } from 'node:child_process';
import { access, readFile, rename, stat } from 'node:fs/promises';
import { join } from 'node:path';
import { FFMPEG, VIDEO_DIR, fail } from './config.mjs';

// Dérive les fichiers publiables de l'enregistrement Playwright (raw.webm, VP8, lourd) :
//   demo.mp4     H.264, seul format vidéo publié : lu par tous les navigateurs
//   poster.png   image d'aperçu, prise sur la scène « player »
//   demo.gif     boucle courte pour le README et la page Présentation
//
// Pourquoi un seul MP4 : en H.264 `veryslow` + `tune animation` (réglage adapté
// aux aplats d'une interface), il pèse moins que la même vidéo en VP9, et un
// deuxième format n'apporterait que du poids au dépôt.
//
// Les instants viennent de marks.json (écrit par la capture) ; VIDEO_START,
// POSTER_AT, GIF_START et GIF_DURATION, en secondes, les surchargent.
// VIDEO_CRF règle le compromis poids / netteté (défaut 30 ; plus bas = plus net).

const env = process.env;
let source = join(VIDEO_DIR, 'raw.webm');
const legacy = join(VIDEO_DIR, 'demo.source.webm');

try {
  await access(source);
} catch {
  // Enregistrement fait avec une version précédente du script.
  try {
    await access(legacy);
    await rename(legacy, source);
  } catch {
    fail(`Aucun enregistrement dans ${source}. Lancez d'abord \`npm run video\`.`);
  }
}

let marks = [];
try {
  marks = JSON.parse(await readFile(join(VIDEO_DIR, 'marks.json'), 'utf8'));
} catch {
  // pas de repères : valeurs par défaut
}
const at = (name, fallback) => marks.find((m) => m.name === name)?.t ?? fallback;

// Le début de l'enregistrement est une page blanche pendant le chargement.
const start = Number(env.VIDEO_START ?? Math.max(0, at('auth', 0) + 0.8));
const end = at('end', null);
const duration = end ? ['-t', String(Math.max(1, end - start + 1))] : [];
const crf = String(env.VIDEO_CRF ?? 30);

function ffmpeg(args) {
  return new Promise((resolve, reject) => {
    const child = spawn(FFMPEG, ['-y', '-loglevel', 'error', ...args], { stdio: ['ignore', 'inherit', 'inherit'] });
    child.on('error', reject);
    child.on('close', (code) => (code === 0 ? resolve() : reject(new Error(`ffmpeg a échoué (${code})`))));
  });
}

const size = async (file) => `${((await stat(file)).size / 1e6).toFixed(2)} Mo`;

console.log(`→ demo.mp4 (H.264, CRF ${crf})`);
await ffmpeg(['-ss', String(start), '-i', source, ...duration,
  '-c:v', 'libx264', '-crf', crf, '-preset', 'veryslow', '-tune', 'animation',
  '-pix_fmt', 'yuv420p', '-movflags', '+faststart', '-an',
  join(VIDEO_DIR, 'demo.mp4')]);

const posterAt = Number(env.POSTER_AT ?? Math.max(0, at('player', 12) + 4 - start));
console.log(`→ poster.png (${posterAt.toFixed(1)} s)`);
await ffmpeg(['-ss', String(posterAt), '-i', join(VIDEO_DIR, 'demo.mp4'), '-frames:v', '1', join(VIDEO_DIR, 'poster.png')]);

const gifStart = Number(env.GIF_START ?? Math.max(0, at('catalogue', 8) - start));
const gifDuration = Number(env.GIF_DURATION ?? 36);
console.log(`→ demo.gif (${gifStart.toFixed(1)} s, ${gifDuration} s)`);
await ffmpeg(['-ss', String(gifStart), '-t', String(gifDuration), '-i', join(VIDEO_DIR, 'demo.mp4'),
  '-vf', 'fps=10,scale=900:-1:flags=lanczos,split[a][b];[a]palettegen=stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=4',
  join(VIDEO_DIR, 'demo.gif')]);

for (const name of ['demo.mp4', 'poster.png', 'demo.gif']) {
  console.log(`  ${name.padEnd(11)} ${await size(join(VIDEO_DIR, name))}`);
}
console.log(`✓ encodage terminé → ${VIDEO_DIR}`);
