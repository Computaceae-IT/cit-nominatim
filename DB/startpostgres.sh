#!/bin/bash

service postgresql start

# for update
touch /var/log/update.log
nohup sudo -u postgres ./src/build/utils/update.php --import-osmosis-all > /var/log/update.log  2>&1&

tail -f /var/log/postgresql/postgresql-12-main.log -f /var/log/update.log