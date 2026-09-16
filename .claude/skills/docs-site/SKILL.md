---
name: docs-site
description: Maintenir le site de documentation et la landing page de Cladèse (docs/, HTML statique sans dépendance, en français), le README du dépôt, et régénérer captures, vidéo et GIF de présentation avec dev-tools/media. À utiliser dès qu'il faut écrire, corriger ou restructurer une page de docs/, la landing, le README, ajouter une page, mettre à jour des médias, ou vérifier la cohérence doc ↔ code.
---

# Site de documentation Cladèse

Le site vit dans `docs/` et se publie tel quel sur GitHub Pages
(`https://edwinalkins.github.io/e-learning/`, branche `main`, dossier `/docs`). Les médias
viennent de `dev-tools/media/`. Le README racine est la vitrine GitHub du même contenu.

## Règles non négociables

1. **Aucune dépendance** : ni générateur, ni CDN, ni police externe, ni JavaScript exécuté,
   ni badge distant (shields.io). Une seule feuille `docs/assets/style.css`. Seule exception :
   le bloc JSON-LD de `index.html`, qui est de la donnée. Les badges shields.io sont permis
   dans le **README** uniquement.
2. **Français**, ton direct, phrases courtes, vouvoiement. Pas de jargon sur la landing
   (Qdrant, RabbitMQ, H.264… vont dans les pages techniques).
3. **Chaque affirmation se vérifie dans le code** avant d'être écrite. Lire la source
   (`e-learning-api/src/e_learning/…`, `e-learning-front/src/…`, `.env.template`,
   `docker-compose.yml`) plutôt que supposer. Mesurer plutôt qu'estimer (`docker stats`,
   `docker images`, `stat`).
4. **Aucune sur-promesse.** Formulations interdites ou à reformuler :
   - « l'IA regarde / voit les vidéos » → elle traite la parole transcrite et le texte des documents ;
   - « pas de réponse inventée » → l'assistant peut se tromper, les sources servent à vérifier ;
   - « vos contenus ne sortent jamais » → les **médias** restent sur le serveur ; le **texte**
     part vers le LLM s'il est distant ;
   - toute fonctionnalité absente (comptes, rôles, SSO, SCORM, pagination, changelog, instance de démo).
