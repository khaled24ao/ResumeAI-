#!/bin/bash
# Initialize database script

set -e

echo "Initializing ResumeAI database..."

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
while ! nc -z postgres 5432; do
  sleep 1
done

echo "PostgreSQL is ready"

# Run database migrations/init
python scripts/seed_db.py

echo "Database initialized successfully"