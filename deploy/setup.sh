#!/usr/bin/env bash
# setup.sh — run once as root on a fresh Ubuntu 22.04 droplet
# Usage: bash setup.sh
set -euo pipefail

APP_DIR=/opt/pensions_panorama

echo "==> Updating system packages..."
apt-get update -y && apt-get upgrade -y

echo "==> Installing Python 3.11, nginx, git..."
apt-get install -y python3.11 python3.11-venv python3.11-dev nginx git

echo "==> Creating app directory at $APP_DIR..."
mkdir -p "$APP_DIR"
chown www-data:www-data "$APP_DIR"

echo "==> Copying app files (run this from your local machine instead if using rsync)..."
echo "    Skip this block if you already rsynced the project here."

echo "==> Creating Python virtual environment..."
python3.11 -m venv "$APP_DIR/.venv"
"$APP_DIR/.venv/bin/pip" install --upgrade pip
"$APP_DIR/.venv/bin/pip" install -e "$APP_DIR[dev]"

echo "==> Installing systemd service..."
cp "$APP_DIR/deploy/pensions-panorama.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable pensions-panorama
systemctl start pensions-panorama

echo "==> Configuring nginx..."
cp "$APP_DIR/deploy/nginx.conf" /etc/nginx/sites-available/ramyzeid
ln -sf /etc/nginx/sites-available/ramyzeid /etc/nginx/sites-enabled/ramyzeid
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

echo ""
echo "==> Done! App should be live at http://ramyzeid.com/pensionspanorama"
echo "    Check service status: systemctl status pensions-panorama"
echo "    View logs:            journalctl -u pensions-panorama -f"
