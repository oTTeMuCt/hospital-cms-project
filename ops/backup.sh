#!/usr/bin/env bash
set -euo pipefail
umask 077

if [[ $# != 1 ]]; then
    echo "Usage: bash ops/backup.sh /path/to/new-backup-directory" >&2
    exit 2
fi

destination=$1
mkdir -- "$destination"
docker compose exec -T db sh -c 'pg_dump -Fc --no-owner --no-acl -U "$POSTGRES_USER" "$POSTGRES_DB"' > "$destination/database.dump"
docker compose run --rm --no-deps -T --entrypoint tar backend -C /media -czf - . > "$destination/media.tar.gz"
(
    cd "$destination"
    sha256sum database.dump media.tar.gz > SHA256SUMS
)
printf 'Backup complete: %s\n' "$destination"
