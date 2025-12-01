#!/bin/sh
echo "Waiting for PostgreSQL..."
while ! python -c "import socket; s=socket.socket(); s.connect(('db', 5432))" 2>/dev/null; do
  sleep 1
done
echo "PostgreSQL is up - executing command"
exec "$@"