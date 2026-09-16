import { chromium } from 'playwright';
import { mkdir, readdir, rename, rm, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import {
  ASK, ASK_TIMEOUT_MS, FRONT, MODE, NOTE, SCALE, SHOTS_DIR, THEME, VIDEO_DIR,
  api, fail, lessonsOf, loadDemo,
} from './config.mjs';

// Premier mot de la note, sans balisage : sert a attendre son apparition a
// l'ecran, puis a la retrouver pour la supprimer en fin de prise.
const NOTE_MARKER = NOTE.replace(/[*_`#>[\]]/g, '').trim().split(/\s+/)[0] || 'note';

// Parcours complet du front : accueil, catalogue, formation, assistant,
// lecteur, résumé, notes, documents, studio. Deux modes :
//   shots  captures PNG (×SCALE) dans out/shots/
//   video  enregistrement brut (WebM VP8) avec curseur dessiné dans out/video/raw.webm,
//          à passer ensuite dans encode.mjs
//
// Aucune action destructive : rien n'est supprimé, déplacé ni renommé. La
// note écrite pendant la vidéo est retirée via l'API à la fin.

// Faux curseur : Playwright n'enregistre pas le pointeur système.
const CURSOR = `
  (() => {
    const install = () => {
      if (document.getElementById('__cur')) return;
      const d = document.createElement('div');
      d.id = '__cur';
      d.style.cssText = 'position:fixed;z-index:2147483647;width:20px;height:20px;margin:-10px 0 0 -10px;' +
        'border-radius:50%;background:rgba(255,255,255,.9);box-shadow:0 0 0 2px rgba(0,60,160,.75),0 2px 10px rgba(0,0,0,.35);' +
        'pointer-events:none;left:-100px;top:-100px;transition:transform .08s ease-out';
      document.documentElement.appendChild(d);
      addEventListener('mousemove', e => { d.style.left = e.clientX + 'px'; d.style.top = e.clientY + 'px'; }, true);
      addEventListener('mousedown', () => {
        d.style.transform = 'scale(.6)';
        const r = document.createElement('div');
        r.style.cssText = 'position:fixed;z-index:2147483646;width:14px;height:14px;margin:-7px 0 0 -7px;border-radius:50%;' +
          'border:2px solid rgba(0,198,251,.95);pointer-events:none;left:' + d.style.left + ';top:' + d.style.top + ';' +
          'transition:all .45s ease-out';
        document.documentElement.appendChild(r);
        requestAnimationFrame(() => { r.style.width='54px'; r.style.height='54px'; r.style.margin='-27px 0 0 -27px'; r.style.opacity='0'; });
        setTimeout(() => r.remove(), 500);
      }, true);
      addEventListener('mouseup', () => { d.style.transform = 'scale(1)'; }, true);
    };
    if (document.readyState === 'loading') addEventListener('DOMContentLoaded', install);
    else install();
    new MutationObserver(install).observe(document.documentElement, { childList: true });
  })();
`;

const video = MODE === 'video';
const demo = await loadDemo();

// Résolution de la cible via l'API : la capture échoue tôt et clairement
// plutôt qu'au milieu d'un enregistrement.
const { formations } = await api('/formations', { uid: demo.uid });
const formation = formations.find((f) => f.name === demo.formation);
if (!formation) fail(`Formation « ${demo.formation} » absente de ${FRONT}. Lancez \`npm run seed\`.`);
const lessons = lessonsOf(formation);
const lesson = lessons.find((l) => l.title === demo.lesson)
  ?? lessons.find((l, i) => i > 0 && l.summary_status === 'ready')
  ?? lessons[Math.min(1, lessons.length - 1)];
if (!lesson) fail(`La formation « ${formation.name} » ne contient aucune leçon.`);

const outDir = video ? VIDEO_DIR : SHOTS_DIR;
await mkdir(outDir, { recursive: true });

const browser = await chromium.launch({ args: ['--force-color-profile=srgb', '--font-render-hinting=none', '--autoplay-policy=no-user-gesture-required'] });
const ctx = await browser.newContext({
  viewport: { width: 1440, height: 900 },
  deviceScaleFactor: video ? 1 : SCALE,
  locale: 'fr-FR',
  colorScheme: THEME,
  reducedMotion: 'no-preference',
  ...(video ? { recordVideo: { dir: outDir, size: { width: 1440, height: 900 } } } : {}),
});
if (video) await ctx.addInitScript(CURSOR);
const page = await ctx.newPage();
const t0 = Date.now();

// Horodatage des scènes : encode.mjs s'en sert pour l'image d'aperçu et le GIF.
const marks = [];
const mark = (name) => marks.push({ name, t: Number(((Date.now() - t0) / 1000).toFixed(2)) });

const pause = (ms) => page.waitForTimeout(video ? ms : Math.min(ms, 250));

async function moveTo(loc) {
  if (!video) return;
  const box = await loc.boundingBox();
  if (!box) return;
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2, { steps: 24 });
}
async function click(loc) {
  await loc.scrollIntoViewIfNeeded();
  await moveTo(loc);
  await pause(250);
  await loc.click();
  await pause(450);
}
async function type(loc, text, delay = 45) {
  await click(loc);
  await loc.pressSequentially(text, { delay: video ? delay : 0 });
}
async function smoothScrollTo(loc, offset = 90) {
  const box = await loc.boundingBox();
  if (!box) return;
  const target = Math.max(0, box.y + (await page.evaluate(() => window.scrollY)) - offset);
  await page.evaluate(([y, behavior]) => window.scrollTo({ top: y, behavior }), [target, video ? 'smooth' : 'instant']);
  // Attend l'arrêt réel du défilement : un clic pendant l'animation vise un
  // élément qui bouge encore, et Playwright attend sa stabilité indéfiniment.
  await page.evaluate(() => new Promise((resolve) => {
    let last = -1;
    let still = 0;
    const tick = () => {
      still = window.scrollY === last ? still + 1 : 0;
      last = window.scrollY;
      if (still >= 6) resolve();
      else requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }));
  await pause(300);
}
async function shot(name, target = page, opts = {}) {
  if (video) return;
  await page.waitForTimeout(150);
  await target.screenshot({ path: join(outDir, `${name}.png`), animations: 'disabled', caret: 'hide', ...opts });
  console.log(`  ${name}.png`);
}
const startsWith = (text) => new RegExp(`^${text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}`);

/** Sur la page formation : déplie le chapitre de la leçon si besoin, renvoie sa ligne. */
async function revealLesson() {
  const row = page.getByRole('button', { name: startsWith(lesson.title) }).first();
  if (!(await row.isVisible())) {
    await click(page.getByRole('button', { name: startsWith(lesson.chapter.name), expanded: false }).first());
    await row.waitFor();
  }
  return row;
}

async function toTop() {
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'instant' }));
}

