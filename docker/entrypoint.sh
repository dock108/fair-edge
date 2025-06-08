#!/bin/bash
set -e

# Wait for dependencies if needed
if [ "$WAIT_FOR_DEPS" = "true" ]; then
    echo "Waiting for dependencies..."
    
    # Wait for Redis
    until redis-cli -h redis ping > /dev/null 2>&1; do
        echo "Waiting for Redis..."
        sleep 2
    done
    echo "Redis is ready!"
fi

# Run database migrations if needed
if [ "$RUN_MIGRATIONS" = "true" ]; then
    echo "Running database migrations..."
    # Add migration commands here if needed
    echo "Migrations completed!"
fi

# Execute the command passed to the container
exec "$@" 