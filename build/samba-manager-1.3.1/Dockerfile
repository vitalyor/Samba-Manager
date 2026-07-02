FROM python:3.11-slim

# Install Samba and runtime tools
RUN apt-get update && \
    apt-get install -y samba samba-common-bin smbclient sudo procps iproute2 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /opt/samba-manager
COPY . /opt/samba-manager
RUN pip install -r requirements.txt
RUN chmod +x /opt/samba-manager/releases/docker/entrypoint.sh

# Expose port for web interface
EXPOSE 139 445 5000

ENTRYPOINT ["/opt/samba-manager/releases/docker/entrypoint.sh"]
