#!/usr/bin/env bash
# Copia coherente de una instalación propia, guardada fuera de la carpeta pública.
set -euo pipefail
umask 077
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd -P)
[[ -f "$root/.secrets/db_password" && ! -L "$root/backups" ]] || exit 1
mkdir -p -- "$root/backups" "$root/.runtime"
chmod 700 -- "$root/backups" "$root/.runtime"
exec {backup_lock}>"$root/.runtime/backup.lock"
flock -n "$backup_lock" || exit 0
stamp=$(date -u +%Y%m%dT%H%M%SZ)
work="$root/backups/.part-$stamp"
mkdir -m 700 -- "$work"
trap 'rm -rf -- "$work"' EXIT
compose=(docker compose -f "$root/docker/production/compose.yaml")
# La expansión pertenece al shell del contenedor, no al host.
# shellcheck disable=SC2016
timeout -k 10s 180s "${compose[@]}" exec -T db sh -c \
  'MYSQL_PWD="$(cat /run/secrets/db_password)" exec mariadb-dump --user=facuso --single-transaction --skip-lock-tables --skip-comments facuso' \
  | gzip -c > "$work/database.sql.gz"
timeout -k 10s 180s "${compose[@]}" exec -T wordpress \
  tar -C /var/www/html -czf - wp-content wp-config.php .htaccess > "$work/wordpress.tar.gz"
tar -C "$root" -czf "$work/private-config.tar.gz" .secrets .runtime/cron.env docker/production
gzip -t "$work/database.sql.gz"
tar -tzf "$work/wordpress.tar.gz" >/dev/null
tar -tzf "$work/private-config.tar.gz" >/dev/null
mv -- "$work" "$root/backups/$stamp"
trap - EXIT
printf '%s\n' "$stamp" > "$root/.runtime/last-backup"
# Retención por antigüedad, restringida al nombre y nivel de nuestras copias.
find "$root/backups" -mindepth 1 -maxdepth 1 -type d -name '20??????T??????Z' -mtime +7 -exec rm -rf -- {} +
printf 'Copia FAC-USO guardada: %s\n' "$stamp"
