# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
npm run dev      # Start dev server (http://localhost:3000) with Turbopack
npm run build    # Production build
npm run start    # Run production build
npm run lint     # ESLint (flat config, eslint.config.mjs)
```

No test framework is configured.

## Environment

Copy `.env.template` to `.env.local` and set:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

The API client (`src/services/api.ts`) falls back to `http://localhost:8000` if unset.

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

### State Management (Zustand)

Stores in `src/stores/`:

- `auth.store.ts` — utilisateur courant (`GET /auth/me`), `status` `unknown`/`authenticated`/`anonymous`, `accessDenied` (dernier 403)
- `catalog.store.ts` — Formations apprenant via `apiService.getFormations()`
- `studio.store.ts` — CRUD studio via `studio.api.ts` → `apiService`
- `theme.store.ts` — `'light' | 'dark' | 'system'`
- `player.store.ts` — Progression vidéo debounced 500 ms

### API Layer

- [`src/services/api.ts`](src/services/api.ts) — Axios `withCredentials` + header `X-Requested-With` (anti-CSRF exigé par l'API sur les écritures par cookie) ; 401 → session effacée, 403 → « accès refusé » sans déconnexion ; normalisation ids API (`normalizeApiFormation`)
- [`src/services/studio.api.ts`](src/services/studio.api.ts) — Façade studio (pas de mock)

**Studio — endpoints utilisés :**

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

MUI (`@mui/material` v7) only — no Tailwind. Theme in `src/app/theme-provider.tsx`. Markdown editor (`@uiw/react-md-editor`) needs `data-color-mode` and CSS overrides.

### Video Player

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
