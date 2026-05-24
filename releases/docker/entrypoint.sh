#!/bin/bash
# Docker entrypoint for Samba Manager

set -euo pipefail

echo "Starting Samba Manager container..."

export SAMBA_MANAGER_SECRET_KEY="${SAMBA_MANAGER_SECRET_KEY:-$(python3 -c 'import secrets; print(secrets.token_hex(32))')}"
export FLASK_ENV="${FLASK_ENV:-production}"

# Required runtime directories for Samba
mkdir -p /etc/samba /run/samba /var/lib/samba /var/lib/samba/private /var/cache/samba /var/log/samba /var/log/samba-manager /etc/samba/shares.d /app
chmod 0755 /var/lib/samba
chmod 700 /var/lib/samba/private
chmod 755 /etc/samba /etc/samba/shares.d /var/log/samba /var/log/samba-manager

# Initialize UI users DB file
USERS_FILE="${SAMBA_MANAGER_USERS_FILE:-/app/users.json}"
if [ ! -f "$USERS_FILE" ] || [ ! -s "$USERS_FILE" ]; then
    echo "{}" > "$USERS_FILE"
else
    if ! python3 - "$USERS_FILE" <<'PY'; then
import json, pathlib, shutil, sys, datetime
p = pathlib.Path(sys.argv[1])
try:
    json.loads(p.read_text() or "{}")
except Exception:
    ts = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
    backup = p.with_name(p.name + f".bak.{ts}")
    shutil.copy2(p, backup)
    p.write_text("{}")
PY
      echo "WARN: users.json was invalid, backed up and reset to {}"
    fi
fi

# Initialize Samba config if needed
if [ ! -f /etc/samba/smb.conf ] || [ ! -s /etc/samba/smb.conf ]; then
    cat > /etc/samba/smb.conf <<'EOF'
[global]
server string = Samba Server
workgroup = WORKGROUP
security = user
map to guest = Bad User

server min protocol = SMB2_02
server max protocol = SMB3

log file = /var/log/samba/log.%m
max log size = 1000

passdb backend = tdbsam

include = /etc/samba/shares.conf
EOF
fi
chmod 644 /etc/samba/smb.conf

if [ ! -f /etc/samba/shares.conf ]; then
    cat > /etc/samba/shares.conf <<'EOF'
# Samba shares configuration
EOF
fi

# Validate configuration before booting daemons
echo "Validating Samba configuration with testparm..."
if ! testparm -s /etc/samba/smb.conf >/tmp/testparm.out 2>/tmp/testparm.err; then
    echo "ERROR: Invalid Samba configuration"
    cat /tmp/testparm.out /tmp/testparm.err || true
    exit 1
fi

shutdown() {
    echo "Stopping services..."
    if [ -n "${FLASK_PID:-}" ] && kill -0 "$FLASK_PID" 2>/dev/null; then
        kill "$FLASK_PID" 2>/dev/null || true
    fi
    pkill -TERM smbd 2>/dev/null || true
    pkill -TERM nmbd 2>/dev/null || true
    wait || true
}

trap shutdown TERM INT

echo "Starting smbd..."
/usr/sbin/smbd -D
echo "Starting nmbd..."
/usr/sbin/nmbd -D

echo "Starting Flask UI..."
python /opt/samba-manager/run.py --host 0.0.0.0 --port "${FLASK_PORT:-5000}" &
FLASK_PID=$!

# Keep PID 1 alive and react to child exits/signals
wait -n "$FLASK_PID"
shutdown
