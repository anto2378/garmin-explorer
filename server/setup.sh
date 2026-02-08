#!/usr/bin/env bash
# Server provisioning for Garmin Explorer.
# Run once on a fresh Ubuntu 24.04 machine (as root).
# Idempotent — safe to re-run.
#
# Usage:  ssh web-nebluda 'bash -s' < server/setup.sh
#    or:  ./deploy.sh --setup

set -euo pipefail

APP_USER="garmin"
APP_DIR="/opt/garmin-explorer"
DATA_DIR="${APP_DIR}/data"

echo "==> Garmin Explorer server setup"

# --- System packages ---
apt-get update -qq
apt-get install -y -qq rsync curl debian-keyring debian-archive-keyring apt-transport-https > /dev/null

# --- Caddy (official repo) ---
if ! command -v caddy &> /dev/null; then
    echo "==> Installing Caddy"
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list > /dev/null
    apt-get update -qq
    apt-get install -y -qq caddy > /dev/null
else
    echo "==> Caddy already installed"
fi

# --- uv (Python package manager) ---
if ! command -v uv &> /dev/null; then
    echo "==> Installing uv"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Copy binary to system path (not symlink — garmin user can't traverse /root/)
    cp /root/.local/bin/uv /usr/local/bin/uv
    cp /root/.local/bin/uvx /usr/local/bin/uvx
    chmod 755 /usr/local/bin/uv /usr/local/bin/uvx
else
    echo "==> uv already installed"
fi

# --- App user ---
if ! id "$APP_USER" &> /dev/null; then
    echo "==> Creating user ${APP_USER}"
    useradd --system --home-dir "$APP_DIR" --shell /usr/sbin/nologin "$APP_USER"
else
    echo "==> User ${APP_USER} already exists"
fi

# --- App directory ---
echo "==> Setting up directories"
mkdir -p "$APP_DIR" "$DATA_DIR/tokens"
chown -R "$APP_USER:$APP_USER" "$APP_DIR"

# --- Caddy config ---
echo "==> Installing Caddyfile"
cp "${APP_DIR}/server/Caddyfile" /etc/caddy/Caddyfile
systemctl enable caddy
systemctl restart caddy

# --- Systemd service ---
echo "==> Installing systemd service"
cp "${APP_DIR}/server/garmin-explorer.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable garmin-explorer

echo "==> Setup complete!"
echo "    App dir:  ${APP_DIR}"
echo "    Data dir: ${DATA_DIR}"
echo "    Run ./deploy.sh to deploy the app"
