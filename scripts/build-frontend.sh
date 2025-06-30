#!/bin/bash
set -e

echo "Building frontend for production..."

# Build frontend in container
docker compose run --rm frontend npm run build

# Copy built files to the caddy volume
echo "Copying built files to Caddy volume..."
docker run --rm \
  -v fair-edge_frontend_node_modules:/source/node_modules \
  -v fair-edge_frontend_build:/target \
  -v "$(pwd)/frontend:/source" \
  node:18-alpine \
  sh -c "cd /source && npm run build && cp -r dist/* /target/"

echo "Frontend build complete!"