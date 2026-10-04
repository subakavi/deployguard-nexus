#!/bin/bash

set -e

APP_DIR="/opt/deployguard-nexus"
VENV_DIR="/opt/deployguard-venv"

echo "Installing DeployGuard Nexus..."

# Install required system packages
dnf install -y python3 python3-pip curl

# Create virtual environment
python3 -m venv "$VENV_DIR"

# Upgrade pip
"$VENV_DIR/bin/pip" install --upgrade pip

# Install application dependencies
"$VENV_DIR/bin/pip" install -r "$APP_DIR/app/requirements.txt"

# Install Gunicorn for production application serving
"$VENV_DIR/bin/pip" install gunicorn

# Create systemd service
cat > /etc/systemd/system/deployguard.service <<EOF
[Unit]
Description=DeployGuard Nexus Flask Application
After=network.target

[Service]
User=root
WorkingDirectory=$APP_DIR/app
Environment="PATH=$VENV_DIR/bin"
ExecStart=$VENV_DIR/bin/gunicorn --bind 0.0.0.0:5000 app:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable deployguard.service

echo "DeployGuard Nexus installation completed."