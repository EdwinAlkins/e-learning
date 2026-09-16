#!/usr/bin/env python3
"""Vérifie le site docs/ : liens internes, ancres, id dupliqués, médias, sitemap, JSON-LD.

Usage : python3 .claude/skills/docs-site/scripts/check_links.py [dossier_docs]
Code de sortie 1 si un problème est trouvé.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
DOCS = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / "docs"
BASE = "https://edwinalkins.github.io/e-learning/"

problems: list[str] = []
pages = sorted(DOCS.glob("*.html"))
ids: dict[str, list[str]] = {}
for page in pages:
    ids[page.name] = re.findall(r'\bid="([^"]+)"', page.read_text(encoding="utf-8"))

for page in pages:
    text = page.read_text(encoding="utf-8")
    name = page.name

    duplicates = {i for i in ids[name] if ids[name].count(i) > 1}
    if duplicates:
        problems.append(f"{name}: id dupliqués {sorted(duplicates)}")

    for ref in re.findall(r'(?:href|src|poster)="(\./[^"]+)"', text):
        path, _, fragment = ref[2:].partition("#")
        target = DOCS / path
        if not target.exists():
            kind = "média manquant" if path.startswith("assets/media/") else "lien cassé"
            problems.append(f"{name}: {kind} {ref}")
        elif fragment and path.endswith(".html") and fragment not in ids.get(path, []):
            problems.append(f"{name}: ancre inexistante {ref}")

    for fragment in re.findall(r'href="#([^"]+)"', text):
        if fragment not in ids[name]:
            problems.append(f"{name}: ancre locale inexistante #{fragment}")

    if name != "index.html":
        if 'aria-current="page"' not in text:
            problems.append(f"{name}: aucun lien aria-current dans la sidenav")
        if f'href="{BASE}{name}"' not in text:
            problems.append(f"{name}: canonical / og:url absent ou incorrect")

    for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', text, re.S):
        try:
            json.loads(block)
        except json.JSONDecodeError as error:
            problems.append(f"{name}: JSON-LD invalide ({error})")

    for script in re.findall(r"<script(?![^>]*application/ld\+json)[^>]*>", text):
        problems.append(f"{name}: script interdit {script}")
    for external in re.findall(r'<(?:link|script|img)[^>]+(?:href|src)="(https?://[^"]+)"', text):
        if not external.startswith(BASE) and "rel=\"canonical\"" not in text.split(external)[0][-80:]:
            problems.append(f"{name}: ressource externe chargée {external}")

sitemap = DOCS / "sitemap.xml"
if sitemap.exists():
    listed = set(re.findall(r"<loc>(.*?)</loc>", sitemap.read_text(encoding="utf-8")))
    for page in pages:
        url = BASE if page.name == "index.html" else BASE + page.name
        if url not in listed:
            problems.append(f"sitemap.xml: {page.name} absente")
else:
    problems.append("sitemap.xml absent")

media = DOCS / "assets" / "media"
referenced = set()
for page in pages:
    referenced.update(re.findall(r'\./assets/media/([^"#]+)', page.read_text(encoding="utf-8")))
if media.exists():
    for file in media.iterdir():
        if file.name not in referenced:
            problems.append(f"assets/media/{file.name}: présent mais référencé par aucune page")

print(f"{len(pages)} pages vérifiées dans {DOCS}")
for problem in problems:
    print(f"✗ {problem}")
print("✓ aucun problème" if not problems else f"{len(problems)} problème(s)")
sys.exit(1 if problems else 0)
