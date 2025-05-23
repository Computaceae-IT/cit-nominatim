# Nominatim Docker (Nominatim version 3.6)

## Manual DB

```
docker run --name=cit-nominatim-db \
        --volume /data/nominatim:/var/lib/postgresql/12/main \
        --env=REPLICATION_URL=http://planet.openstreetmap.org/replication/day/ \
        --env=NOMINATIM_PASSWORD=<XXX> \
        --workdir=/app \
        -p 172.16.0.250:6432:5432 \
        --restart=always \
        --log-opt max-size=100m \
        -e THREADS=16 \
        --detach=true \
        registry.computaceae-it.tech/cit-nominatim-db \
        sh /app/startpostgres.sh
```

## Automatic import

Download the required data, initialize the database and start nominatim in one go

```
docker run -it --rm \
  -e PBF_URL=https://download.geofabrik.de/europe/monaco-latest.osm.pbf \
  -e REPLICATION_URL=https://download.geofabrik.de/europe/monaco-updates/ \
  -e IMPORT_WIKIPEDIA=true \
  -p 8080:8080 \
  --name nominatim \
  mediagis/nominatim:3.6
```

The port 8080 is the nominatim HTTP API port and 5432 is the Postgres port, which you may or may not want to expose.

If you want to check that your data import was sucessful, you can use the API with the following URL: http://localhost:8080/search.php?q=avenue%20pasteur

## Configuration

The following environment variables are available for configuration:

  - `PBF_URL`: Which OSM extract to download. Check https://download.geofabrik.de
  - `REPLICATION_URL`: Where to get updates from. Also availble from Geofabrik.
  - `IMPORT_WIKIPEDIA`: Whether to import the Wikipedia importance dumps, which improve scoring of results. On a beefy 10 core server this takes around 5 minutes. (default: `false`)
  - `IMPORT_US_POSTCODES`: Whether to import the US postcode dump. (default: `false`)
  - `IMPORT_GB_POSTCODES`: Whether to import the GB postcode dump. (default: `false`)
  - `THREADS`: How many threads should be used to import (default: `16`)
  - `NOMINATIM_PASSWORD`: The password to connect to the database with (default: `qaIACxO6wMR3`)

The following environment variables are available to tune PostgreSQL:

  - `POSTGRES_SHARED_BUFFERS` (default: `2GB`)
  - `POSTGRES_MAINTENANCE_WORK_MEM` (default: `10GB`)
  - `POSTGRES_AUTOVACUUM_WORK_MEM` (default: `2GB`)
  - `POSTGRES_WORK_MEM` (default: `50MB`)
  - `POSTGRES_EFFECTIVE_CACHE_SIZE` (default: `24GB`)
  - `POSTGRES_SYNCHRONOUS_COMMIT` (default: `off`)
  - `POSTGRES_MAX_WAL_SIZE` (default: `1GB`)
  - `POSTGRES_CHECKPOINT_TIMEOUT` (default: `10min`)
  - `POSTGRES_CHECKPOINT_COMPLETITION_TARGET` (default: `0.9`)

See https://nominatim.org/release-docs/3.6.0/admin/Installation/#tuning-the-postgresql-database for more details on those settings.


The following run parameters are available for configuration:

  - `shm-size`: Size of the tmpfs in Docker, for bigger imports (e.g. Europe) this needs to be set to at least 1GB or more. Half the size of your available RAM is recommended. (default: `64M`)

## Persistent container data

There is one folder the can be persisted across container creation and removal.

- `/var/lib/postgresql/12/main` is the storage location of the Postgres database & holds the state about whether the import was succesful

So if you want to be able to kill your container and start it up again with all the data still present use the following command:

```
docker run -it --rm --shm-size=1g \
  -e PBF_URL=https://download.geofabrik.de/europe/monaco-latest.osm.pbf \
  -e REPLICATION_URL=https://download.geofabrik.de/europe/monaco-updates/ \
  -e IMPORT_WIKIPEDIA=false \
  -e NOMINATIM_PASSWORD=very_secure_password \
  -v nominatim-data:/var/lib/postgresql/12/main \
  -p 8080:8080 \
  --name nominatim \
  mediagis/nominatim:3.6
```

## Updating the database

Full documentation for Nominatim update available [here](https://nominatim.org/release-docs/3.6.0/admin/Update/). For a list of other methods see the output of:
```
docker exec -it nominatim sudo -u nominatim ./src/build/utils/update.php --help
```

The following command will keep updating the database forever:

```
docker exec -it nominatim sudo -u nominatim ./src/build/utils/update.php --import-osmosis-all
```

If there are no updates available this process will sleep for 15 minutes and try again.

## Development

If you want to work on the Docker image you can use the following command to build a local
image and run the container with

```
docker build -t nominatim . && \
docker run -it --rm \
    -e PBF_URL=https://download.geofabrik.de/europe/monaco-latest.osm.pbf \
    -e REPLICATION_URL=https://download.geofabrik.de/europe/monaco-updates/ \
    -p 8080:8080 \
    --name nominatim \
    nominatim
```
