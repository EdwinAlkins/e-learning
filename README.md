# E-Learning

Plateforme e-learning : formations, chapitres, médias (vidéo / audio), documents, progression, notes, transcription et résumés.

## Architecture

```
e-learning/
├── docker-compose.yml      # Stack complète (Postgres, API, front)
├── .env.template           # Variables d'environnement
├── scripts/
│   └── backup.sh           # Sauvegarde / restauration
├── e-learning-api/         # API FastAPI (hexagonale / DDD)
└── e-learning-front/       # Front Next.js (App Router, MUI)
```


| Service    | Rôle                          | Port par défaut |
| ---------- | ----------------------------- | --------------- |
| `postgres` | Base PostgreSQL               | `5432`          |
| `migrate`  | Migrations Alembic (one-shot) | —               |
| `api`      | API REST + stream médias      | `8000`          |
| `front`    | Interface apprenant / studio  | `3000`          |


Les fichiers médias (MP4, MP3, documents) sont stockés sur le disque hôte (`VIDEOS_HOST_PATH`) et montés dans l’API sur `/app/videos`.

## Prérequis

- [Docker](https://docs.docker.com/get-docker/) + Docker Compose
- (Optionnel) Node 22+, Python ≥ 3.14 + [uv](https://docs.astral.sh/uv/) pour le développement hors Docker



## Démarrage rapide

```bash
cp .env.template .env
# Ajuster VIDEOS_HOST_PATH, mots de passe, URLs si besoin

docker compose up --build
```

- Front : [http://localhost:3000](http://localhost:3000)  
- API : [http://localhost:8000](http://localhost:8000)  
- Docs API (si `APP_DEBUG=true`) : [http://localhost:8000/api-docs](http://localhost:8000/api-docs)

Arrêt :

```bash
docker compose down
```



## Configuration

Variables principales (voir `[.env.template](.env.template)`) :


| Variable                  | Description                                    |
| ------------------------- | ---------------------------------------------- |
| `POSTGRES_*`              | Identifiants et port Postgres                  |
| `APP_DATABASE_URL`        | URL async SQLAlchemy (depuis le réseau Docker) |
| `VIDEOS_HOST_PATH`        | Dossier hôte des formations / médias           |
| `API_PORT` / `FRONT_PORT` | Ports exposés                                  |
| `NEXT_PUBLIC_API_URL`     | URL de l’API vue par le navigateur             |
| `APP_SUMMARY_STRATEGY`    | Résumés (`openapi` / `gemini`)                 |
| `APP_MAX_UPLOAD_SIZE`     | Taille max upload (octets)                     |




## Fonctionnalités

- Catalogue formations → chapitres → médias (vidéo / audio) + documents
- Association automatique documents ↔ vidéos par similarité de nom
- Player vidéo (video.js) ou audio selon le type de média
- Conversion ffmpeg en arrière-plan (MP4 H.264/AAC ou MP3) à l’upload studio
- Progression, notes horodatées, résumé / transcription
- Studio : CRUD formations, chapitres, médias, documents



## Développement



### API seule

Voir `[e-learning-api/README.md](e-learning-api/README.md)`.

```bash
cd e-learning-api
cp .env.template .env
uv sync --group ai --group dev
uv run alembic upgrade head
uv run hypercorn e_learning.main:app --reload
```

CLI utile :

```bash
uv run e-learning-cli reconcile
uv run e-learning-cli convert
uv run e-learning-cli transcribe --video-id <uuid>
uv run e-learning-cli resume --video-id <uuid>
```



### Front seul

Voir `[e-learning-front/README.md](e-learning-front/README.md)`.

```bash
cd e-learning-front
cp .env.template .env
npm ci
npm run dev
```



## Sauvegardes

Le script `[scripts/backup.sh](scripts/backup.sh)` sauvegarde **uniquement la base Postgres** (`pg_dump`).

Les médias (`VIDEOS_HOST_PATH`) ne sont pas inclus — à gérer séparément si besoin.

```bash
# Créer une sauvegarde
./scripts/backup.sh

# Lister les archives
./scripts/backup.sh list

# Restaurer la plus récente (ou une archive précise)
./scripts/backup.sh restore
./scripts/backup.sh restore backups/e-learning-2026-08-05_120000.dump

# Purger selon la rétention (défaut : 7 archives)
./scripts/backup.sh prune
```

Variables optionnelles :


| Variable       | Défaut                 | Description                   |
| -------------- | ---------------------- | ----------------------------- |
| `BACKUP_DIR`   | `./backups`            | Répertoire des dumps          |
| `BACKUP_KEEP`  | `7`                    | Nombre d’archives à conserver |
| `COMPOSE_FILE` | `./docker-compose.yml` | Fichier Compose               |
| `ENV_FILE`     | `./.env`               | Fichier d’environnement       |


Exemple cron (tous les jours à 2 h) :

```cron
0 2 * * * cd /chemin/vers/e-learning && ./scripts/backup.sh >> /var/log/e-learning-backup.log 2>&1
```



## Documentation complémentaire

- API endpoints : `[e-learning-api/API.md](e-learning-api/API.md)`
- Architecture API : `[e-learning-api/CLAUDE.md](e-learning-api/CLAUDE.md)`
- Front : `[e-learning-front/CLAUDE.md](e-learning-front/CLAUDE.md)`



## Licence

Voir le fichier `[LICENSE](LICENSE)`.