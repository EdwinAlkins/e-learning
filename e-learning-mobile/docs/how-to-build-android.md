# How to build — Android (APK + ADB)

Guide pour produire un APK installable et le déployer sur un téléphone Android
via `adb`, sans `flutter run`.

## Prérequis

- Flutter **3.47+** / Dart **3.13+**
- Android SDK (API **37** minimum pour compiler : `flutter_secure_storage` 11+)
- `adb` dans le `PATH`
- Téléphone : **Options développeur** + **Débogage USB** activés
- API e-learning joignable depuis le téléphone (IP LAN du PC, pas `localhost`)

```bash
cd e-learning-mobile
flutter pub get
flutter doctor
```

## 1. Détecter le téléphone

```bash
# Câble données (pas charge seule) + mode « Transfert de fichiers / MTP »
adb kill-server
adb start-server
adb devices -l
flutter devices
```

| État `adb devices` | Action |
|---|---|
| vide | Câble / port / mode USB à revoir |
| `unauthorized` | Accepter la popup « Autoriser le débogage USB » sur le téléphone |
| `device` | OK pour installer |

Si la popup n’apparaît pas : Options développeur → **Révoquer les autorisations
de débogage USB** → débrancher / rebrancher.

## 2. Construire l’APK

L’URL de l’API est lue dans `.env`, embarqué dans l’APK au moment du build : il
suffit d’y mettre la bonne valeur avant de construire. Sur un appareil physique,
utilise l’IP LAN du PC qui héberge l’API.

`--dart-define=API_URL=…` reste disponible pour surcharger `.env` sans le
modifier (utile en CI) ; les commandes ci-dessous le montrent sous cette forme.
Elle est aussi modifiable après installation depuis le panneau **Paramètres**.

```bash
# IP du PC (exemple)
ip -4 addr show scope global | grep -oP 'inet \K[\d.]+'
```

### APK debug (rapide, signature debug)

```bash
flutter build apk --debug \
  --dart-define=API_URL=http://192.168.1.17:8000
```

Sortie typique :

```text
build/app/outputs/flutter-apk/app-debug.apk
```

### APK release (optimisé)

En v0, le `build.gradle.kts` signe encore en **debug** pour le type `release`
(pratique pour tester hors store). Pour un vrai store, il faudra une keystore.

```bash
flutter build apk --release \
  --dart-define=API_URL=http://192.168.1.17:8000
```

Sortie typique :

```text
build/app/outputs/flutter-apk/app-release.apk
```

### APK split par ABI (plus léger)

```bash
flutter build apk --release --split-per-abi \
  --dart-define=API_URL=http://192.168.1.17:8000
```

Fichiers générés (ex.) :

```text
build/app/outputs/flutter-apk/app-armeabi-v7a-release.apk
build/app/outputs/flutter-apk/app-arm64-v8a-release.apk
build/app/outputs/flutter-apk/app-x86_64-release.apk
```

Sur la plupart des téléphones récents : `app-arm64-v8a-release.apk`.

## 3. Installer via ADB

```bash
# Un seul appareil branché
adb install -r build/app/outputs/flutter-apk/app-debug.apk

# Plusieurs appareils : préciser le serial
adb -s <device-serial> install -r build/app/outputs/flutter-apk/app-debug.apk
```

`-r` = réinstalle / met à jour si l’app est déjà présente.

Lancer l’app :

```bash
adb shell am start -n com.edwinalkins.e_learning_mobile/.MainActivity
```

Désinstaller :

```bash
adb uninstall com.edwinalkins.e_learning_mobile
```

## 4. Vérifier / dépanner

### L’app ne joint pas l’API

- Sur téléphone physique, **ne pas** utiliser `localhost` ni `10.0.2.2`
  (`10.0.2.2` = émulateur Android uniquement).
- Rebuild avec la bonne IP : `--dart-define=API_URL=http://<IP-LAN>:8000`
- Ou change l’URL à l’exécution dans **Paramètres** (icône engrenage).
- Le téléphone et le PC doivent être sur le **même réseau** ; le firewall du PC
  doit laisser le port `8000`.

Test rapide depuis le téléphone (même Wi‑Fi) : ouvrir
`http://<IP-LAN>:8000/health` dans le navigateur mobile.

### Build `compileSdk` / `flutter_secure_storage`

Si Gradle exige SDK 37 :

```kotlin
// android/app/build.gradle.kts
android {
    compileSdk = 37
    ...
}
```

Installer la plateforme si besoin :

```bash
sdkmanager "platforms;android-37"
```

### Logs runtime

```bash
adb logcat | grep -iE 'flutter|e_learning|AndroidRuntime'
```

## Récap one-liner

```bash
flutter build apk --debug --dart-define=API_URL=http://192.168.1.17:8000 \
  && adb install -r build/app/outputs/flutter-apk/app-debug.apk
```
