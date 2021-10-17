#!/usr/bin/env bash

# Deploys latest main in webroot on toolforge automagically!
#
# USAGE ./toolforge-deploy.sh

set -euo pipefail

HOST=tools-login.wmflabs.org
USER=tools.trainbow
WEBROOT=/data/project/trainbow/www/python/src

sshcmd() {
    ssh "$HOST" -- sudo -u "$USER" "$@"
}

sshcmd git -C "$WEBROOT" remote update
sshcmd git -C "$WEBROOT" checkout --force origin/main
sshcmd git -C "$WEBROOT" status
sshcmd git -C "$WEBROOT" -c gc.auto=128 gc --auto --quiet
sshcmd webservice --backend=kubernetes python3.7 restart
