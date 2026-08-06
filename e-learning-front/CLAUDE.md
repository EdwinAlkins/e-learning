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
| `/` | Catalogue formations (`AuthGuard`) |
| `/auth` | Génération / saisie UID |
| `/formation/[formationId]` | Détail formation (id entier stringifié ; fallback nom legacy) |
| `/player/[videoId]` | Lecteur vidéo, notes, résumé |
| `/studio` | Liste formations (édition) |
| `/studio/formation/new` | Créer une formation |
| `/studio/formation/[id]` | Éditeur formation / chapitres / vidéos |

All pages are Client Components (`'use client'`). There is no server-side rendering in practice.

### State Management (Zustand)

Stores in `src/stores/`:

- `auth.store.ts` — UID ; `localStorage` key `user_uid`
- `catalog.store.ts` — Formations apprenant via `apiService.getFormations()`
- `studio.store.ts` — CRUD studio via `studio.api.ts` → `apiService`
- `theme.store.ts` — `'light' | 'dark' | 'system'`
- `player.store.ts` — Progression vidéo debounced 500 ms

### API Layer

- [`src/services/api.ts`](src/services/api.ts) — Axios + `X-User-UID` ; normalisation ids API (`normalizeApiFormation`)
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

UUID in `localStorage`. No JWT. `AuthGuard` redirects to `/auth` if missing.

### Path Alias

`@/*` → `./src/*` (`tsconfig.json`).
