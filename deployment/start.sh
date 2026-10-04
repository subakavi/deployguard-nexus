#!/bin/bash

set -e

echo "Starting DeployGuard Nexus..."

systemctl start deployguard.service

sleep 5

curl --fail http://localhost:5000/health

echo
echo "DeployGuard Nexus started successfully."