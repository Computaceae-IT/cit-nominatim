#!/bin/sh
# READ ONLY. Run on zambezia, only with authorization to inspect PRD.
# Output may disclose internal paths: retain it in a restricted evidence store.
set -eu
container=${1:-cit-nominatim-db}
docker inspect --format 'ImageID={{.Image}} ImageRef={{.Config.Image}} Path={{.Path}} Args={{json .Args}}' "$container"
docker inspect --format 'Mounts={{json .Mounts}} Restart={{json .HostConfig.RestartPolicy}} Ports={{json .HostConfig.PortBindings}} ShmSize={{.HostConfig.ShmSize}}' "$container"
docker image inspect --format 'ID={{.Id}} RepoDigests={{json .RepoDigests}}' "$(docker inspect --format '{{.Image}}' "$container")"
docker exec "$container" sh -c 'cat /etc/os-release; php -v; dpkg-query -W "php7.4*" "libapache2-mod-php7.4"; ps -eo pid,ppid,user,args | grep "[u]pdate.php" || true'
docker exec -e PGOPTIONS='-c default_transaction_read_only=on' -u postgres "$container" psql -X -v ON_ERROR_STOP=1 -d postgres -c "SELECT name, setting FROM pg_settings WHERE name IN ('data_directory','config_file','hba_file','server_version','fsync','full_page_writes','synchronous_commit','wal_level','archive_mode'); SELECT oid, spcname, pg_tablespace_location(oid) FROM pg_tablespace; SELECT datname FROM pg_database;"
docker exec -e PGOPTIONS='-c default_transaction_read_only=on' -u postgres "$container" psql -X -v ON_ERROR_STOP=1 -d nominatim -c 'SELECT extname, extversion FROM pg_extension; SELECT * FROM import_status; SELECT * FROM import_osmosis_log ORDER BY batchend DESC LIMIT 5;'
# Review changed container files; locate settings/local.php, flatnodes, WAL and
# tablespace symlinks separately, using the actual SQL data_directory above.
docker diff "$container"
