#!/bin/bash

echo "Stopping DeployGuard Nexus..."

systemctl stop deployguard.service || true

echo "DeployGuard Nexus stopped."