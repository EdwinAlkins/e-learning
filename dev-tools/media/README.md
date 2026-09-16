# Media — démo, captures et vidéo de présentation

Scripts Node (Playwright + ffmpeg) qui peuplent une instance avec une formation de
démonstration, pilotent le front et produisent les captures et la vidéo utilisées par le site
`docs/`. C'est de l'outillage : rien ici n'est importé par l'application, livré dans une
image ou exécuté en CI.

| Script | Rôle |
| --- | --- |
| `seed.mjs` | Crée trois formations via l'API : médias générés par ffmpeg, résumés, documents, notes et progression d'un apprenant de démo |
| `capture.mjs` | Parcours complet du front. `shots` : PNG ×2 ; `video` : enregistrement brut 1440×900 avec curseur dessiné |
| `encode.mjs` | Dérive de l'enregistrement `demo.mp4` (H.264, seul format vidéo publié), `poster.png` et `demo.gif` |
| `promote.mjs` | Copie la sélection dans `docs/assets/media/` sous les noms attendus par les pages |
| `config.mjs` | Cibles, identité, thème, chemins ; client API partagé |
| `seed-content.mjs` | Le contenu des formations de démo : titres, durées, résumés, documents |

## Prérequis

- Node 20+ et ffmpeg (avec `libx264`, `libmp3lame`, `drawtext`).
- Une instance qui tourne : `docker compose up -d` à la racine, ou API + worker + front en
  local. Le worker, Qdrant et un modèle de langage ne sont nécessaires que pour la scène de
  l'assistant.

```bash
cd dev-tools/media
npm run setup          # installe playwright et Chromium
```

## Pas à pas

```bash
npm run seed           # une fois : formations de démo + out/demo.json
npm run shots          # → out/shots/01-auth.png … 11-mobile.png
npm run video          # → out/video/raw.webm (brut) + marks.json
npm run encode         # → out/video/demo.mp4, poster.png, demo.gif
npm run promote        # → docs/assets/media/
```

`npm run all` enchaîne `shots`, `video`, `encode` et `promote`.

Ouvrez ensuite `docs/index.html` dans un navigateur pour vérifier le rendu.

## Configuration

Tout vient de l'environnement ; aucun hôte ni identifiant n'est écrit dans un fichier versionné.

| Variable | Défaut | Rôle |
| --- | --- | --- |
| `FRONT_URL` | `http://localhost:3000` | Front à filmer |
| `API_URL` | `http://localhost:8000` | API, pour le seed et la résolution des identifiants |
| `THEME` | `light` | `light` ou `dark` (préférence de couleur du navigateur) |
| `SCALE` | `2` | Densité des captures PNG |
| `ASK` | une question sur la mise en production | Question posée à l'assistant ; `ASK=` (vide) saute la scène |
| `ASK_TIMEOUT` | `120` | Attente maximale de la réponse, en secondes |
| `NOTE` | une note sur les volumes Docker | Note tapée dans le lecteur pendant la vidéo, puis supprimée par l'API |
| `DEMO_UID` | celui de `out/demo.json` | Identité utilisée par le seed et la capture |
| `FORMATION` | `Docker en pratique` | Formation à filmer (nom exact) |
| `LESSON` | `Images et conteneurs` | Leçon ouverte dans le lecteur (titre exact) |
| `SEED_RESET` | — | `1` : supprime et recrée les formations de démo |
| `FONT` | DejaVu Sans ou Arial | Police TrueType des cartons titres |
| `FFMPEG` | `ffmpeg` | Binaire ffmpeg |
| `OUT` | `out` | Dossier de sortie, relatif à ce dossier |
| `VIDEO_START`, `POSTER_AT`, `GIF_START`, `GIF_DURATION` | tirés de `marks.json` | Réglages fins de `encode.mjs`, en secondes |
| `VIDEO_CRF` | `30` | Qualité H.264 : plus bas = plus net et plus lourd |
| `GIF_FPS`, `GIF_COLORS` | `6`, `96` | Images par seconde et couleurs du GIF : plus haut = plus fluide et plus lourd |

Exemples :

```bash
THEME=dark npm run shots
ASK= npm run video                                  # instance sans LLM
FRONT_URL=https://learn.example.test API_URL=https://learn.example.test/api \
  DEMO_UID=… FORMATION="Ma formation" npm run shots  # instance déjà peuplée
```

## Ce que fait le parcours

