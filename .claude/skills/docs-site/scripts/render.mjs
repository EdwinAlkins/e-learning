// Capture des pages de docs/ en clair, sombre et 400 px, avec contrôle des
// débordements horizontaux et des images cassées.
//
// Usage : node .claude/skills/docs-site/scripts/render.mjs [page.html …]
//         (sans argument : toutes les pages)
// Sortie : OUT (défaut /tmp/docs-render) ; code 1 si un défaut est détecté.
// Playwright est pris dans dev-tools/media (npm run setup).

import { createRequire } from 'node:module';
import { mkdir, readdir } from 'node:fs/promises';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(HERE, '../../../..');
const DOCS = join(ROOT, 'docs');
const OUT = process.env.OUT ?? '/tmp/docs-render';

let chromium;
try {
  ({ chromium } = createRequire(join(ROOT, 'dev-tools/media/package.json'))('playwright'));
} catch {
  console.error('Playwright introuvable : cd dev-tools/media && npm run setup');
  process.exit(1);
}

const pages = process.argv.slice(2).length
  ? process.argv.slice(2)
  : (await readdir(DOCS)).filter((f) => f.endsWith('.html'));

const VARIANTS = [
  ['light', 'light', 1280],
  ['dark', 'dark', 1280],
  ['mobile', 'light', 400],
];

await mkdir(OUT, { recursive: true });
const browser = await chromium.launch();
let failures = 0;

for (const name of pages) {
  for (const [variant, scheme, width] of VARIANTS) {
    const page = await browser.newPage({ viewport: { width, height: 900 }, colorScheme: scheme });
    const errors = [];
    page.on('console', (m) => m.type() === 'error' && errors.push(m.text()));
    page.on('pageerror', (e) => errors.push(e.message));
    await page.goto(`file://${join(DOCS, name)}`, { waitUntil: 'load' });
    await page.waitForTimeout(400);
    const report = await page.evaluate(() => ({
      overflow: document.documentElement.scrollWidth > window.innerWidth,
      broken: [...document.images].filter((i) => i.complete && !i.naturalWidth).map((i) => i.getAttribute('src')),
      height: document.body.scrollHeight,
    }));
    const file = join(OUT, `${name.replace('.html', '')}-${variant}.png`);
    await page.screenshot({ path: file, fullPage: true });
    const issues = [];
    if (report.overflow) issues.push('débordement horizontal');
    if (report.broken.length) issues.push(`images cassées : ${report.broken.join(', ')}`);
    if (errors.length) issues.push(`erreurs : ${errors.join(' | ')}`);
    failures += issues.length ? 1 : 0;
    console.log(`${issues.length ? '✗' : '✓'} ${name} [${variant}] ${report.height}px → ${file}${issues.length ? `\n    ${issues.join('\n    ')}` : ''}`);
    await page.close();
  }
}

await browser.close();
process.exit(failures ? 1 : 0);
