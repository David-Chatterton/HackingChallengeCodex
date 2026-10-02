#!/bin/sh
set -eu

if [ "$(id -u)" -ne 0 ]; then
  echo "Run this setup script with sudo on the dedicated lab VM." >&2
  exit 1
fi

useradd --create-home --shell /bin/bash operator 2>/dev/null || true
mkdir -p /home/operator/relay
cp "$(dirname "$0")/server.py" /home/operator/relay/server.py
ACCESS_CODE="$(python3 -c 'import secrets; print(secrets.token_urlsafe(15))')"
FLAG_CODE="$(python3 -c 'import secrets; print("FLAG{" + secrets.token_hex(12).upper() + "}")')"
printf '%s\n' "$ACCESS_CODE" > /home/operator/relay/ssh-code.txt
printf '%s\n' "$FLAG_CODE" > /home/operator/MISSION_COMPLETE.txt
chown -R operator:operator /home/operator/relay /home/operator/MISSION_COMPLETE.txt
chmod 700 /home/operator/relay
chmod 600 /home/operator/relay/ssh-code.txt
printf 'operator:%s\n' "$ACCESS_CODE" | chpasswd

cat > /etc/systemd/system/relay-station.service <<'EOF'
[Unit]
Description=Signal School deliberately vulnerable relay
After=network.target

[Service]
Type=simple
User=operator
WorkingDirectory=/home/operator/relay
ExecStart=/usr/bin/python3 /home/operator/relay/server.py --bind 0.0.0.0 --port 8080
Restart=on-failure
NoNewPrivileges=true
PrivateDevices=true
ProtectSystem=strict
ProtectHome=read-only

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now relay-station.service
echo "Relay Station is active on TCP 8080. Keep this VM on an isolated lab VLAN/bridge."
echo "A unique access code and flag were generated. Root can inspect them if recovery is needed."
