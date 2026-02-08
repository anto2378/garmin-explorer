#!/usr/bin/env bash
# Deploy Garmin Explorer to the VPS.
#
# Usage:
#   ./deploy.sh           # deploy code + restart
#   ./deploy.sh --setup   # first-time server provisioning + deploy
set -euo pipefail

SERVER="web-nebluda"
APP_DIR="/opt/garmin-explorer"

# --- First-time setup ---
if [[ "${1:-}" == "--setup" ]]; then
    echo "==> Running server provisioning..."
    # Sync files first so setup.sh can find Caddyfile and service file
    rsync -az --delete \
        --exclude '.git/' \
        --exclude '.venv/' \
        --exclude '__pycache__/' \
        --exclude 'data/' \
        --exclude 'creds*.json' \
        --exclude '.env*' \
        --exclude '.cache/' \
        --exclude '.local/' \
        ./ "${SERVER}:${APP_DIR}/"
    ssh "$SERVER" "bash ${APP_DIR}/server/setup.sh"
    echo "==> Provisioning done. Running deploy..."
fi

# --- Sync project files ---
echo "==> Syncing files to ${SERVER}:${APP_DIR}/"
rsync -az --delete \
    --exclude '.git/' \
    --exclude '.venv/' \
    --exclude '__pycache__/' \
    --exclude 'data/' \
    --exclude 'creds*.json' \
    --exclude '.env*' \
    --exclude '.cache/' \
    --exclude '.local/' \
    ./ "${SERVER}:${APP_DIR}/"

# --- Fix ownership (data dir stays owned by garmin user) ---
ssh "$SERVER" "chown -R garmin:garmin ${APP_DIR}"

# --- Install deps as app user + restart ---
echo "==> Installing dependencies..."
ssh "$SERVER" "sudo -u garmin bash -c 'cd ${APP_DIR} && /usr/local/bin/uv sync --no-dev 2>&1 | tail -5'"

echo "==> Restarting service..."
ssh "$SERVER" "systemctl restart garmin-explorer"

# --- Verify ---
sleep 2
STATUS=$(ssh "$SERVER" "systemctl is-active garmin-explorer")
if [[ "$STATUS" == "active" ]]; then
    echo "==> ✅ Deployed! Service is running."
    echo "    https://fake-sporter.nebluda.com/"
else
    echo "==> ❌ Service failed to start. Checking logs..."
    ssh "$SERVER" "journalctl -u garmin-explorer --no-pager -n 20"
    exit 1
fi
