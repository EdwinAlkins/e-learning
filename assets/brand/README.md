# Identité visuelle — icônes

## Master

`icon-master.png` — 1254 px, RGBA, fond transparent. Seule source conservée.

Deux variantes en dérivent :

- **transparente** — favicon, manifest `purpose: "any"`, launcher Android.
  Simple redimensionnement du master.
- **plein cadre** — icône iOS et manifest `purpose: "maskable"`, où le système
  applique son propre masque et refuse la transparence. Le master est réduit à
  ~70 % puis centré sur un fond plein `#10284b`, et le canal alpha est retiré :
  un PNG avec alpha fait échouer la validation App Store.

Un master aplati sur blanc existait aussi ; il a été supprimé. Aucune icône du
projet n'utilise de fond blanc, et il n'était la source d'aucune des deux
variantes ci-dessus.

## Fichiers dérivés versionnés

| Chemin | Taille | Variante |
|---|---|---|
| `e-learning-mobile/ios/Runner/Assets.xcassets/AppIcon.appiconset/Icon-App-1024x1024@1x.png` | 1024 | plein cadre |
| `e-learning-mobile/android/app/src/main/res/mipmap-xxxhdpi/ic_launcher.png` | 192 | transparente |
| `e-learning-front/public/icon-192.png` | 192 | transparente |
| `e-learning-front/public/icon-512.png` | 512 | transparente |
| `e-learning-front/public/icon-maskable-512.png` | 512 | plein cadre |
| `docs/assets/logo.png` | 192 | transparente |

## Pourquoi un seul fichier par plateforme

Ne pas réintroduire les déclinaisons par taille ou par densité : elles sont
produites par les chaînes de build.

- **iOS** — depuis Xcode 14, un `AppIcon.appiconset` accepte une entrée unique
  `1024x1024` en `idiom: "universal"`. `actool` génère les 14 autres tailles à
  la compilation. Le PNG doit rester sans canal alpha, sinon la validation
  App Store échoue.
- **Android** — `minSdk = 26`, et le système redimensionne depuis la densité
  disponible la plus proche. Le fichier est placé en `mipmap-xxxhdpi` (192 px)
  pour que toutes les densités inférieures soient obtenues par réduction,
  jamais par agrandissement. Les dossiers `mipmap-mdpi` à `mipmap-xxhdpi` ont
  été supprimés.
- **Front** — les conventions Next.js `src/app/icon.png` et
  `src/app/apple-icon.png` recopiaient des rendus déjà présents dans `public/`.
  `layout.tsx` déclare désormais `metadata.icons` pointant sur ces derniers.
- **Docs** — le site se déploie seul et a besoin de sa propre copie. Elle est
  dimensionnée à 192 px : le plus grand affichage est `.hero .logo` à 5,5 rem
  (88 px), soit 176 px en écran @2x.

Les fichiers retirés lors de cette consolidation sont conservés dans
`backups/icons-20260916/` (dossier non versionné).
