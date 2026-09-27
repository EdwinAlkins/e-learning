# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
npm run dev      # Start dev server (http://localhost:3000) with Turbopack
npm run build    # Production build
npm run start    # Run production build
npm run lint     # ESLint (flat config, eslint.config.mjs)
npm run typecheck # TypeScript without emitting files
npm test         # Vitest unit/component tests
npm run test:e2e # Playwright browser tests
npm run check    # Lint + typecheck + Vitest
```

Vitest uses Testing Library and MSW (`vitest.config.mts`, `src/test/`). Playwright tests live in
`e2e/`; install Chromium once with `npx playwright install chromium` before running them locally.

## Environment

Copy `.env.template` to `.env.local` and set:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

The shared HTTP client (`src/shared/api/http-client.ts`) falls back to
`http://localhost:8000` if unset.

## Architecture

**Next.js App Router** — routes principales :

| Route | Rôle |
|-------|------|
| `/` | Catalogue formations |
| `/auth` | Connexion email + mot de passe (seule page publique ; `?next=` = retour après login) |
| `/formation/[formationId]` | Détail formation (id entier stringifié ; fallback nom legacy) |
| `/player/[videoId]` | Lecteur vidéo, notes, résumé |
| `/studio` | Liste formations (édition) — `/studio/*` réservé aux admins (`app/studio/layout.tsx`) |
| `/studio/users` | Gestion des comptes (création, rôle, activation, suppression) |
| `/studio/formation/new` | Créer une formation |
| `/studio/formation/[id]` | Éditeur formation / chapitres / vidéos |
| `/usage` | Consommation IA de l'utilisateur (`GET /usage?days=`) |

All pages are Client Components (`'use client'`). There is no server-side rendering in practice.

### State Management

TanStack Query owns formation server state. `src/features/catalog/queries/formation.queries.ts`
defines the shared `['formations']` and `['formation', id]` keys plus cache update helpers.
`src/features/studio/hooks/useStudioMutations.ts` applies Studio mutations to that shared cache,
including optimistic reorder rollback. Do not add a second Zustand copy of server resources.
Formation progress, usage and paginated admin users also live under their feature `queries/`
directories. The root `QueryProvider` clears all account-scoped queries on logout.

Zustand is limited to client state in `src/stores/`:

- `auth.store.ts` — utilisateur courant (`GET /auth/me`), `status` `unknown`/`authenticated`/`anonymous`, `accessDenied` (dernier 403)
- `theme.store.ts` — `'light' | 'dark' | 'system'`
- `player.store.ts` — Progression vidéo debounced 500 ms

### API Layer

- `src/shared/api/http-client.ts` — Axios `withCredentials` + header `X-Requested-With` ; 401 → session effacée, 403 → « accès refusé » sans déconnexion
- `src/shared/api/errors.ts` / `contracts.ts` — erreurs lisibles et violations explicites de contrat
- `src/entities/formation/` — DTO Zod du backend et mapping vers les modèles frontend
- `src/features/*/api/` — endpoints regroupés par auth, catalogue, formation, player, studio, usage et utilisateurs

**Studio — endpoints utilisés :**

`components/studio/formation-builder/useFormationBuilder.ts` only composes feature controllers.
Editing, dialogs, reorder/drag-and-drop and background-job polling are separated respectively into
`useFormationEditor`, `useStudioDialogs`, `useVideoReorder` and `useStudioBackgroundJobs` under
`features/studio/hooks/`.

- `GET/POST/PATCH/DELETE /formations`, chapitres, vidéos (multipart upload)
- `PUT /chapters/{chapter_id}/videos/order` — réordonnancement intra-chapitre (`putChapterVideoOrder`)
- `PATCH /chapters/{source}/{target}/{video_id}` — déplacement inter-chapitres
- Pas de `sort_order` API : ordre = tableau `videos` dans `GET /formations`

**Apprenant :**

- `GET /progress/formation/{formationId}`
- `GET /videos/{videoId}/stream` — lecteur (`VideoPlayer.tsx`)
- Notes, résumés, progression vidéo inchangés

Voir [`docs/BACKEND_STUDIO_API.md`](docs/BACKEND_STUDIO_API.md), [`docs/BACKEND_CHAPTER_VIDEO_ORDER.md`](docs/BACKEND_CHAPTER_VIDEO_ORDER.md).

### Styling

MUI (`@mui/material` v9) only — no Tailwind. Theme in `src/app/theme-provider.tsx`. Markdown editor (`@uiw/react-md-editor`) needs `data-color-mode` and CSS overrides.

### Video Player

`app/player/[videoId]/page.tsx` is a composition point. Navigation/catalog lookup, jobs and summary
controllers live in `features/player/hooks/`; server resources (summary, documents, progress and
notes) live in `features/player/queries/`. Presentation is split into `PlayerNavigation`,
`PlayerMediaPanel`, `VideoSummaryPanel` and `PlayerTabs`.

`src/components/VideoPlayer.tsx` — video.js, `video/mp4`, stream URL `${API_BASE_URL}/videos/{id}/stream`. See `docs/SUPPORT_MP3_MP4.md`.

### Authentication

`POST /auth/login` pose un cookie `HttpOnly` `access_token` (illisible en JS) : la session est
connue en appelant `GET /auth/me`. Aucun jeton n'est stocké côté front.

- `SessionGate` (layout racine) : charge la session, redirige vers `/auth?next=…` toute page non
  publique sans session, affiche la snackbar « accès refusé ».
- `AuthGuard` : cadre des pages connectées (header).
- `app/studio/layout.tsx` : un apprenant est renvoyé à `/` ; le lien Studio n'apparaît que si
  `is_admin`. Confort seulement : l'API renvoie 403.
- Médias (`VideoPlayer`, `AudioPlayer`, `VideoUploadDialog`, `documentFileUrl`) : URL directes,
  le navigateur envoie le cookie. Front et API doivent donc être sur le **même site**
  (ex. `app.example.com` / `api.example.com`, ou `localhost:3000` / `localhost:8000`) et les
  balises média ne doivent pas porter `crossOrigin="anonymous"`.

### Path Alias

`@/*` → `./src/*` (`tsconfig.json`).

<!-- BEGIN:nextjs-agent-rules -->

# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->
