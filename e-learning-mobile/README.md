# Cladèse Mobile

Application Flutter **apprenant** pour la plateforme e-learning.

## Périmètre couvert

- Auth UID (`X-User-UID`)
- Catalogue + détail formation + progressions
- **Lecteur vidéo / audio** multi-plateforme
  - mobile : `video_player` + `chewie` (vidéo), `just_audio` + `audio_session` (audio)
  - desktop (Linux/Windows/macOS) : `media_kit` (libmpv), vidéo **et** audio
  - reprise de lecture, sauvegarde debounce 500 ms (flush ≤ 5 s, sur pause,
    passage en arrière-plan et sortie d'écran)
  - barre de progression `position / durée · %`, vitesse de lecture, ±10 s
  - états de conversion : « Conversion en cours… », échec + relance
  - navigation vidéo précédente / suivante, split view en paysage
- **Notes** : création liée au temps courant, liste triée par timecode, seek au
  tap, édition inline, suppression confirmée, rendu Markdown
- **Résumé / IA** : lancement transcription, génération et régénération du
  résumé, édition Markdown avec aperçu, polling des jobs (3 s, suspendu en
  arrière-plan)
- Documents de la vidéo : ouverture et téléchargement système
- Assistant RAG minimal (sans réindexation)
- Thème clair / sombre / système

Hors périmètre : studio, offline, notifications push.

## Prérequis

- Flutter **3.47+** / Dart **3.13+**
- API e-learning accessible (voir `e-learning-api/API.md`)
- Linux desktop : `sudo apt-get install -y libsecret-1-dev libmpv-dev mpv`
  (`libmpv` est requis par `media_kit`, le backend de lecture desktop)

## Configuration

```bash
cp .env.template .env   # requis : le fichier est embarqué comme asset
```

`.env` est la **configuration de base** : il suffit d'y renseigner `API_URL`,
aucun `--dart-define` n'est nécessaire en développement.

| Environnement | `API_URL` |
|---|---|
| Émulateur Android | `http://10.0.2.2:8000` |
| Simulateur iOS | `http://localhost:8000` |
| Appareil physique | `http://<IP-LAN>:8000` |
| Prod | HTTPS via `--dart-define=API_URL=https://…` |

Ordre de priorité, du plus fort au plus faible :

1. le panneau **Paramètres** de l'app (surcharge persistée par appareil) ;
2. `--dart-define=API_URL=…` — réservé aux builds CI / release ;
3. `.env` à la racine du projet ;
4. `http://10.0.2.2:8000` par défaut, si `.env` est absent.

> `.env` étant embarqué comme asset, une modification n'est prise en compte
> qu'au **relancement** de l'app (pas au hot reload). Pour changer d'URL sans
> rebuild, passer par le panneau Paramètres.

L'URL peut aussi être changée **à l'exécution** depuis le panneau **Paramètres**
(icône engrenage, présente sur tous les écrans y compris celui de connexion) :
saisie, test de joignabilité (`/health`), enregistrement persistant et retour à
la valeur du build. Le changement recrée le client HTTP, donc les écrans se
rechargent sur le nouveau serveur.

## Lancer

```bash
flutter pub get
flutter run                # utilise l'API_URL du .env
flutter run -d android
flutter run -d linux --no-enable-impeller

# Surcharge ponctuelle, sans toucher au .env :
flutter run -d android --dart-define=API_URL=http://<IP-LAN>:8000
```

### Lecture vidéo sur Linux : désactiver Impeller

Sur Linux desktop, la lecture vidéo **fait planter l'application** avec le
backend de rendu Impeller, devenu le défaut de Flutter. `media_kit` affiche la
vidéo via une *texture externe* dans un contexte EGL isolé, et la destruction de
cette texture — au moment où l'on quitte le lecteur — provoque un
déréférencement de pointeur nul dans le thread raster du moteur :

```text
io.flutter.rast[…]: segfault at 0 … in libflutter_linux_gtk.so
```

Le crash est dans le moteur Flutter, pas dans le code de l'app ni dans
`media_kit`.

**Aucune action requise :** `linux/runner/main.cc` force le backend historique
au démarrage, quel que soit le mode de lancement (`flutter run`, bundle exécuté
directement, ou depuis un lanceur de bureau). Supprimer le bloc
`disable_impeller()` de ce fichier pour repasser sur Impeller le jour où le
défaut est corrigé en amont.

Un réglage externe reste prioritaire, pour tester sans toucher au code :

```bash
FLUTTER_ENGINE_SWITCHES=0 build/linux/x64/debug/bundle/e_learning_mobile
```

Android et iOS ne sont pas concernés : ils utilisent `video_player`, pas
`media_kit`.

Pour produire un **APK** et l’installer via **adb** (sans `flutter run`), voir
[docs/how-to-build-android.md](docs/how-to-build-android.md).

> Note : les modèles sont en Dart immuable manuel (freezed 3.x incompatible analyzer/Dart 3.13 au moment du scaffold).

## Endpoints consommés (API.md)

- `POST /auth/generate`, `POST /auth/restore`
- `GET /formations`, `GET /formations/{id}`
- `POST /formations/{id}/ask`
- `GET/POST /progress/{video_id}`, `GET /progress/formations`, `GET /progress/formation/{id}`
- `GET /videos/{id}/stream`
- `GET/PUT /videos/{id}/summary`, `POST /videos/{id}/summary/generate`
- `POST /videos/{id}/transcription`, `POST /videos/{id}/conversion`
- `GET/POST /notes/{video_id}`, `PUT/DELETE /notes/{note_id}`
- `GET /docs/chapters/{chapter_id}`, `GET /docs/{id}/file`
