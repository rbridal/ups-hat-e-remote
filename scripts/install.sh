#!/bin/bash
# Install ups-hat-e-remote on shop-dash (or any Pi with user dash).
set -euo pipefail
REPO=https://github.com/rbridal/ups-hat-e-remote.git
DEST=/opt/ups-hat-e-remote

if ! id dash >/dev/null 2>&1; then
  echo "user dash is missing; this script targets shop-dash" >&2
  exit 1
fi

sudo mkdir -p "$DEST"
sudo chown dash:dash "$DEST"
if [[ ! -d "$DEST/.git" ]]; then
  sudo -u dash git clone "$REPO" "$DEST"
else
  sudo -u dash git -C "$DEST" pull --ff-only
fi

if [[ ! -d "$DEST/venv" ]]; then
  sudo -u dash python3 -m venv "$DEST/venv"
fi
sudo -u dash "$DEST/venv/bin/pip" install -q -r "$DEST/requirements.txt"

if [[ ! -f "$DEST/config.yaml" ]]; then
  sudo -u dash cp "$DEST/config.example.yaml" "$DEST/config.yaml"
  sudo chmod 600 "$DEST/config.yaml"
fi

sudo install -m 644 "$DEST/ups-hat-e-remote.service" /etc/systemd/system/ups-hat-e-remote.service
sudo systemctl daemon-reload

if grep -q 'CHANGE_ME' "$DEST/config.yaml"; then
  echo "unit installed, not started"
  echo "edit $DEST/config.yaml (mqtt password), then:"
  echo "  sudo systemctl enable --now ups-hat-e-remote"
  exit 0
fi

sudo systemctl enable --now ups-hat-e-remote
sudo systemctl --no-pager --full status ups-hat-e-remote