5. **Positionnement fixé** : trois piliers, dans cet ordre — **e-learning** (le produit),
   **auto-hébergé** (le déploiement), **IA** (le différenciateur). « Pointer un dossier de
   vidéos » est un atout d'import, pas l'identité. Cible annoncée tôt : **usage personnel ou
   équipe de confiance** (pas d'authentification intégrée).
6. **Ne jamais publier de contenu tiers** : pas de cours commercial, visage, filigrane ou
   nom de formation réelle dans `docs/assets/media/`. Les captures se font sur une formation
   dont l'utilisateur a les droits, ou sur le seed de démo.
7. Ni commit ni branche sans demande explicite de l'utilisateur.

Avant d'accepter une critique ou une revue externe, la confronter au code et à ces règles :
les revues contiennent des erreurs factuelles (voir « Faits établis »).

## Carte du site

| Page | Rôle | Section de la nav |
| --- | --- | --- |
| `index.html` | Landing : hero, démo, installation, plateforme, IA, contrôle, « Est-ce le bon outil ? », FAQ | — |
| `overview.html` | Présentation : trois piliers, pour qui, structure du dépôt | La plateforme |
| `installation.html` | Prérequis, ressources mesurées, Docker, import, hors Docker, exposer, mise à jour | La plateforme |
| `configuration.html` | Toutes les variables `APP_*`, Compose, front | La plateforme |
| `learning.html` | Parcours apprenant | Utiliser |
| `studio.html` | Studio, conversion, documents, catalogue disque, réconciliation | Utiliser |
| `ai.html` | Chaîne IA, limites, ce qui sort du serveur, modèles, dépannage | Utiliser |
| `mobile.html` | Application Flutter | Utiliser |
| `architecture.html` | Vue d'ensemble (schéma de déploiement), couches, contextes, jobs | Sous le capot |
| `api.html` | Routes HTTP | Sous le capot |
| `operations.html` | CLI, worker, migrations, sauvegardes, diagnostic | Sous le capot |
| `development.html` | Tests, qualité, dev-tools, publication du site | Sous le capot |

Aussi : `sitemap.xml`, `robots.txt`, `.nojekyll`, `assets/logo.png`, `assets/media/`.

## Anatomie d'une page de documentation

Copier une page existante plutôt que partir de zéro. Éléments obligatoires :

- `<head>` : `<title>Titre &mdash; Cladèse</title>`, `meta description`, `link rel="canonical"`,
  balises `og:type/url/title/description/image/locale` (URL absolues), feuille et favicon.
- `.topbar` (marque + « Accueil » + « Code source »), `.shell` avec `.sidenav` identique sur
  toutes les pages et `aria-current="page"` sur la page courante.
- `<main id="content">` → `<header>` avec `h1` et `.lede`.
- Titres `h2`/`h3` avec `id` et ancre : `<h2 id="x">Titre<a class="anchor" href="#x" aria-label="Lien vers cette section">#</a></h2>`.
- `nav.pager` précédent / suivant, puis `footer.site`.

Composants CSS disponibles : `.snippet[data-lang]` + `pre > code`, `.table-wrap > table`,
`.note` (info), `.warn` (danger), `.cards` (liens `a` ou `div`), `.pill.pill-get|post|put|patch|delete`,
`.shot` + `.shot-caption`, `.diagram > svg`. Landing : `.hero`, `.cta`, `.badges`, `.steps`,
`.split` / `.split.reverse`, `.also`, `table.fit td.yes|no`, `.faq`, `.closing`.

Schémas : SVG inline, couleurs via `var(--ink|muted|line|surface|ground|accent)` pour suivre
clair/sombre, `role="img"` et `aria-label` descriptif. Échapper `<` `>` `&` dans le HTML.

**Ajouter une page** : copier une page, ajuster head/og/canonical, ajouter le lien dans la
`.sidenav` de **toutes** les pages, recâbler les `pager` voisins, ajouter l'URL à `sitemap.xml`.

## Procédure de mise à jour

1. Lire le code concerné et la page actuelle (le fichier a pu être modifié à la main :
   partir de l'état sur disque).
2. Écrire les modifications en respectant les règles ci-dessus ; répercuter dans le README si
   la vitrine est touchée (accroche, tableau « ce qu'il est / n'est pas », compatibilité,
   démarrage, sécurité, FAQ).
3. Vérifier :
   ```bash
   python3 .claude/skills/docs-site/scripts/check_links.py
   node .claude/skills/docs-site/scripts/render.mjs index.html architecture.html
   ```
   `check_links.py` contrôle liens internes, ancres, `id` dupliqués, médias manquants et
   JSON-LD. `render.mjs` produit des captures clair / sombre / 400 px et signale tout
   débordement horizontal et toute image cassée ; il utilise le Playwright installé dans
   `dev-tools/media` (`npm run setup` si absent). Regarder les images produites.
4. Résumer à l'utilisateur ce qui a été changé, retenu ou écarté, et pourquoi.

## Médias (captures, vidéo, GIF)

Pipeline dans `dev-tools/media/` (voir son README) :

```bash
cd dev-tools/media
npm run seed                     # facultatif : formations de démo via l'API
DEMO_UID=… FORMATION="…" LESSON="…" ASK="…" npm run shots
DEMO_UID=… FORMATION="…" LESSON="…" ASK="…" npm run video   # → out/video/raw.webm
npm run encode                   # → demo.mp4 (H.264 CRF 30), poster.png, demo.gif
npm run promote                  # → docs/assets/media/
```

- **Un seul format vidéo publié : MP4 H.264** (`-preset veryslow -tune animation`, CRF 30,
  ≈ 1,2 Mo), plus léger que VP9 et universel. Pas de WebM dans `docs/`.
- `ASK` doit être une question pertinente pour la formation filmée, sinon l'assistant répond
  qu'il ne sait pas.
- Noms publiés attendus par les pages : `auth, catalogue, formation, assistant, player, notes,
  studio, builder` (`.png`), `demo.mp4`, `poster.png`, `demo.gif`, plus `launch.mp4` et
  `launch-poster.jpg` (film de la landing, dérivé à la main de `brag-output/brag.mp4` : voir
  « Vidéo de lancement » dans `dev-tools/media/README.md`).
- Répartition : landing = `launch.mp4` (sans son) ; page Présentation = `demo.mp4` avec
  `demo.gif` en repli ; README = `demo.gif` (GitHub n'anime pas un MP4 du dépôt). Toute nouvelle image
  référencée doit être ajoutée à `SELECTION` dans `promote.mjs`.
- Si une capture manque, `.shot` affiche un emplacement « Capture à venir » (CSS
  `img.shot::before/::after`) : ne pas s'en contenter pour une publication.
- Le seed écrit dans `VIDEOS_HOST_PATH` et en base : ne pas le lancer sur l'instance réelle de
  l'utilisateur sans accord.

## Faits établis (vérifiés)

- Python **3.14** est sorti (octobre 2025) et requis hors Docker (UUIDv7 de la stdlib).
- Lancer `docker compose` **à la racine** ; `e-learning-api/docker-compose.yml` ne démarre ni
  front ni Qdrant.
- Ressources mesurées : ≈ 2,3 Go de RAM au repos (API et worker chargent chacun le modèle
  d'embeddings, ≈ 1,1 Go), + ≈ 1 Go par transcription Whisper `base` ; image API ≈ 7 Go ;
  pas de GPU requis. Premier démarrage : téléchargement du modèle d'embeddings (Hugging Face).
- Aucun LLM requis pour démarrer ; résumés et assistant en ont besoin.
- Conversion automatique selon l'**extension** (≠ `.mp4` / `.mp3`), pas le codec ; un MP4 HEVC
  se convertit via « Convertir pour le web ».
- Transcription = `leçon.txt`, résumé = `leçon.md`, à côté du média. `PUT /videos/{id}/summary`
  passe `summary_status` à `ready`.
- Assistant : recherche filtrée par formation, prompt « uniquement à partir du contexte », réponse
  en français, citations (transcription, résumé, document). Documents indexés : md, txt, csv, pdf, docx.
- `APP_RECONCILE_ON_STARTUP` figure bien dans `configuration.html`.
- API non paginée. En bash, `UID` est en lecture seule : ne pas l'utiliser comme nom de variable
  dans les exemples.
- `backup.sh` applique la rotation après chaque sauvegarde ; il ne sauvegarde pas les médias.
- `NEXT_PUBLIC_API_URL` est figée au build du front.
- Bug front connu : charger directement `/player/…` ou `/formation/…` renvoie au catalogue
  (`AuthGuard` redirige avant de lire l'UID). Les scripts de capture naviguent donc dans
  l'application au lieu d'utiliser `page.goto` sur ces routes.
- L'application mobile ne sait pas passer une authentification HTTP ni un proxy SSO : seul un
  VPN la protège.
