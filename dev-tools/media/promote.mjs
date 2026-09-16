import { copyFile, mkdir, stat } from 'node:fs/promises';
import { join, relative } from 'node:path';
import { DOCS_MEDIA_DIR, SHOTS_DIR, VIDEO_DIR } from './config.mjs';

// Copie la sélection publiée par le site dans docs/assets/media/, sous les noms
// que les pages HTML référencent. Tout le reste de out/ reste local.
//
// Relisez chaque image avant de commiter : voir « Avant de publier » dans le README.

const SELECTION = [
  [SHOTS_DIR, '01-auth.png', 'auth.png'],
  [SHOTS_DIR, '02-catalogue.png', 'catalogue.png'],
  [SHOTS_DIR, '03-formation.png', 'formation.png'],
  [SHOTS_DIR, '04-assistant.png', 'assistant.png'],
  [SHOTS_DIR, '05-player.png', 'player.png'],
  [SHOTS_DIR, '07-notes.png', 'notes.png'],
  [SHOTS_DIR, '09-studio.png', 'studio.png'],
  [SHOTS_DIR, '10-builder.png', 'builder.png'],
  [VIDEO_DIR, 'demo.mp4', 'demo.mp4'],
  [VIDEO_DIR, 'poster.png', 'poster.png'],
  [VIDEO_DIR, 'demo.gif', 'demo.gif'],
];

await mkdir(DOCS_MEDIA_DIR, { recursive: true });

let missing = 0;
for (const [dir, from, to] of SELECTION) {
  const source = join(dir, from);
  try {
    const { size } = await stat(source);
    await copyFile(source, join(DOCS_MEDIA_DIR, to));
    console.log(`  ${from.padEnd(18)} → ${to.padEnd(14)} ${(size / 1e6).toFixed(2)} Mo`);
  } catch {
    missing += 1;
    console.warn(`! ${relative(process.cwd(), source)} absent — ${to} non mis à jour`);
  }
}

console.log(missing
  ? `\n${missing} fichier(s) manquant(s) : relancez shots, video puis encode.`
  : `\n✓ ${SELECTION.length} fichiers copiés dans ${DOCS_MEDIA_DIR}`);
