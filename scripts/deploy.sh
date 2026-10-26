#!/bin/bash
# CodeDeploy AfterInstall hook: runs as root after files are copied.
set -e

APP_DIR=/opt/deployguard-nexus
VENV=/opt/deployguard-venv

echo "========================================"
echo "DeployGuard Nexus CodeDeploy Deployment"
echo "========================================"

cd "$APP_DIR"
chmod +x scripts/*.sh deployment/*.sh 2>/dev/null || true

echo "Installing Python dependencies..."
"$VENV/bin/pip" install -q -r app/requirements.txt || echo "Warning: pip install reported a problem"

echo "Restarting application service..."
systemctl restart deployguard

echo "TEST: simulating a crash"; systemctl stop deployguard; echo "Waiting for the application to respond..."
for i in 1 2 3 4 5 6 7 8 9 10; do
  if curl -fsS http://127.0.0.1:5000/health > /dev/null; then
    echo "Health check passed."
    echo "CodeDeploy deployment completed."
    exit 0
  fi
  sleep 3
done

echo "Health check FAILED: application did not respond."
journalctl -u deployguard -n 20 --no-pager || true
exit 1