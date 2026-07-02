# Samba Manager 1.3.1 Release Manifest

**Release Date**: Thu Jul  2 07:48:44 MSK 2026
**Build System**: Darwin
**Release Manager**: Release Pack Builder Script

## Package Contents

### Archives
- **samba-manager-1.3.1.tar.gz** (GNU tar + gzip)
  - Size: 196K
  - SHA256: be1e45c00c296eecd06888b114014c84d83198f9e456a9b96e7f072e8255e846

- **samba-manager-1.3.1.zip** (ZIP format)
  - Size: 212K
  - SHA256: c365970e457f9c32d213e0c51bd38828b22ba0d4553ccdf435373562378dc3cb

### Documentation
- RELEASE_NOTES.md - Release notes and installation guide
- MANIFEST.txt - Package contents listing

### Verification
- checksums.txt - SHA-256 checksums for all packages
- verify_release.sh - Installation verification script

## System Requirements

- Linux distribution (Ubuntu, Debian, Fedora, RHEL, CentOS, Arch, Manjaro)
- Python 3.6+
- Samba 4.0+
- 512 MB RAM minimum
- 100 MB disk space minimum

## Installation Methods

1. **Automated Installation**
   ```bash
   tar -xzf samba-manager-1.3.1.tar.gz
   cd samba-manager-1.3.1
   sudo ./install.sh
   ```

2. **Docker Deployment**
   ```bash
   cd samba-manager-1.3.1
   docker build -t samba-manager:1.3.1 .
   docker run -p 5000:5000 -v /etc/samba:/etc/samba samba-manager:1.3.1
   ```

## Checksum Verification

Verify package integrity before installation:

```bash
sha256sum -c checksums.txt
```

Expected output:
```
samba-manager-1.3.1.tar.gz: OK
samba-manager-1.3.1.zip: OK
```

## Quick Start

After installation:

1. Start the service:
   ```bash
   sudo systemctl start samba-manager
   ```

2. Access the web interface:
   - URL: http://localhost:5000
   - Browser: Chrome, Firefox, Safari, Edge (latest versions)

3. Login with your credentials (set during installation)

## Support Resources

- **GitHub**: https://github.com/lyarinet/samba-manager
- **Issues**: https://github.com/lyarinet/samba-manager/issues
- **Wiki**: https://github.com/lyarinet/samba-manager/wiki

## License

This software is distributed under the MIT License.
See LICENSE file in the package for details.

---

Built by: Release Pack Builder Script
Build Date: 2026-07-02 07:48:44

