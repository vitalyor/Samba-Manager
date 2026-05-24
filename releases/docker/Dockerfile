FROM python:3.12-slim-bookworm

LABEL maintainer="Lyarinet <lyarinet@example.com>"
LABEL description="Web-based interface for managing Samba file sharing on Linux systems"
LABEL version="1.2.0"

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    samba \
    samba-common \
    smbclient \
    sudo \
    procps \
    iproute2 \
    curl \
    wget \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /opt/samba-manager

# Copy application files
COPY app /opt/samba-manager/app
COPY run.py /opt/samba-manager/
COPY version.py /opt/samba-manager/
COPY requirements.txt /opt/samba-manager/
COPY smb.conf.template /opt/samba-manager/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p /var/log/samba-manager \
    && mkdir -p /etc/samba/shares.d \
    && touch /var/log/samba-manager/access.log \
    && chmod 755 /var/log/samba-manager

COPY releases/docker/entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

# Expose web port
EXPOSE 139 445 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Run as non-root user when possible
RUN useradd -m -s /bin/bash sambamanager || true

# Volume mounts for persistent data
VOLUME ["/etc/samba", "/var/log/samba-manager", "/var/log/samba"]

ENTRYPOINT ["/entrypoint.sh"]
