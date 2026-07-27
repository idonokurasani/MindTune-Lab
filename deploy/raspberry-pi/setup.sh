#!/usr/bin/env bash
set -euo pipefail

USER_NAME="mindtune"
DATA_DIR="/opt/mindtune/data"

if ! id -u "$USER_NAME" >/dev/null 2>&1; then
    sudo useradd -r -m -s /bin/bash "$USER_NAME"
fi

sudo mkdir -p "$DATA_DIR"/{events,sessions,profiles,studies,exports,cache,logs,backups,tmp}
sudo chown -R "$USER_NAME:$USER_NAME" "$DATA_DIR"

if [ -f .env ]; then
    sudo install -m 600 -o "$USER_NAME" -g "$USER_NAME" .env /opt/mindtune/.env
fi

echo "Run: sudo cp deploy/systemd/mindtune-clm.service /etc/systemd/system/"
echo "     sudo systemctl enable --now mindtune-clm"
