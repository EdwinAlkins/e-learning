// Contenu de la démo : trois formations fictives. Les médias sont des cartons
// titres générés par ffmpeg (voir seed.mjs) ; les résumés, documents, notes et
// progressions sont écrits via l'API pour que chaque écran ait quelque chose à
// montrer, y compris l'assistant, qui s'appuie sur les résumés et documents.
//
// Durées en secondes. `progress` est la fraction déjà vue par l'apprenant de
// démo (0 à 1). `lesson: true` désigne la leçon ouverte dans le lecteur.

const min = (m, s = 0) => m * 60 + s;

export const MAIN_FORMATION = 'Docker en pratique';

export const FORMATIONS = [
  {
    name: MAIN_FORMATION,
    chapters: [
      {
        name: 'Les bases',
        lessons: [
          {
            title: 'Pourquoi des conteneurs',
            duration: min(6, 20),
            progress: 1,
            summary: `## Pourquoi des conteneurs

- Un conteneur **isole un processus** et ses dépendances, sans embarquer un système complet comme une machine virtuelle.
- Il démarre en quelques centaines de millisecondes et partage le noyau de l'hôte.
- Le même artefact tourne à l'identique sur le poste du développeur, en CI et en production : fini le « chez moi ça marche ».

### À retenir
1. Une **image** est un modèle immuable ; un **conteneur** en est une instance en cours d'exécution.
2. L'isolation repose sur les *namespaces* et les *cgroups* du noyau Linux.
3. Un conteneur n'est pas une sécurité absolue : il réduit la surface, il ne remplace pas les mises à jour.`,
          },
          {
            title: 'Images et conteneurs',
            duration: min(9, 45),
            progress: 0.62,
            lesson: true,
            summary: `## Images et conteneurs

Une image Docker est une **pile de couches en lecture seule**. Chaque instruction du Dockerfile ajoute une couche ; le conteneur y superpose une couche inscriptible, perdue à sa suppression.

### Points clés
- \`docker pull\` télécharge une image, \`docker run\` crée **et** démarre un conteneur.
- Les couches identiques sont **partagées** entre images : dix services basés sur \`python:3.14-slim\` ne stockent la base qu'une fois.
- Un tag (\`:latest\`, \`:1.4\`) est une étiquette mobile ; le *digest* \`sha256:…\` désigne un contenu exact.

### Commandes vues
| Commande | Rôle |
|---|---|
| \`docker images\` | lister les images locales |
| \`docker ps -a\` | lister les conteneurs, arrêtés compris |
| \`docker rm -f\` | supprimer un conteneur |`,
            notes: [
              { at: 95, content: '**Couche inscriptible** : tout ce qui est écrit dans le conteneur disparaît avec lui → utiliser un volume.' },
              { at: 241, content: 'Épingler les images par *digest* en production, pas par `latest`.' },
              { at: 352, content: 'À tester : `docker history python:3.14-slim` pour voir les couches.' },
            ],
            documents: [{ title: 'Mémo des commandes', file: 'memo-commandes.md' }],
          },
          {
            title: 'Écrire un bon Dockerfile',
            duration: min(12, 10),
            progress: 0,
            summary: `## Écrire un bon Dockerfile

- **Ordonner les instructions** du moins au plus changeant : dépendances d'abord, code ensuite, pour profiter du cache.
- Utiliser un **build multi-étapes** : compiler dans une image complète, livrer dans une image minimale.
- Lancer le processus avec un **utilisateur non root** (\`USER\`).
- Préférer la forme *exec* : \`CMD ["python", "app.py"]\`, pour que les signaux atteignent le processus.
- Un \`.dockerignore\` évite d'envoyer \`.git\`, \`node_modules\` ou des secrets dans le contexte de build.`,
          },
        ],
      },
      {
        name: 'Composer une application',
        lessons: [
          {
            title: 'Services, réseaux et variables',
            duration: min(11, 30),
            progress: 0.3,
            summary: `## Services, réseaux et variables

Docker Compose décrit une application multi-conteneurs dans un fichier YAML.

- Chaque **service** devient un ou plusieurs conteneurs.
- Compose crée un **réseau par projet** : les services se joignent par leur nom (\`postgres:5432\`).
- Les variables viennent d'un fichier \`.env\` et s'injectent avec \`\${VARIABLE}\`.
- \`depends_on\` avec \`condition: service_healthy\` attend qu'une dépendance soit réellement prête, pas seulement démarrée.`,
            documents: [{ title: 'Exemple docker-compose.yml', file: 'exemple-compose.md' }],
          },
          {
            title: 'Volumes et persistance',
            duration: min(8, 5),
            progress: 0,
            summary: `## Volumes et persistance

- Un **volume nommé** est géré par Docker et survit à la suppression des conteneurs.
- Un **bind mount** monte un dossier de l'hôte : pratique en développement, dépendant du chemin.
- Les bases de données doivent **toujours** écrire dans un volume.
- \`docker compose down\` conserve les volumes ; \`down -v\` les supprime.`,
          },
          {
            title: 'Entretien : les pièges de docker compose',
            duration: min(14),
            audio: true,
            progress: 0,
            summary: `## Entretien : les pièges de docker compose

Un échange sur les erreurs rencontrées le plus souvent en équipe :

1. **Publier tous les ports** d'une base sur \`0.0.0.0\` : exposer Postgres ou RabbitMQ à tout le réseau.
2. **Oublier les healthchecks** : l'application démarre avant la base et échoue au premier appel.
3. **Mettre des secrets dans l'image** au lieu de les passer à l'exécution.
4. **Utiliser \`latest\`** et découvrir une mise à jour majeure au redéploiement.`,
          },
        ],
      },
      {
        name: 'Aller en production',
        documents: [{ title: 'Checklist avant la mise en production', file: 'checklist-production.md' }],
        lessons: [
          {
            title: 'Healthchecks et redémarrages',
            duration: min(7, 40),
            progress: 0,
            summary: `## Healthchecks et redémarrages

- Un \`healthcheck\` exécute une commande à intervalle régulier et marque le conteneur \`healthy\` ou \`unhealthy\`.
- Distinguer **vivant** (le processus répond) et **prêt** (ses dépendances aussi).
- \`restart: unless-stopped\` relance un service tombé, sauf arrêt volontaire.
- Un healthcheck trop lourd devient lui-même une charge : viser une requête simple et rapide.`,
          },
          {
            title: 'Sauvegarder ses données',
            duration: min(10, 15),
            progress: 0,
            summary: `## Sauvegarder ses données

- Sauvegarder une base avec **son outil natif** (\`pg_dump\`), jamais en copiant le volume à chaud.
- Appliquer la règle **3-2-1** : trois copies, deux supports, une hors site.
- Une sauvegarde non restaurée est une hypothèse : **tester la restauration** régulièrement.
- Automatiser la rotation pour ne pas saturer le disque.`,
          },
        ],
      },
    ],
  },
  {
    name: 'SQL pour les débutants',
    chapters: [
      {
        name: 'Premiers pas',
        lessons: [
          { title: 'Installer PostgreSQL', duration: min(5, 30), progress: 1 },
          { title: 'SELECT, WHERE et ORDER BY', duration: min(13, 20), progress: 1 },
          { title: 'Agréger avec GROUP BY', duration: min(10, 50), progress: 0.45 },
        ],
      },
      {
        name: 'Jointures',
        lessons: [
          { title: 'INNER JOIN et LEFT JOIN', duration: min(15), progress: 0 },
          { title: 'Sous-requêtes et CTE', duration: min(12, 35), progress: 0 },
        ],
      },
    ],
  },
  {
    name: 'Git au quotidien',
    chapters: [
      {
        name: "L'essentiel",
        lessons: [
          { title: 'Des commits qui racontent une histoire', duration: min(8), progress: 0 },
          { title: 'Branches, merge et rebase', duration: min(16, 40), progress: 0 },
          { title: 'Réparer une erreur sans paniquer', duration: min(11, 15), progress: 0 },
        ],
      },
    ],
  },
];

