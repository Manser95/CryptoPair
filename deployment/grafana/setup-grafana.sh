#!/bin/bash
# Setup script for Grafana - creates default dashboards and alerts

set -e

echo "Waiting for Grafana to start..."
until curl -s http://localhost:3000/api/health > /dev/null; do
    sleep 2
done

echo "Grafana is ready. Setting up dashboards..."

# Set admin password if different from default
if [ ! -z "$GF_SECURITY_ADMIN_PASSWORD" ]; then
    echo "Admin password is already set via environment variable"
fi

# Create API key for automation (optional)
# This can be useful for CI/CD pipelines
# API_KEY=$(curl -s -X POST -H "Content-Type: application/json" \
#     -d '{"name":"automation-key","role":"Admin"}' \
#     http://admin:${GF_SECURITY_ADMIN_PASSWORD}@localhost:3000/api/auth/keys \
#     | jq -r .key)

echo "Setting up home dashboard..."
curl -s -X PUT \
    -H "Content-Type: application/json" \
    -d '{"theme":"dark","homeDashboardId":1,"timezone":"browser"}' \
    http://admin:${GF_SECURITY_ADMIN_PASSWORD:-admin}@localhost:3000/api/org/preferences

echo "Grafana setup complete!"
echo "Access Grafana at: http://localhost:3000"
echo "Default credentials: admin / ${GF_SECURITY_ADMIN_PASSWORD:-admin}"