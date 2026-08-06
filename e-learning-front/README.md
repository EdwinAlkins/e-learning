# e-learning-front

Frontend de la plateforme e-learning : catalogue de formations, lecteur vidéo/audio, notes, et studio d’édition (formations, chapitres, vidéos, documents).

## Stack

- **Next.js** 16 (App Router) + **React** 19 + **TypeScript**
- **MUI** v7 (`@mui/material`) — pas de Tailwind
- **Zustand** — état client
- **Axios** — client HTTP (`X-User-UID`)
- **video.js** / **react-player** — lecture média
- **@uiw/react-md-editor** — édition Markdown
- **@hello-pangea/dnd** — drag & drop (studio)

## Prérequis

- Node.js 24+ (recommandé, aligné sur le Dockerfile)
- npm
- API backend démarrée (par défaut `http://localhost:8000`)

## Installation

```bash
cp .env.template .env.local
npm install
npm run dev
```

Ouvrir [http://localhost:3000](http://localhost:3000).

### Variables d’environnement

| Variable | Description | Défaut |
|----------|-------------|--------|
| `NEXT_PUBLIC_API_URL` | URL de l’API backend | `http://localhost:8000` |

## Scripts

| Commande | Description |
|----------|-------------|
| `npm run dev` | Serveur de développement (Turbopack) |
| `npm run build` | Build de production (`output: standalone`) |
| `npm run start` | Serveur de production |
| `npm run lint` | ESLint |

## Routes

| Route | Rôle |
|-------|------|
| `/` | Catalogue des formations |
| `/auth` | Génération / saisie de l’UID utilisateur |
| `/formation/[formationId]` | Détail d’une formation |
| `/player/[videoId]` | Lecteur (vidéo, notes, résumé) |
| `/studio` | Liste des formations (édition) |
| `/studio/formation/new` | Création d’une formation |
| `/studio/formation/[id]` | Éditeur formation / chapitres / vidéos |

Les pages sont des Client Components (`'use client'`).

## Architecture

```
src/
├── app/              # Routes App Router
├── components/       # UI (lecteur, notes, studio…)
├── services/         # Clients API (api.ts, studio.api.ts)
├── stores/           # Stores Zustand
├── types/            # Types partagés
└── utils/            # Helpers
```

Alias de chemins : `@/*` → `./src/*`.

### Authentification

Pas de JWT. Un UID (UUID) est stocké dans `localStorage` (`user_uid`).  
`AuthGuard` redirige vers `/auth` si l’UID est absent. Les requêtes envoient l’en-tête `X-User-UID`.

### Stores Zustand

| Store | Rôle |
|-------|------|
| `auth.store` | UID utilisateur |
| `catalog.store` | Formations côté apprenant |
| `studio.store` | CRUD studio |
| `theme.store` | Thème `light` / `dark` / `system` |
| `player.store` | Progression vidéo (debounce 500 ms) |

### API

- `src/services/api.ts` — client Axios + normalisation des formations
- `src/services/studio.api.ts` — façade CRUD studio (formations, chapitres, vidéos, documents, ordre)

Le stream vidéo : `GET ${NEXT_PUBLIC_API_URL}/videos/{id}/stream`.

## Docker

Build multi-stage (image Node 24 Alpine, mode standalone) :

```bash
docker build -t e-learning-front \
  --build-arg NEXT_PUBLIC_API_URL=http://localhost:8000 \
  .

docker run -p 3000:3000 e-learning-front
```

## Licence

Projet privé.