Accueil (saisie de l'UID) → catalogue → page formation → question à l'assistant → leçon
dans le lecteur, lecture quelques secondes → résumé → notes (en vidéo, une note est écrite
puis retirée par l'API à la fin) → documents → studio → éditeur de formation, survol des
actions → rendu mobile (captures uniquement).

**Aucune action destructive.** Rien n'est supprimé, renommé ni déplacé dans l'interface. Si
vous étendez le script, gardez cette règle : il doit pouvoir tourner contre une instance
réelle.

Chaque scène est horodatée dans `out/video/marks.json` ; `encode.mjs` s'en sert pour couper
la page blanche du début, choisir l'image d'aperçu et le départ du GIF.

## Le seed

- Les médias sont des **cartons titres** (fond bleu, titre, chapitre, minuterie) encodés à
  10 images/s : environ 1 Mo et une quinzaine de secondes d'encodage pour 10 minutes de
  leçon. Ils sont générés une fois dans `out/seed-media/` (≈ 2 à 3 minutes pour les 16 leçons),
  puis réutilisés.
- Ils sont **muets** : les résumés sont écrits directement (`PUT /videos/{id}/summary`), et
  l'assistant s'appuie sur ces résumés et sur les documents Markdown. Cliquer sur
  *Transcrire* sur une leçon de démo produit une transcription vide.
- L'indexation de la formation est lancée à la fin ; elle demande le worker, Qdrant et les
  embeddings. Sans eux, tout le reste de la démo fonctionne.

> **Les fichiers atterrissent dans `VIDEOS_HOST_PATH`.** Avec le `.env` par défaut, c'est
> `e-learning-api/videos/`, qui n'est pas ignoré par git. Pointez `VIDEOS_HOST_PATH` hors du
> dépôt pour une instance de démo, ou ne commitez pas ce dossier.

## Sorties

| Fichier | Contenu | Publié sous |
| --- | --- | --- |
| `shots/01-auth.png` | Écran d'accueil | `auth.png` |
| `shots/02-catalogue.png` | Catalogue et progression | `catalogue.png` |
| `shots/03-formation.png` | Page formation | `formation.png` |
| `shots/04-assistant.png` | Assistant : réponse et sources | `assistant.png` |
| `shots/05-player.png` | Lecteur | `player.png` |
| `shots/06-summary.png` | Panneau résumé | — |
| `shots/07-notes.png` | Onglet notes | `notes.png` |
| `shots/08-documents.png` | Onglet documents | — |
| `shots/09-studio.png` | Liste du studio | `studio.png` |
| `shots/10-builder.png` | Éditeur de formation | `builder.png` |
| `shots/11-mobile.png` | Lecteur à 430 px | — |
| `video/raw.webm` | Enregistrement brut de Playwright (VP8, lourd) | — |
| `video/demo.mp4`, `poster.png` | Vidéo de présentation (61 s, ≈ 1,6 Mo) et image d'aperçu | mêmes noms |
| `video/demo.gif` | Boucle de 36 s, 900 px, 6 images/s (≈ 3 Mo) | `demo.gif` (README ; repli de la vidéo sur la page Présentation) |

### Vidéo de lancement (landing)

La landing ne montre pas `demo.mp4` mais un film de présentation de 31 s, réalisé à part avec
le skill `/brag` (Hyperframes) dans `brag-output/`, dossier ignoré par git. Il n'est pas produit
par ce pipeline : après un nouveau rendu de `brag-output/brag.mp4`, dérivez la version web à la
main, depuis la racine du dépôt :

```bash
# Sans son (lecture automatique muette), 1280 px, première image (miniature intégrée) retirée
ffmpeg -y -i brag-output/brag.mp4 -an \
  -vf "select='gte(n\,1)',setpts=N/FRAME_RATE/TB,scale=1280:-2:flags=lanczos" \
  -c:v libx264 -preset veryslow -tune animation -crf 32 -pix_fmt yuv420p -movflags +faststart \
  docs/assets/media/launch.mp4
ffmpeg -y -i brag-output/brag.jpg -vf "scale=1280:-2:flags=lanczos" -q:v 4 \
  docs/assets/media/launch-poster.jpg
```

| Fichier | Contenu | Page |
| --- | --- | --- |
| `docs/assets/media/launch.mp4` | Film de présentation, sans son, 1280×720 (≈ 0,8 Mo) | `index.html` |
| `docs/assets/media/launch-poster.jpg` | Image d'aperçu : logo, nom, tagline | `index.html` |

La version complète, avec musique, sert aux réseaux sociaux et ne va pas dans `docs/` : la
licence de la musique n'est pas vérifiée pour une diffusion sur le site.

### Pourquoi un seul format vidéo

Le site ne publie qu'un **MP4 H.264** : c'est le seul format lu par tous les navigateurs, y
compris les anciens Safari sur iOS. Encodé en `-preset veryslow -tune animation` (réglage
adapté aux aplats d'une interface) à CRF 30, il pèse ≈ 1,6 Mo pour 61 s. Un second format
n'ajouterait que du poids au dépôt.

Le poids dépend fortement de ce qui est filmé : des cartons titres du seed compressent bien
mieux qu'une vidéo réelle affichée dans le lecteur. Remesurez après chaque prise, et ajustez
`GIF_DURATION` ou la largeur du GIF si la page devient lourde.

En cas d'échec, la capture enregistre l'écran courant dans `error.png`.

## Avant de publier

Une capture montre plus que l'interface. Pour chaque image promue dans `docs/assets/media/` :

- **UID** : visible dans l'en-tête et tapé à l'écran d'accueil. Utilisez l'UID de démo, jamais
  celui d'un vrai apprenant.
- **Contenu** : titres de formations, notes, résumés et réponses de l'assistant d'une instance
  réelle peuvent être confidentiels. Capturez une instance peuplée par le seed.
- **Adresses** : les captures Playwright n'ont pas de barre d'adresse, mais une URL peut fuiter
  par un message d'erreur, un nom de fichier ou un message de commit.
- **Licence du contenu filmé** : les captures montrent les vidéos réellement présentes dans
  l'instance, titres compris. Ne filmez que du contenu dont vous avez le droit de diffuser des
  images — le seed, ou des vidéos sous licence libre — et créditez la source dans `README.md`,
  `docs/index.html` et `docs/overview.html`. Le catalogue liste **toutes** les formations de
  l'instance : une formation tierce laissée en base apparaît sur la capture du catalogue.
