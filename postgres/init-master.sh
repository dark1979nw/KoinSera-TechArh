#!/bin/bash
set -e

# Wait for PostgreSQL to be ready
until pg_isready -U "$POSTGRES_USER"; do
    echo "Waiting for PostgreSQL to be ready..."
    sleep 2
done

# Create replication user
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE USER replicator WITH REPLICATION ENCRYPTED PASSWORD 'replicator_password';
EOSQL

# Configure PostgreSQL for replication
cat >> "$PGDATA/postgresql.conf" <<EOF
listen_addresses = '*'
wal_level = replica
max_wal_senders = 10
max_replication_slots = 10
hot_standby = on
EOF

# Configure access for replication and application
cat >> "$PGDATA/pg_hba.conf" <<EOF
host replication replicator all md5
host all koinsera all md5
EOF

# Create application database and user with proper permissions
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Drop if exists to ensure clean state
    DROP DATABASE IF EXISTS koinsera;
    DROP USER IF EXISTS koinsera;
    
    -- Create user and database
    CREATE USER koinsera WITH ENCRYPTED PASSWORD 'koinsera_password';
    CREATE DATABASE koinsera OWNER koinsera;
    
    -- Grant all privileges
    GRANT ALL PRIVILEGES ON DATABASE koinsera TO koinsera;
    
    -- Connect to koinsera database to grant schema privileges
    \c koinsera
    GRANT ALL ON SCHEMA public TO koinsera;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO koinsera;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO koinsera;
EOSQL 