try {
  // ── 1. Accueil : reprise de l'identifiant ───────────────────────────────
  mark('auth');
  await page.goto(`${FRONT}/auth`, { waitUntil: 'networkidle' });
  const uidField = page.getByLabel('UID');
  await uidField.waitFor();
  await pause(900);
  await shot('01-auth');
  await type(uidField, demo.uid, 28);
  await pause(400);
  await click(page.getByRole('button', { name: 'Continue' }));
  await page.waitForURL((u) => !u.pathname.startsWith('/auth'), { timeout: 20000 });

  // ── 2. Catalogue ────────────────────────────────────────────────────────
  mark('catalogue');
  await page.getByRole('heading', { name: 'Mes formations' }).waitFor();
  await page.locator('.MuiLinearProgress-root').first().waitFor();
  await page.waitForLoadState('networkidle');
  await pause(1500);
  await shot('02-catalogue');
  const card = page.getByRole('heading', { name: formation.name, exact: true });
  await moveTo(card);
  await pause(700);

  // ── 3. Formation ────────────────────────────────────────────────────────
  mark('formation');
  await click(card);
  await page.getByRole('heading', { level: 1, name: formation.name }).waitFor();
  await page.waitForLoadState('networkidle');
  await pause(1400);
  await shot('03-formation');

  // ── 4. Assistant (facultatif : demande un LLM et une formation indexée) ──
  const assistant = page.locator('.MuiPaper-root').filter({ has: page.getByText(/^Assistant — /) }).first();
  if (ASK) {
    mark('assistant');
    const input = assistant.getByPlaceholder('Votre question…');
    await type(input, ASK, 38);
    await pause(300);
    await page.keyboard.press('Enter');
    const outcome = await Promise.race([
      assistant.getByText('Sources', { exact: true }).waitFor({ timeout: ASK_TIMEOUT_MS }).then(() => 'answer'),
      assistant.locator('.MuiAlert-standardError').waitFor({ timeout: ASK_TIMEOUT_MS }).then(() => 'error'),
    ]).catch(() => 'timeout');
    if (outcome === 'answer') {
      await pause(2800);
      await shot('04-assistant', assistant);
    } else {
      console.warn(`! assistant : ${outcome === 'error' ? 'erreur renvoyée par l\'API' : 'pas de réponse à temps'} — capture 04 sautée`);
    }
    await pause(600);
  }

  // Parcours des chapitres, puis ouverture de la leçon.
  const lessonRow = await revealLesson();
  await smoothScrollTo(lessonRow, 260);
  await pause(1200);

  // ── 5. Lecteur ──────────────────────────────────────────────────────────
  mark('player');
  await click(lessonRow);
  await page.getByRole('heading', { level: 1, name: lesson.title }).waitFor();
  await page.waitForLoadState('networkidle');
  const media = page.locator('video, audio').first();
  await media.waitFor({ state: 'attached' });
  await page.waitForFunction(() => {
    const m = document.querySelector('video, audio');
    return m && m.readyState >= 1;
  }, null, { timeout: 15000 }).catch(() => {});
  if (video) {
    const bigPlay = page.locator('.vjs-big-play-button');
    if (await bigPlay.isVisible().catch(() => false)) await click(bigPlay);
    await pause(3500);
    await page.evaluate(() => document.querySelector('video, audio')?.pause());
  } else {
    await pause(800);
  }
  await shot('05-player');

  // ── 6. Résumé ───────────────────────────────────────────────────────────
  const summaryButton = page.getByRole('button', { name: 'Résumé', exact: true });
  if (await summaryButton.isVisible().catch(() => false)) {
    mark('summary');
    await click(summaryButton);
    const summaryPanel = page.locator('.MuiPaper-root').filter({ has: page.getByRole('heading', { name: 'Résumé', exact: true }) }).first();
    await summaryPanel.waitFor();
    await pause(700);
    await smoothScrollTo(summaryPanel);
    await pause(2600);
    await shot('06-summary', summaryPanel);
    // Replié ensuite : un long résumé repousse les notes très loin sous le lecteur.
    await click(summaryButton);
    await summaryPanel.waitFor({ state: 'hidden' }).catch(() => {});
  }

  // ── 7. Notes ────────────────────────────────────────────────────────────
  mark('notes');
  const tabsBlock = page.getByRole('tablist').locator('xpath=ancestor::div[contains(@class,"MuiTabs-root")]/..');
  await smoothScrollTo(page.getByRole('tablist'));
  await page.getByText('Ajouter une note').waitFor();
  const noteText = NOTE;
  if (video) {
    // L'éditeur du résumé, replié, précède celui des notes dans le DOM.
    const notePanel = page.locator('.MuiPaper-root').filter({ has: page.getByText('Ajouter une note') }).last();
    const editor = notePanel.locator('.w-md-editor-text-input');
    await type(editor, noteText, 32);
    await pause(500);
    await click(page.getByRole('button', { name: 'Lier au temps actuel' }));
    await page.getByText(NOTE_MARKER, { exact: false }).last().waitFor();
    await pause(1800);
  } else {
    await pause(500);
  }
  await shot('07-notes', tabsBlock);

  // ── 8. Documents ────────────────────────────────────────────────────────
  const docsTab = page.getByRole('tab', { name: /^Documents/ });
  mark('documents');
  await click(docsTab);
  await pause(1600);
  await shot('08-documents', tabsBlock);

  // ── 9. Studio ───────────────────────────────────────────────────────────
  await toTop();
  mark('studio');
  await click(page.getByRole('button', { name: 'Studio', exact: true }));
  await page.getByRole('heading', { level: 1, name: 'Studio' }).waitFor();
  await page.waitForLoadState('networkidle');
  await pause(1300);
  await shot('09-studio');

  const row = page.getByRole('listitem').filter({ hasText: formation.name }).first();
  await click(row.getByRole('button', { name: 'Éditer' }));
  await page.getByLabel('Titre de la formation').waitFor();
  await page.waitForLoadState('networkidle');
  mark('builder');
  await pause(1300);
  await shot('10-builder');
  if (video) {
    for (const label of ['Transcrire', 'Monter', 'Déplacer']) {
      const action = page.getByRole('button', { name: label, exact: true }).nth(1);
      if (await action.isVisible().catch(() => false)) {
        await moveTo(action);
        await pause(1100);
      }
    }
    await smoothScrollTo(page.getByText('Ajouter un chapitre'), 500);
    await pause(1500);
    await toTop();
    await pause(600);

    // Bascule de thème, puis retour : montre le mode sombre sans le garder.
    mark('theme');
    await click(page.getByRole('button', { name: 'Changer le thème' }));
    await click(page.getByRole('menuitem', { name: THEME === 'dark' ? 'Clair' : 'Sombre' }));
    await pause(2200);
    await click(page.getByRole('button', { name: 'Changer le thème' }));
    await click(page.getByRole('menuitem', { name: 'Système' }));
    await pause(1200);
  }

  // ── 10. Rendu mobile ────────────────────────────────────────────────────
  // Navigation dans l'application, pas `page.goto` : un chargement direct d'une
  // page protégée repasse par /auth, qui renvoie au catalogue.
  if (!video) {
    await page.setViewportSize({ width: 430, height: 932 });
    await page.getByText('Formation', { exact: true }).first().click();
    await page.getByRole('heading', { name: formation.name, exact: true }).click();
    await page.getByRole('heading', { level: 1, name: formation.name }).waitFor();
    await (await revealLesson()).click();
    await page.getByRole('heading', { level: 1, name: lesson.title }).waitFor();
    await page.waitForTimeout(1200);
    await shot('11-mobile', page, { fullPage: false });
  }
  mark('end');
} catch (error) {
  await page.screenshot({ path: join(outDir, 'error.png') }).catch(() => {});
  console.error(`✗ capture interrompue : ${error.message.split('\n').slice(0, 12).join('\n    ')}\n  écran enregistré dans ${join(outDir, 'error.png')}`);
  process.exitCode = 1;
} finally {
  const recording = page.video();
  await ctx.close();
  await browser.close();

  if (video && recording) {
    const recorded = await recording.path();
    const target = join(outDir, 'raw.webm');
    await rm(target, { force: true });
    await rename(recorded, target);
    // Nettoie les enregistrements orphelins et les anciens noms (demo.webm, demo.source.webm).
    for (const name of await readdir(outDir)) {
      if (name.endsWith('.webm') && name !== 'raw.webm') await rm(join(outDir, name), { force: true });
    }
    await writeFile(join(outDir, 'marks.json'), `${JSON.stringify(marks, null, 2)}\n`);
    console.log(`  raw.webm, marks.json`);
  }
}

// La note tapée pendant la vidéo ne doit pas s'accumuler d'une prise à l'autre.
if (video) {
  const notes = await api(`/notes/${lesson.id}`, { uid: demo.uid }).catch(() => []);
  for (const note of notes.filter((n) => n.content.startsWith(NOTE.slice(0, 30)))) {
    await api(`/notes/${note.id}`, { uid: demo.uid, method: 'DELETE' }).catch(() => {});
  }
}

console.log(process.exitCode ? '✗ échec' : `✓ ${MODE} (${THEME}) → ${outDir}`);
