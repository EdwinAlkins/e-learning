# dev-tools

Outillage de mainteneur. Rien ici n'est importé par les applications, copié dans les images
Docker ou exécuté en CI : chaque dossier a ses propres dépendances et son propre README.

| Dossier | Contenu |
| --- | --- |
| [`media/`](media/) | Scripts Playwright et ffmpeg qui créent une formation de démonstration, capturent les écrans et produisent la vidéo de présentation utilisée par le site `docs/` |

Deux règles valent pour tout ce qui est ajouté ici :

- **Aucun détail de déploiement dans le code.** URLs, identifiants et noms de formation
  viennent de l'environnement, avec une valeur locale par défaut. Rien qui désigne une
  instance précise n'est commité.
- **Les sorties ne sont pas versionnées.** Tout ce qui est généré reste dans le `out/` de
  l'outil ; seule la sélection promue dans `docs/assets/` est commitée.
