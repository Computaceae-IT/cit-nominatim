#!/bin/sh
# Check Ubuntu package revisions: php -v alone cannot identify backported fixes.
set -eu
minimum=7.4.3-4ubuntu2.29+esm5
for package in php7.4-cli php7.4-common php7.4-pgsql php7.4-intl php7.4-json php7.4-opcache php7.4-readline libapache2-mod-php7.4; do
    test "$(dpkg-query -W -f='${Status}' "$package")" = 'install ok installed'
done
packages=$(mktemp)
trap 'rm -f "$packages"' EXIT HUP INT TERM
dpkg-query -W -f='${source:Package} ${binary:Package} ${Version} ${db:Status-Status}\n' > "$packages"
while read -r source package version status; do
    if [ "$source" = php7.4 ] && [ "$status" = installed ]; then
        dpkg --compare-versions "$version" ge "$minimum" || {
            echo "Unpatched PHP package: $package ($version < $minimum)" >&2
            exit 1
        }
        printf '%s %s\n' "$package" "$version"
    fi
done < "$packages"
php -r 'foreach (["pgsql", "pdo_pgsql", "intl", "json"] as $e) { if (!extension_loaded($e)) { fwrite(STDERR, "Missing extension: $e\n"); exit(1); } }'
