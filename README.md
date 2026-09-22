# Cladèse

**Votre plateforme e-learning, auto-hébergée, avec l'IA intégrée à vos cours.** Hébergez vos
formations vidéo et audio, suivez la progression, prenez des notes liées au passage de la vidéo ;
l'IA transcrit les leçons, rédige des résumés et répond aux questions en citant les passages utilisés.

[![Licence](https://img.shields.io/badge/licence-AGPL%20v3-blue)](LICENSE)
[![Documentation](https://img.shields.io/badge/docs-edwinalkins.github.io-informational)](https://edwinalkins.github.io/e-learning/)
[![Déploiement](https://img.shields.io/badge/d%C3%A9ploiement-Docker%20Compose-2496ED)](#démarrage-rapide)
[![IA](https://img.shields.io/badge/IA-locale%20ou%20distante-success)](#lia-et-vos-données)
[![Clients](https://img.shields.io/badge/clients-web%20%C2%B7%20Android%20%C2%B7%20iOS%20%C2%B7%20Linux-informational)](#architecture)

![Démonstration : catalogue, formation, question à l'assistant, lecteur avec résumé et notes, studio](docs/assets/media/demo.gif)

<sub>Cours filmé : les présentations officielles des versions de Blender, publiées sur la chaîne
YouTube de Blender et réutilisées sous licence [Creative Commons Attribution](https://creativecommons.org/licenses/by/3.0/).</sub>

**[Documentation](https://edwinalkins.github.io/e-learning/)** ·
[Démarrage rapide](#démarrage-rapide) ·
[Configuration](#configuration) ·
[L'IA et vos données](#lia-et-vos-données) ·
[Sécurité](#sécurité) · [FAQ](#faq)

- **Formations → chapitres → leçons** vidéo ou audio, avec documents rattachés (PDF, Office, Markdown, images) ;
- **reprise de lecture** et progression par leçon, chapitre et formation ;
- **notes horodatées** en Markdown, un clic ramène au passage ;
- **studio** : création, téléversement, réordonnancement, conversion automatique en arrière-plan ;
- **import d'un dossier existant** `Formation/Chapitre/leçon` en une commande ;
- **transcription Whisper**, **résumés** éditables et **assistant par formation** qui cite ses sources ;
- **modèle au choix** : LM Studio ou Ollama en local, ou tout fournisseur compatible OpenAI ;
- **web et mobile** : front Next.js, application Flutter pour Android, iOS et Linux.

## Ce qu'il est, et ce qu'il n'est pas

Une plateforme de formation pour un **usage personnel** ou une **équipe de confiance**, qui garde
médias, base et index sur votre infrastructure. Ce n'est **pas** un LMS commercial : pas de comptes
avec mot de passe ni de rôles pour l'instant.

| Besoin | Cladèse | Sinon |
| --- | --- | --- |
| Héberger et suivre vos propres formations vidéo | ✅ | — |
| Une plateforme privée pour une petite équipe | ✅ | Sur un réseau privé, ou derrière une authentification |
| Transcription, résumés et questions sur le cours sans service tiers imposé | ✅ | Modèle local ou distant, à configurer |
| Reprendre une bibliothèque de cours rangée en dossiers | ✅ | [`e-learning-cli reconcile`](#cli) |
| Application mobile | ✅ côté apprenant | Le studio reste sur le web |
| Comptes, SSO, rôles formateur / apprenant | ❌ | Un proxy authentifiant devant l'instance ([détails](#sécurité)) |
| Vendre des formations, inscriptions, certificats, SCORM | ❌ | [Moodle](https://moodle.org), [Open edX](https://openedx.org) |

## Compatibilité

| | Pris en charge |
| --- | --- |
| Déploiement | Docker avec le plugin Compose v2 |
| Dépôt | Git avec [Git LFS](https://git-lfs.com) (images, vidéo, polices) |
| Développement hors Docker | Python 3.14+ et [uv](https://docs.astral.sh/uv/), Node 22+, ffmpeg |
| Vidéo | MP4, WebM, MKV, AVI, MOV, M4V, WMV, FLV — hors MP4, converti en MP4 H.264/AAC |
| Audio | MP3, WAV, M4A, AAC, OGG, FLAC, WMA, Opus — hors MP3, converti en MP3 |
| Documents | PDF, DOC(X), PPT(X), XLS(X), ODT/ODS/ODP, Markdown, texte, CSV, images |
| Modèle de langage | Tout point d'accès `/v1/chat/completions` compatible OpenAI, ou `gemini-cli` |
| Mobile | Flutter 3.47+ ; Android (SDK 37 pour compiler), iOS, Linux desktop |
| Navigateurs | Firefox, Chrome et Safari récents |

Ressources mesurées au repos : **≈ 2,3 Go de mémoire** (API et worker chargent chacun le modèle
d'embeddings), plus ≈ 1 Go par transcription Whisper `base` en cours. Image de l'API ≈ 7 Go. Pas de
GPU requis.

## Démarrage rapide

```bash
git lfs install           # une fois par machine, avant le clone
git clone https://github.com/EdwinAlkins/e-learning.git
cd e-learning
cp .env.template .env      # VIDEOS_HOST_PATH : dossier de vos médias
docker compose up -d --build
```

- Front : <http://localhost:3000> — **Generate New UID**, puis **Studio** pour créer une formation
- API : <http://localhost:8000> — documentation OpenAPI sur `/api-docs` si `APP_DEBUG=true`

> **Lancez depuis la racine du dépôt.** `e-learning-api/docker-compose.yml` sert au développement de
> l'API seule et ne démarre ni le front ni Qdrant.

> **Git LFS est requis.** Les images, la vidéo de démonstration et les polices sont stockées avec
> [Git LFS](https://git-lfs.com). Sans `git lfs install` (paquet `git-lfs`) avant le clone, vous
> récupérez des fichiers pointeurs de quelques centaines d'octets à la place : les icônes du front
> manquent et le build échoue. Sur un dépôt déjà cloné, `git lfs install && git lfs pull` répare.

**Aucun modèle de langage n'est nécessaire pour démarrer** : catalogue, lecteur, progression, notes,
documents et studio fonctionnent sans. Renseignez `APP_OPENAI_BASE_URL` pour activer résumés et
assistant. Le premier démarrage télécharge le modèle d'embeddings depuis Hugging Face.

Vous avez déjà des vidéos rangées en `Formation/Chapitre/leçon` sous `VIDEOS_HOST_PATH` :

```bash
docker compose exec api e-learning-cli reconcile
```

Arrêt : `docker compose down`. Mise à jour : `./scripts/backup.sh && git pull && docker compose up -d --build`.

| Service | Rôle | Port |
| --- | --- | --- |
| `front` | Interface apprenant et studio | `3000` |
| `api` | API REST, stream des médias | `8000` |
| `worker` | Jobs : conversion, transcription, résumé, indexation | — |
| `migrate` | Migrations Alembic, une fois au démarrage | — |
| `postgres` | Base de données | `5432` |
| `rabbitmq` | File des jobs, console de gestion | `5672`, `15672` |
| `qdrant` | Index vectoriel de l'assistant | `6333` |

## Configuration

Tout passe par `.env` (voir [`.env.template`](.env.template)). Les variables principales :

| Variable | Rôle |
| --- | --- |
| `VIDEOS_HOST_PATH` | Dossier hôte des formations, monté sur `/app/videos` |
| `NEXT_PUBLIC_API_URL` | URL de l'API vue par le navigateur — **figée au build** du front |
| `APP_CORS_ORIGINS` | Origines autorisées, liste JSON |
| `APP_OPENAI_BASE_URL` / `_API_KEY` / `_MODEL` | Modèle de langage (résumés, assistant) |
| `APP_SUMMARY_STRATEGY` | `openapi` ou `gemini` |
| `APP_EMBEDDING_BASE_URL` | Vide : embeddings locaux (`sentence-transformers`) ; renseignée : API distante |
| `APP_WORKER_PREFETCH` | Jobs en parallèle par worker (défaut `3`) |
| `APP_MAX_UPLOAD_SIZE` | Taille maximale d'un téléversement, en octets |
| `APP_DEBUG` | Interface OpenAPI et UID de repli — `false` en production |

Référence complète : [Configuration](https://edwinalkins.github.io/e-learning/configuration.html).

## L'IA et vos données

| Étape | Moteur | Où ça tourne | Résultat |
| --- | --- | --- | --- |
| Transcription | Whisper (`base` par défaut) | Worker, en local | `leçon.txt` à côté du média |
| Résumé | LLM compatible OpenAI, ou `gemini-cli` | Là où pointe `APP_OPENAI_BASE_URL` | `leçon.md` à côté du média |
| Indexation | `sentence-transformers` ou API d'embeddings | Worker, en local par défaut | Vecteurs dans Qdrant |
| Question | Embeddings + LLM | API | Réponse et sources |

- **Les fichiers médias ne quittent jamais le serveur.**
- Avec un **modèle distant**, le texte des transcriptions et les extraits retrouvés sont envoyés à ce
  fournisseur. Avec un modèle local et les embeddings par défaut, **aucun contenu ne sort**.
- L'assistant cherche uniquement dans la formation courante et affiche ses sources. Comme tout
  modèle de langage, **il peut se tromper** : les sources servent à vérifier.
- L'IA travaille sur la **parole transcrite et le texte des documents** ; elle ne voit pas l'image.

Détails, limites et modèles : [Transcription et IA](https://edwinalkins.github.io/e-learning/ai.html).

## Architecture

```
e-learning/
├── docker-compose.yml   # Pile complète : Postgres, RabbitMQ, Qdrant, migrations, API, worker, front
├── .env.template
├── e-learning-api/      # FastAPI, architecture hexagonale / DDD, CLI et worker
├── e-learning-front/    # Next.js 16 (App Router), React 19, MUI 7
├── e-learning-mobile/   # Flutter, parcours apprenant
├── scripts/backup.sh    # Sauvegarde / restauration de la base
├── docs/                # Site de documentation (HTML statique, GitHub Pages)
└── dev-tools/           # Outillage : données de démo, captures et vidéo de présentation
```

- **API hexagonale** : `presentation → infrastructure → application → domain`, vérifié par
  `import-linter` ; le domaine n'importe ni FastAPI, ni SQLAlchemy, ni Pydantic.
- **Jobs lourds hors requête** : conversion, transcription, résumé et indexation sont publiés sur
  RabbitMQ **après commit** et exécutés par `e-learning-worker`. Les clients suivent l'avancement
  par polling.
- **Disque et base réconciliés** : chaque fichier a un chemin relatif unique ; l'ordre est une
  colonne `position`, réordonner ne renomme rien. Transcriptions et résumés sont des fichiers
  voisins du média.
- **Identité anonyme** : un UUIDv7 dans l'en-tête `X-User-UID` porte progression et notes.

Plus loin : [Architecture](https://edwinalkins.github.io/e-learning/architecture.html) ·
[API HTTP](https://edwinalkins.github.io/e-learning/api.html) ·
[`e-learning-api/API.md`](e-learning-api/API.md).

## Développement

Infrastructure dans Docker, applications en local :

```bash
docker compose up -d postgres rabbitmq qdrant

# API
cd e-learning-api
cp .env.template .env
uv sync --group ai --group dev
uv run alembic upgrade head
uv run e-learning-api          # http://localhost:8000
uv run e-learning-worker       # second terminal

# Front
cd e-learning-front
cp .env.template .env.local
npm ci
npm run dev                    # http://localhost:3000

# Mobile
cd e-learning-mobile
cp .env.template .env          # obligatoire : embarqué comme asset
flutter pub get && flutter run
```

Qualité :

```bash
cd e-learning-api
uv run pytest tests/unit/          # rapides
uv run pytest tests/integration/   # Docker requis (testcontainers)
uv run ruff check . && uv run mypy && uv run lint-imports

cd e-learning-front
npm run lint && npm run build
```

Captures et vidéo de la documentation : [`dev-tools/media/`](dev-tools/media/README.md).

### CLI

```bash
docker compose exec api e-learning-cli reconcile               # disque ↔ base
docker compose exec api e-learning-cli list-videos -f "SQL"    # UUID des leçons
docker compose exec api e-learning-cli convert --glob '**/*.*' # conversion web en lot
docker compose exec api e-learning-cli transcribe -v <uuid> --model small --language fr
docker compose exec api e-learning-cli summary -v <uuid>
docker compose exec api e-learning-cli index-rag               # réindexer l'assistant
```

## Sauvegardes

[`scripts/backup.sh`](scripts/backup.sh) sauvegarde **la base PostgreSQL uniquement** (`pg_dump`),
puis applique la rotation.

```bash
./scripts/backup.sh                    # créer une archive
./scripts/backup.sh list               # lister
./scripts/backup.sh restore            # restaurer la plus récente
./scripts/backup.sh restore backups/e-learning-2026-08-05_120000.dump
./scripts/backup.sh prune              # appliquer la rotation seule
```

| Variable | Défaut | Rôle |
| --- | --- | --- |
| `BACKUP_DIR` | `./backups` | Dossier des archives |
| `BACKUP_KEEP` | `7` | Archives conservées |
| `COMPOSE_FILE` | `./docker-compose.yml` | Fichier Compose |
| `ENV_FILE` | `./.env` | Fichier d'environnement |

```cron
0 2 * * * cd /chemin/vers/e-learning && ./scripts/backup.sh >> /var/log/e-learning-backup.log 2>&1
```

> **Les médias ne sont pas dans l'archive.** Vidéos, documents, transcriptions et résumés vivent sous
> `VIDEOS_HOST_PATH` : sauvegardez ce dossier séparément (restic, rsync, snapshots). Qdrant se
> reconstruit avec `e-learning-cli index-rag`.

## Sécurité

**Il n'y a pas d'authentification intégrée.** L'UID est un identifiant de suivi, pas un secret :
toute personne qui atteint le front ou l'API peut lire le catalogue, téléverser et supprimer.

- Gardez l'instance **sur un réseau privé** (VPN, Tailscale) ou **derrière un proxy authentifiant**
  (authentification HTTP, Authelia, Authentik, oauth2-proxy). Seul le VPN convient aussi à
  l'application mobile.
- Le compose publie **PostgreSQL, RabbitMQ (`guest` par défaut) et Qdrant** sur toutes les
  interfaces : en production, retirez ces ports ou liez-les à `127.0.0.1`, et changez les
  identifiants par défaut.
- `APP_DEBUG=false` en production : le mode debug expose l'interface OpenAPI et accepte les requêtes
  sans UID.

Recettes : [Exposer l'instance](https://edwinalkins.github.io/e-learning/installation.html#exposer).

## FAQ

**Mes vidéos sont-elles envoyées à un service d'IA ?**
Non. Les fichiers restent sur votre serveur ; transcription et embeddings y sont calculés. Seul du
texte part vers le modèle de langage, et uniquement si vous configurez un fournisseur distant.

**Faut-il une carte graphique ?**
Non. Tout fonctionne sur processeur ; la transcription est plus lente et se fait en arrière-plan.

**Peut-on l'utiliser sans IA ?**
Oui. Seuls les résumés et l'assistant ont besoin d'un modèle de langage.

**Comment un apprenant retrouve-t-il sa progression sur un autre appareil ?**
Il copie son UID depuis l'en-tête de l'application et le saisit sur l'autre appareil, web ou mobile.

**Une formation ajoutée sur le disque n'apparaît pas.**
Lancez `e-learning-cli reconcile`, ou `APP_RECONCILE_ON_STARTUP=true`. Vérifiez les trois niveaux
`Formation/Chapitre/fichier`.

**Une vidéo ne se lit pas dans le navigateur.**
Le conteneur est MP4 mais le codec ne l'est pas (HEVC par exemple) : **Convertir pour le web** dans
le studio la ré-encode en H.264/AAC.

**Changer `NEXT_PUBLIC_API_URL` n'a aucun effet.**
La valeur est intégrée au build : `docker compose build front && docker compose up -d front`.

## Licence

[GNU AGPL v3](LICENSE).
