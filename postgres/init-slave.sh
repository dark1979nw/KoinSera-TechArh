#!/bin/bash

# Wait for master to be ready
until pg_isready -h postgres-master -p 5432 -U postgres; do
    echo "Waiting for master to be ready..."
    sleep 2
done

# Configure PostgreSQL for replication
cat >> "$PGDATA/postgresql.conf" <<EOF
listen_addresses = '*'
wal_level = replica
max_wal_senders = 10
max_replication_slots = 10
hot_standby = on
EOF

# Configure access for replication
cat >> "$PGDATA/pg_hba.conf" <<EOF
host replication replicator all md5
EOF

# Remove existing data
rm -rf "$PGDATA"/*

# Create base backup from master
pg_basebackup -h postgres-master -U replicator -D "$PGDATA" -P -Xs -R

# Configure replication
cat > "$PGDATA/postgresql.auto.conf" <<EOF
primary_conninfo = 'host=postgres-master port=5432 user=replicator password=replicator_password'
EOF 