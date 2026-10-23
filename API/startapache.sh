#!/bin/sh
set -eu
# Kubernetes may provide a local.php override. Otherwise retain the image config.
if [ -f /data/local.php ]; then
    cp /data/local.php /app/src/build/settings/local.php
fi
sh /usr/local/bin/verify-php
/app/src/build/utils/setup.php --setup-website
/usr/sbin/apache2ctl configtest
exec /usr/sbin/apache2ctl -D FOREGROUND
