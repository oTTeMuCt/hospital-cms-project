#!/usr/bin/env bash
set -euo pipefail
umask 077

if [[ $# != 1 ]]; then
    echo "Usage: bash ops/verify-backup.sh /path/to/backup-directory" >&2
    exit 2
fi

backup=$1
(
    cd "$backup"
    sha256sum --check SHA256SUMS
)
tar -tzf "$backup/media.tar.gz" >/dev/null

container=$(docker run -d --rm --network none -e POSTGRES_USER=restore_check \
    -e POSTGRES_DB=restore_check -e POSTGRES_HOST_AUTH_METHOD=trust postgres:16-alpine)
trap 'docker stop "$container" >/dev/null 2>&1 || true' EXIT

ready=false
for attempt in {1..60}; do
    if docker exec "$container" pg_isready -h 127.0.0.1 -U restore_check -d restore_check >/dev/null 2>&1; then
        ready=true
        break
    fi
    sleep 1
done
if [[ "$ready" != true ]]; then
    echo "Isolated PostgreSQL did not become ready" >&2
    exit 1
fi

docker exec -i "$container" pg_restore --exit-on-error --no-owner --no-acl -U restore_check -d restore_check < "$backup/database.dump"
docker exec "$container" psql -v ON_ERROR_STOP=1 -U restore_check -d restore_check \
    -c 'SELECT count(*) AS migrations FROM django_migrations;' \
    -c 'SELECT count(*) AS patients FROM patients_patient;'
docker exec -i "$container" sh -c 'mkdir /tmp/restored-media && tar -C /tmp/restored-media -xzf - && find /tmp/restored-media -type f | wc -l' < "$backup/media.tar.gz"
printf 'Database and media restored in an isolated container.\n'
