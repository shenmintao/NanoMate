#!/bin/sh
set -eu

python /app/docker/life-assistant-bootstrap.py

if [ "$#" -eq 0 ]; then
    set -- gateway
fi

exec /usr/local/bin/entrypoint.sh "$@"
