# API Documentation

## Authentification

Toute route est fermée par défaut. Seules `POST /auth/login`, `POST /auth/logout`,
`/`, `/health`, `/ready` et `/metrics` sont publiques.

Le jeton (JWT HS256, `sub` = id utilisateur, durée `APP_ACCESS_TOKEN_EXPIRE_MINUTES`)
est accepté de deux façons :

| Transport | Clients | Détail |
|-----------|---------|--------|
| `Authorization: Bearer <token>` | mobile, Swagger, scripts | prioritaire si présent |
| cookie `access_token` | web | posé par `/auth/login` : `HttpOnly`, `SameSite=Lax`, `Secure` hors `localhost` |

Avec le cookie, les requêtes d'écriture (`POST`, `PUT`, `PATCH`, `DELETE`) doivent aussi
porter le header `X-Requested-With` (valeur libre, ex. `XMLHttpRequest`) : protection CSRF.
Sans lui → `403`. Les lectures (`<video src>`, liens de téléchargement) n'en ont pas besoin.

Le rôle n'est pas lu dans le jeton : le compte est relu en base à chaque requête, un
retrait du rôle admin ou une désactivation prend donc effet immédiatement.

| Rôle | Droits |
|------|--------|
| anonyme | routes publiques uniquement |
| apprenant (`is_admin=false`) | catalogue, vidéos, documents, RAG, ses notes, sa progression, sa consommation |
| admin (`is_admin=true`) | tout, plus le studio (écritures) et `/admin/users` |

Codes : `401` = pas de jeton, jeton invalide ou expiré, compte désactivé ;
`403` = rôle insuffisant (ou header CSRF manquant) ; `429` = trop d'échecs de connexion
(5 par email ou par IP sur 15 min, header `Retry-After`).

Notes et progression restent cloisonnées par utilisateur, admin compris.

Premier admin : créé au démarrage depuis `APP_FIRST_ADMIN_EMAIL` / `APP_FIRST_ADMIN_PASSWORD`
s'il n'existe pas (idempotent, le mot de passe n'est jamais réécrit). Autres admins :
`uv run e-learning-cli create-admin --email <email>` ou `POST /admin/users`.

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

- `POST /auth/login` (public) — `application/x-www-form-urlencoded` `username` (email) + `password`
  → `{"access_token", "token_type": "bearer", "expires_in"}` + cookie `access_token`.
  `401` au message unique (email ou mot de passe), compte désactivé → `401`, `429` si bloqué.
- `POST /auth/logout` (public) → `204`, efface le cookie
- `GET /auth/me` → `{"id", "email", "full_name", "is_admin"}`
- `PATCH /auth/me/password` body `{"current_password", "new_password"}` → `204`
  (`400` si mot de passe actuel faux, `422` si le nouveau fait moins de 8 ou plus de 128 caractères)

### Comptes (admin)

- `GET /admin/users?offset=0&limit=50` (limit ≤ 200) → `{"items": [UserResponse], "total"}`
- `POST /admin/users` body `{"email", "password", "full_name"?, "is_admin"?}` → `201` ; email déjà pris → `409`
- `PATCH /admin/users/{id}` body `{"full_name"?, "is_admin"?, "is_active"?, "password"?}` —
  champ absent = inchangé, `full_name: null` efface le nom
- `DELETE /admin/users/{id}` → `204`, supprime aussi ses notes, sa progression et sa consommation

`UserResponse` : `{"id", "email", "full_name", "is_admin", "is_active", "created_at"}` (jamais de mot
de passe ni de hash). Un admin ne peut ni se retirer le rôle admin, ni se désactiver, ni se
supprimer lui-même → `409`.

### Formations (lecture — apprenant)

- `GET /formations` → catalogue (`id` UUID, `name`, `slug`, `chapters[].videos[]` / `chapters[].documents[]` avec `position`, statuts + `active_jobs`)
- `GET /formations/{formation_id}`
- `POST /formations/{formation_id}/ask` body `{"question"}` → `{"answer", "citations": [{"video_id","title","source","excerpt"}]}` (RAG)

### Studio (écriture — admin)

Toutes les routes de cette section et les écritures listées sous *Videos* et *Documents*
sont réservées aux admins (`403` pour un apprenant).

- `POST /formations/{formation_id}/index` → `202` indexation RAG formation (job `rag_index_formation`)

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
- `PUT /videos/{id}/summary` body `{"summary"}` (admin)
- `POST /videos/{id}/summary/generate` (admin) → `202` + `VideoResponse` (`summary_status=processing`, job `summary`)
- `GET /videos/{id}/transcription` → `{"content"}`
- `POST /videos/{id}/transcription` (admin) → `202` + `VideoResponse` (`transcription_status=processing`, job `transcription`)
- `POST /videos/{id}/conversion` (admin) → `202` + `VideoResponse` (reprise / relance ffmpeg, job `media_conversion`)

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

- `GET /docs/chapters/{chapter_id}`
- `POST /chapters/{id}/docs` multipart `title` + `file` + `video_id?` (admin) — `422` si extension refusée
- `PATCH /docs/{document_id}` body `{"title"?,"video_id"?}` — `video_id: null` détache (admin)
- `DELETE /docs/{document_id}` (admin)
- `GET /docs/{document_id}/file`

### OpenAPI (debug)

- `/api-docs`, `/api-redoc`, `/openapi.json` — bouton *Authorize* branché sur `/auth/login`
  (saisir l'email dans le champ `username`)
