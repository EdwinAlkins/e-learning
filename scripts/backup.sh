#!/usr/bin/env bash
# Sauvegarde / restauration E-Learning (Postgres uniquement).
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="${COMPOSE_FILE:-$ROOT_DIR/docker-compose.yml}"
ENV_FILE="${ENV_FILE:-$ROOT_DIR/.env}"
BACKUP_DIR="${BACKUP_DIR:-$ROOT_DIR/backups}"
BACKUP_KEEP="${BACKUP_KEEP:-7}"
COMPOSE=(docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE")

usage() {
  cat <<EOF
Usage: $(basename "$0") [commande] [archive]

Commandes :
  backup              Créer une sauvegarde Postgres (défaut)
  list                Lister les archives
  prune               Supprimer les anciennes archives (garde BACKUP_KEEP)
  restore [archive]   Restaurer (sans argument : la plus récente)

Variables d'environnement :
  BACKUP_DIR     Répertoire des archives (défaut : ./backups)
  BACKUP_KEEP    Nombre d'archives à conserver (défaut : 7)
  COMPOSE_FILE   docker-compose.yml
  ENV_FILE       .env

Exemples :
  $(basename "$0")
  $(basename "$0") list
  $(basename "$0") restore backups/e-learning-2026-08-05_120000.dump
EOF
}

log() { printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"; }
die() { printf 'ERREUR: %s\n' "$*" >&2; exit 1; }

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "Commande introuvable : $1"
}

load_env() {
  [[ -f "$ENV_FILE" ]] || die "Fichier env introuvable : $ENV_FILE"
  # shellcheck disable=SC1090
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
  : "${POSTGRES_USER:?POSTGRES_USER manquant dans .env}"
  : "${POSTGRES_DB:?POSTGRES_DB manquant dans .env}"
}

ensure_postgres() {
  if ! "${COMPOSE[@]}" ps --status running --services 2>/dev/null | grep -qx postgres; then
    die "Le service postgres n'est pas démarré. Lancez : docker compose up -d postgres"
  fi
}

latest_archive() {
  local latest
  latest="$(ls -1t "$BACKUP_DIR"/e-learning-*.dump 2>/dev/null | head -n1 || true)"
  [[ -n "$latest" ]] || die "Aucune archive dans $BACKUP_DIR"
  printf '%s' "$latest"
}

cmd_backup() {
  require_cmd docker
  load_env
  ensure_postgres

  local stamp archive
  stamp="$(date '+%Y-%m-%d_%H%M%S')"
  archive="$BACKUP_DIR/e-learning-${stamp}.dump"
  mkdir -p "$BACKUP_DIR"

  log "Dump Postgres (${POSTGRES_DB})…"
  "${COMPOSE[@]}" exec -T postgres \
    pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom --file=/tmp/elearning.dump
  "${COMPOSE[@]}" cp postgres:/tmp/elearning.dump "$archive"
  "${COMPOSE[@]}" exec -T postgres rm -f /tmp/elearning.dump

  local size
  size="$(du -h "$archive" | cut -f1)"
  log "Sauvegarde terminée : $archive ($size)."
  cmd_prune
}

cmd_list() {
  mkdir -p "$BACKUP_DIR"
  if ! ls -1 "$BACKUP_DIR"/e-learning-*.dump >/dev/null 2>&1; then
    log "Aucune archive dans $BACKUP_DIR"
    return 0
  fi
  printf '%-42s %10s %s\n' "ARCHIVE" "TAILLE" "DATE"
  printf '%-42s %10s %s\n' "-------" "------" "----"
  # shellcheck disable=SC2012
  ls -1t "$BACKUP_DIR"/e-learning-*.dump | while read -r file; do
    printf '%-42s %10s %s\n' \
      "$(basename "$file")" \
      "$(du -h "$file" | cut -f1)" \
      "$(date -r "$file" '+%Y-%m-%d %H:%M:%S' 2>/dev/null || stat -c '%y' "$file" | cut -d. -f1)"
  done
}

cmd_prune() {
  mkdir -p "$BACKUP_DIR"
  local count
  count="$(ls -1 "$BACKUP_DIR"/e-learning-*.dump 2>/dev/null | wc -l | tr -d ' ')"
  if (( count <= BACKUP_KEEP )); then
    log "Rétention OK ($count / $BACKUP_KEEP)."
    return 0
  fi
  log "Purge des archives au-delà de $BACKUP_KEEP…"
  # shellcheck disable=SC2012
  ls -1t "$BACKUP_DIR"/e-learning-*.dump | tail -n +"$((BACKUP_KEEP + 1))" | while read -r old; do
    log "Suppression $(basename "$old")"
    rm -f "$old"
  done
}

cmd_restore() {
  require_cmd docker
  load_env
  ensure_postgres

  local archive="${1:-}"
  if [[ -z "$archive" ]]; then
    archive="$(latest_archive)"
  fi
  [[ -f "$archive" ]] || die "Archive introuvable : $archive"

  log "Restauration Postgres depuis $(basename "$archive")…"
  "${COMPOSE[@]}" cp "$archive" postgres:/tmp/elearning.dump
  "${COMPOSE[@]}" exec -T postgres \
    psql -U "$POSTGRES_USER" -d postgres -v ON_ERROR_STOP=1 <<SQL
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = '${POSTGRES_DB}' AND pid <> pg_backend_pid();
DROP DATABASE IF EXISTS ${POSTGRES_DB};
CREATE DATABASE ${POSTGRES_DB} OWNER ${POSTGRES_USER};
SQL
  "${COMPOSE[@]}" exec -T postgres \
    pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists /tmp/elearning.dump \
    || true
  "${COMPOSE[@]}" exec -T postgres \
    psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c 'SELECT 1' >/dev/null
  "${COMPOSE[@]}" exec -T postgres rm -f /tmp/elearning.dump

  log "Restauration terminée. Redémarrez l'API si besoin : docker compose restart api"
}

main() {
  local cmd="${1:-backup}"
  case "$cmd" in
    -h|--help|help) usage ;;
    backup) cmd_backup ;;
    list) cmd_list ;;
    prune) cmd_prune ;;
    restore)
      shift || true
      cmd_restore "${1:-}"
      ;;
    *)
      usage
      die "Commande inconnue : $cmd"
      ;;
  esac
}

main "$@"
