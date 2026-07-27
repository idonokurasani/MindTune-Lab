# Raspberry Pi Deployment

1. Run `deploy/raspberry-pi/setup.sh` to create service user and directories.
2. Copy `.env` to `/opt/mindtune/.env` with mode `600`.
3. Install `deploy/systemd/mindtune-clm.service`.
4. Start and enable the service: `systemctl enable --now mindtune-clm`.
5. Verify `/api/v1/health/ready`.

Real FC11 BLE support is host-dependent and untested on target hardware.
