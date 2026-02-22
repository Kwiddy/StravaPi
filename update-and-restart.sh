#!/bin/bash
# Update Strava Dashboard from git and restart the service.
# Run from the project root: ./update-and-restart.sh

set -e
cd "$(dirname "$0")"

echo "=== Pulling latest changes ==="
git pull

echo "=== Building frontend ==="
cd frontend
npm install
npm run build
cd ..

echo "=== Restarting service ==="
if systemctl is-active --quiet strava-dashboard 2>/dev/null; then
    sudo systemctl restart strava-dashboard
    echo "Service restarted."
else
    echo "Service not running. Start with: sudo systemctl start strava-dashboard"
fi

echo "=== Done ==="
