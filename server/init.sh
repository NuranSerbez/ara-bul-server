#!/bin/bash

# Function to run scraper with proper error handling
run_scraper() {
    echo "Running scraper..."
    python scraper.py
    return $?
}

# Function to check PostgreSQL connection
check_postgres() {
    local retries=30
    local count=0
    
    echo "Checking PostgreSQL connection..."
    until pg_isready -h db -p 5432 -U postgres || [ $count -eq $retries ]
    do
        echo "Waiting for PostgreSQL to be ready... ($count/$retries)"
        count=$((count + 1))
        sleep 2
    done

    if [ $count -eq $retries ]; then
        echo "Failed to connect to PostgreSQL after $retries attempts"
        return 1
    fi
    
    echo "PostgreSQL is ready"
    return 0
}

# Function to verify database schema
verify_schema() {
    echo "Verifying database schema..."
    python -c "
import sys
from sqlalchemy import create_engine, inspect
from os import getenv

try:
    engine = create_engine(getenv('DATABASE_URL'))
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    if 'television_data' not in tables:
        sys.exit(1)
    sys.exit(0)
except Exception as e:
    print(f'Error verifying schema: {e}')
    sys.exit(1)
"
    return $?
}

# Main execution starts here
echo "Starting initialization script..."

# Check for required environment variables
if [ -z "$DATABASE_URL" ]; then
    echo "ERROR: DATABASE_URL environment variable is not set"
    exit 1
fi

# Wait for PostgreSQL
if ! check_postgres; then
    echo "ERROR: PostgreSQL connection failed"
    exit 1
fi

# Initialize/verify schema
if ! verify_schema; then
    echo "Database schema verification failed, will be created by scraper"
fi

# Run scraper with retries
MAX_RETRIES=3
RETRY_COUNT=0
SCRAPER_SUCCESS=false

if [ "$SCRAPER_SUCCESS" = false ]; then
    echo "WARNING: Scraper failed after $MAX_RETRIES attempts"
    echo "Check logs for details"
fi

# Start the Flask application
echo "Starting Flask application..."
export FLASK_APP=server.py
export FLASK_ENV=production
python -m flask run --host=0.0.0.0 --port=4000