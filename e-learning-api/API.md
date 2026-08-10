# API Documentation

## Authentification

La plupart des endpoints nécessitent :
```
X-User-UID: <uuid>
```

Endpoints publics : `/`, `/health`, `/ready`, `/auth/*`, `/formations*` (lecture), `/videos/*`, téléchargement `/docs/{id}/file`.

En `APP_DEBUG=true`, un UID de debug est utilisé si le header est absent.

## Modèle vidéo (catalogue)

Les réponses catalogue / studio exposent sur chaque vidéo :

| Champ | Valeurs |
|-------|---------|
| `kind` | `video` \| `audio` |
| `processing_status` | `ready` \| `processing` \| `failed` |
| `transcription_status` | `none` \| `processing` \| `ready` \| `failed` |
| `summary_status` | `none` \| `processing` \| `ready` \| `failed` |
| `active_jobs` | liste des jobs actifs (`queued` / `running`) |

### `active_jobs[]`

```json
{
  "id": "<uuid>",
  "kind": "media_conversion|transcription|summary|rag_index_video|rag_index_formation",
  "status": "queued|running",
  "progress": 0,
  "message": "…"
}
```

`progress` : `0..100`. Poller `GET /formations` (ou la formation) toutes les ~3 s tant qu’un statut est `processing` pour suivre l’évolution.

Les jobs terminés (`succeeded` / `failed`) ne figurent plus dans `active_jobs` ; les colonnes `*_status` restent la projection métier.

## Endpoints

### Health

- `GET /` → `{"message": "health ok"}`
- `GET /health` → `{"status": "ok"}`
- `GET /ready` → vérifie Postgres

### Auth

- `POST /auth/generate` → `{"uid": "<uuid>"}`
- `POST /auth/restore` body `{"uid": "<uuid>"}` → `{"uid": "<uuid>"}`

### Formations (lecture)

- `GET /formations` → catalogue (`id` UUID, `name`, `slug`, `chapters[].videos[]` / `chapters[].documents[]` avec `position`, statuts + `active_jobs`)
- `GET /formations/{formation_id}`
- `POST /formations/{formation_id}/ask` body `{"question"}` → `{"answer", "citations": [{"video_id","title","source","excerpt"}]}` (RAG)
- `POST /formations/{formation_id}/index` → `202` indexation RAG formation (job `rag_index_formation`)

### Studio (écriture)

- `POST /formations` body `{"name"}`
- `PATCH /formations/{id}` body `{"name"}`
- `DELETE /formations/{id}`
- `POST /formations/{id}/chapters` body `{"name"}`
- `PATCH /chapters/{id}` body `{"name"}`
- `DELETE /chapters/{id}`
- `POST /chapters/{id}/videos` multipart `title` + `file` — si conversion nécessaire : `processing_status=processing` + job `media_conversion` (queue RabbitMQ)
- `PATCH /videos/{id}` JSON `{"title"}` **ou** multipart `title?` + `file?` (remplacement)
- `DELETE /videos/{id}`
- `PUT /chapters/{id}/videos/order` body `{"video_ids": [...]}` — met à jour `position` en base
- `PUT /formations/{id}/chapters/order` body `{"chapter_ids": [...]}` — réordonne les chapitres (`position` DB, slugs FS inchangés)
- `PATCH /chapters/{source}/{target}/{video_id}` body optionnel `position` / `after_video_id`

### Videos

- `GET /videos/{id}/stream` (Range)
- `GET /videos/{id}/file`
- `GET /videos/{id}/summary` → `{"summary"}`
- `PUT /videos/{id}/summary` body `{"summary"}`
- `POST /videos/{id}/summary/generate` → `202` + `VideoResponse` (`summary_status=processing`, job `summary`)
- `GET /videos/{id}/transcription` → `{"content"}`
- `POST /videos/{id}/transcription` → `202` + `VideoResponse` (`transcription_status=processing`, job `transcription`)
- `POST /videos/{id}/conversion` → `202` + `VideoResponse` (reprise / relance ffmpeg, job `media_conversion`)

Après transcription ou résumé réussis, un job `rag_index_video` est enchaîné automatiquement (best-effort).

### Progress

- `GET /progress/formations`
- `GET /progress/formation/{formation_id}`
- `GET /progress/{video_id}`
- `POST /progress/{video_id}` body `{"last_position"}`

### Notes

- `GET /notes/{video_id}`
- `POST /notes/{video_id}` body `{"timecode","content"}`
- `PUT /notes/{note_id}` body `{"content"}`
- `DELETE /notes/{note_id}`

### Documents

Extensions acceptées à l'upload : `.pdf`, `.md`, `.txt`, `.csv`, `.doc`, `.docx`, `.ppt`, `.pptx`, `.xls`, `.xlsx`, `.odt`, `.ods`, `.odp`, `.png`, `.jpg`, `.jpeg`, `.webp`, `.gif`, `.svg` (pas de fichier sans extension).

- `GET /docs/chapters/{chapter_id}` (auth)
- `POST /chapters/{id}/docs` multipart `title` + `file` + `video_id?` (studio) — `422` si extension refusée
- `PATCH /docs/{document_id}` body `{"title"?,"video_id"?}` — `video_id: null` détache (auth)
- `DELETE /docs/{document_id}` (auth)
- `GET /docs/{document_id}/file`

### OpenAPI (debug)

- `/api-docs`, `/api-redoc`, `/openapi.json`
