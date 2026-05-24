#!/bin/bash
# Docker entrypoint for Samba Manager

set -euo pipefail

echo "Starting Samba Manager container..."

export SAMBA_MANAGER_SECRET_KEY="${SAMBA_MANAGER_SECRET_KEY:-$(python3 -c 'import secrets; print(secrets.token_hex(32))')}"
export FLASK_ENV="${FLASK_ENV:-production}"

# Required runtime directories for Samba
mkdir -p /run/samba /var/lib/samba/private /var/cache/samba /var/log/samba /var/log/samba-manager /etc/samba/shares.d
chmod 700 /var/lib/samba/private
chmod 755 /etc/samba /etc/samba/shares.d /var/log/samba /var/log/samba-manager

# Initialize Samba config if needed
if [ ! -f /etc/samba/smb.conf ]; then
    echo "Initializing /etc/samba/smb.conf from template..."
    if [ -f /opt/samba-manager/smb.conf.template ]; then
        cp /opt/samba-manager/smb.conf.template /etc/samba/smb.conf
    else
        echo "ERROR: smb.conf.template not found"
        exit 1
    fi
fi
chmod 644 /etc/samba/smb.conf

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