export const DOCUMENTS = {
  'memo-commandes.md': `# Mémo des commandes Docker

| Besoin | Commande |
|---|---|
| Télécharger une image | \`docker pull postgres:18-alpine\` |
| Lancer un conteneur | \`docker run -d --name db -p 5432:5432 postgres:18-alpine\` |
| Voir les journaux | \`docker logs -f db\` |
| Ouvrir un shell | \`docker exec -it db sh\` |
| Lister les couches | \`docker history postgres:18-alpine\` |
| Nettoyer | \`docker system prune\` |
`,
  'exemple-compose.md': `# Exemple de docker-compose.yml

\`\`\`yaml
services:
  postgres:
    image: postgres:18-alpine
    environment:
      POSTGRES_PASSWORD: \${POSTGRES_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s

  app:
    build: .
    depends_on:
      postgres:
        condition: service_healthy

volumes:
  pgdata:
\`\`\`
`,
  'checklist-production.md': `# Checklist avant la mise en production

1. **Ports** : seuls le proxy HTTPS et les ports publics sont publiés ; bases et brokers restent sur le réseau interne.
2. **Secrets** : aucun mot de passe dans l'image ni dans le dépôt ; tout passe par l'environnement.
3. **Images** : versions épinglées, pas de \`latest\`.
4. **Healthchecks** : chaque service a une sonde, et les dépendances attendent \`service_healthy\`.
5. **Données** : volumes nommés pour toute donnée persistante.
6. **Sauvegardes** : planifiées, avec rotation, et **une restauration testée**.
7. **Journaux** : rotation configurée pour ne pas remplir le disque.
8. **Mises à jour** : procédure écrite, sauvegarde préalable, retour arrière possible.
`,
};
