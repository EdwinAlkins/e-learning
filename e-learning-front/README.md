# e-learning-front

Frontend de la plateforme e-learning : catalogue de formations, lecteur vidéo/audio, notes, et studio d’édition (formations, chapitres, vidéos, documents).

## Stack

- **Next.js** 16 (App Router) + **React** 19 + **TypeScript**
- **MUI** v9 (`@mui/material`) — pas de Tailwind
- **TanStack Query** — cache et synchronisation de l’état serveur
- **Zustand** — état strictement client (session, thème, lecteur)
- **Axios** — client HTTP avec session cookie `HttpOnly` et protection anti-CSRF
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
| `npm run typecheck` | Vérification TypeScript sans émission |
| `npm test` | Tests unitaires et composants (Vitest) |
| `npm run test:watch` | Vitest en mode interactif |
| `npm run test:coverage` | Rapport de couverture Vitest |
| `npm run test:e2e` | Parcours navigateur Playwright |
| `npm run check` | ESLint, TypeScript et tests Vitest |

Pour exécuter les tests navigateur la première fois :

```bash
npx playwright install chromium
```

## Routes

| Route | Rôle |
|-------|------|
| `/` | Catalogue des formations |
| `/auth` | Connexion email + mot de passe |
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
├── components/       # UI partagée et composants historiques
├── entities/         # DTO, mapping et modèles d'entités
├── features/         # APIs et logique regroupées par fonctionnalité
├── shared/api/       # Client HTTP, erreurs et validation de contrats
├── stores/           # État client Zustand uniquement
├── types/            # Types frontend partagés
└── utils/            # Helpers
```

Alias de chemins : `@/*` → `./src/*`.

### Authentification

`POST /auth/login` pose un cookie de session `HttpOnly`, illisible en JavaScript. La session est
chargée avec `GET /auth/me` et Axios envoie le cookie avec `withCredentials`. Les écritures portent
également `X-Requested-With: XMLHttpRequest`, exigé par l’API comme protection anti-CSRF. Un `401`
invalide la session locale ; un `403` conserve la session et affiche un refus d’accès.

### Gestion de l’état

Les formations utilisent un cache TanStack Query partagé entre le catalogue, le détail et le
Studio. Les clés canoniques sont `['formations']` et `['formation', id]`; les mutations Studio
mettent à jour ces deux vues ou les invalident. Les progressions, la consommation IA et la liste
paginée des comptes utilisent également des queries dédiées. Le Player confie au même cache les
résumés, documents, notes et positions initiales. Il n’existe plus de copie séparée du catalogue
dans un store Studio.

Zustand reste réservé à l’état client :

| Store | Rôle |
|-------|------|
| `auth.store` | Session et utilisateur courant |
| `theme.store` | Thème `light` / `dark` / `system` |
| `player.store` | Progression vidéo (debounce 500 ms) |

### API

- `src/shared/api/http-client.ts` — Axios, cookie de session, CSRF et erreurs 401/403 ;
- `src/shared/api/errors.ts` — erreurs réseau et violations de contrat ;
- `src/features/*/api` — endpoints propres à chaque feature ;
- `src/entities/formation` — DTO Zod stricts et mapping vers les modèles frontend.

## Tests

- `src/**/*.test.ts(x)` : tests Vitest, Testing Library et MSW ;
- `src/test/` : serveur MSW et initialisation commune ;
- `e2e/` : parcours Playwright login/catalogue, Player et réordonnancement Studio avec API
  interceptée, donc sans backend requis.

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

[GNU AGPL v3](../LICENSE), comme le reste du projet.
