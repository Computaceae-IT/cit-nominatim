#!/bin/sh
# Existing-cluster entrypoint only. Initial imports must use a separate workflow.
set -eu
PGDATA=/var/lib/postgresql/12/main
config=/etc/postgresql/12/main/postgresql.conf
if ! mountpoint -q "$PGDATA" || [ ! -f "$PGDATA/PG_VERSION" ]; then
    echo "Refusing to start: mount an existing PostgreSQL 12 cluster at $PGDATA" >&2
    exit 1
fi
if [ "$(cat "$PGDATA/PG_VERSION")" != 12 ]; then
    echo 'Refusing to start: PostgreSQL major version must remain 12' >&2
    exit 1
fi
setting() {
    sudo -u postgres /usr/lib/postgresql/12/bin/postgres -D "$PGDATA" -c "config_file=$config" -C "$1"
}
if [ "$(readlink -f "$(setting data_directory)")" != "$(readlink -f "$PGDATA")" ]; then
    echo 'Refusing to start: configured data_directory differs from the verified mount' >&2
    exit 1
fi
for name in fsync full_page_writes; do
    if [ "$(setting "$name")" != on ]; then
        echo "Refusing unsafe runtime setting: $name must be on" >&2
        exit 1
    fi
done
sh /usr/local/bin/verify-php
update_pid=
log_pid=
stop_services() {
    trap '' TERM INT
    if [ -n "$update_pid" ]; then
        kill -TERM "$update_pid" 2>/dev/null || true
        wait "$update_pid" || true
    fi
    pg_ctlcluster --mode fast 12 main stop
    if [ -n "$log_pid" ]; then kill "$log_pid" 2>/dev/null || true; fi
}
trap 'stop_services; exit 0' TERM INT
service postgresql start
pg_isready -q -U postgres
if [ "${NOMINATIM_RUN_UPDATES:-false}" = true ]; then
    sudo -u postgres /usr/bin/php -Cq /app/src/build/utils/update.php --import-osmosis-all >> /var/log/update.log 2>&1 &
    update_pid=$!
elif [ "${NOMINATIM_RUN_UPDATES:-false}" != false ]; then
    echo 'NOMINATIM_RUN_UPDATES must be true or false' >&2
    stop_services
    exit 1
fi
touch /var/log/update.log
tail -F /var/log/postgresql/postgresql-12-main.log /var/log/update.log &
log_pid=$!
# Fail the container if PostgreSQL or the continuous importer exits.
while pg_isready -q -U postgres; do
    if [ -n "$update_pid" ] && ! kill -0 "$update_pid" 2>/dev/null; then
        stop_services
        exit 1
    fi
    sleep 5 &
    wait $! || true
done
stop_services
exit 1
