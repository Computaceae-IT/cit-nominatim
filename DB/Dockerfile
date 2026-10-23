# syntax=docker/dockerfile:1
ARG UBUNTU_BASE=ubuntu:20.04
FROM ${UBUNTU_BASE} AS build

ENV DEBIAN_FRONTEND noninteractive
ENV LANG C.UTF-8

WORKDIR /app

COPY verify-php.sh /usr/local/bin/verify-php

# Attach, install and detach in ONE layer; never pass a Pro token as ARG/ENV.
RUN --mount=type=secret,id=pro-attach-config,required=true \
    true \
    # Do not start daemons after installation.
    && echo '#!/bin/sh\nexit 101' > /usr/sbin/policy-rc.d \
    && chmod +x /usr/sbin/policy-rc.d \
    # Install all required packages.
    && apt-get -y update -qq \
    && apt-get install --no-install-recommends -y ubuntu-pro-client ca-certificates \
    && pro attach --attach-config /run/secrets/pro-attach-config \
    && apt-get update -qq \
    && apt-get upgrade -y \
    && apt-get -y install \
        locales \
    && locale-gen en_US.UTF-8 \
    && update-locale LANG=en_US.UTF-8 \
    && apt-get -y install \
        -o APT::Install-Recommends="false" \
        -o APT::Install-Suggests="false" \
        # Build tools from sources.
        build-essential \
        g++ \
        cmake \
        libpq-dev \
        zlib1g-dev \
        libbz2-dev \
        libproj-dev \
        libexpat1-dev \
        libboost-dev \
        libboost-system-dev \
        libboost-filesystem-dev \
        # PostgreSQL.
        postgresql-contrib \
        postgresql-server-dev-12 \
        postgresql-12-postgis-3 \
        postgresql-12-postgis-3-scripts \
        # PHP and Apache 2.
        php7.4-cli \
        php7.4-common \
        php7.4-intl \
        php7.4-pgsql \
        php7.4-json \
        php7.4-opcache \
        php7.4-readline \
        apache2 \
        libapache2-mod-php7.4 \
        # Python 3.
        python3-dev \
        python3-pip \
        python3-tidylib \
        python3-psycopg2 \
        python3-setuptools \
        # Misc.
        git \
        curl \
        sudo \
        util-linux \
    && sh /usr/local/bin/verify-php \
    && pro detach --assume-yes \
    && apt-get purge -y ubuntu-pro-client \
    && rm -rf /var/lib/ubuntu-advantage /var/log/ubuntu-advantage* /var/lib/apt/lists/*

# Configure postgres.
RUN true \
    && echo "host all all 0.0.0.0/0 md5" >> /etc/postgresql/12/main/pg_hba.conf \
    && echo "listen_addresses='*'" >> /etc/postgresql/12/main/postgresql.conf

# Osmium install to run continuous updates.
RUN pip3 install osmium

# Nominatim install.
ENV NOMINATIM_VERSION v3.6.0

# Retain the exact vendored 3.6 source until its PRD provenance is reconciled.
COPY db-src.tar.gz /tmp/db-src.tar.gz
RUN echo 'b5fe1446d6ce5a64f8112eff8b6e773a4b8a09b242a902e76f86a5d523a32bc6  /tmp/db-src.tar.gz' | sha256sum -c - \
    && mkdir -p /tmp/dbsrc /app/src \
    && tar -xzf /tmp/db-src.tar.gz -C /tmp/dbsrc \
    && cp -a /tmp/dbsrc/src/. /app/src/ \
    && rm -rf /tmp/dbsrc /tmp/db-src.tar.gz

RUN true \
    && cd src \
    && mkdir build \
    && cd build \
    && cmake .. \
    && make -j`nproc` \
    && chmod o=rwx .

RUN curl https://www.nominatim.org/data/country_grid.sql.gz > /app/src/data/country_osm_grid.sql.gz

RUN true \
    # Remove development and unused packages.
    && apt-get -y remove --purge \
        cpp-9 \
        gcc-9* \
        g++ \
        git \
        make \
        cmake* \
        llvm-10* \
        libc6-dev \
        linux-libc-dev \
        libclang-*-dev \
        build-essential \
        postgresql-server-dev-12 \
    && apt-get clean \
    # Clear temporary files and directories.
    && rm -rf \
        /tmp/* \
        /var/tmp/* \
        /root/.cache \
        /app/src/.git \
        /var/lib/apt/lists/*

# Apache configuration
COPY conf.d/local.php /app/src/build/settings/local.php
COPY conf.d/apache.conf /etc/apache2/sites-enabled/000-default.conf

# Runtime tuning only; the import-only configuration must stay out of the image.
# Never ship fsync=off/full_page_writes=off in the runtime DB image.
COPY conf.d/postgres-tuning.conf /etc/postgresql/12/main/conf.d/

COPY config.sh /app/config.sh
COPY init.sh /app/init.sh
COPY start.sh /app/start.sh
COPY startapache.sh /app/startapache.sh
COPY startpostgres.sh /app/startpostgres.sh

RUN sh /usr/local/bin/verify-php

# Collapse image to single layer.
FROM scratch

COPY --from=build / /

WORKDIR /app

EXPOSE 5432
EXPOSE 8080

# Please override this
ENV NOMINATIM_PASSWORD qaIACxO6wMR3
# how many threads should be use for importing
ENV THREADS=16

ENV NOMINATIM_RUN_UPDATES=false
CMD ["sh", "/app/startpostgres.sh"]
