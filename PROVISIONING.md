# Signal School lab provisioning runbook

This is the quickest recommended deployment for the academy and Relay Station challenge. It assumes Proxmox VE, Debian 12, and one or more children using a Linux desktop.

## 1. Recommended layout

Keep all lab guests on the same Proxmox node for the first run. That avoids configuring VLANs or cross-node SDN.

| Guest | Type | Purpose | Address | Minimum resources |
|---|---|---|---|---|
| `academy` | Unprivileged LXC | Hosts the lessons | `10.77.0.10/24` | 1 vCPU, 512 MB RAM, 4 GB disk |
| `student-01` | VM | Child's Linux desktop and terminal | `10.77.0.21/24` | 2 vCPU, 4 GB RAM, 24 GB disk |
| `relay-08` | VM | Disposable vulnerable challenge | `10.77.0.80/24` | 1 vCPU, 1 GB RAM, 8 GB disk |

Create another student VM for each child using `10.77.0.22`, `10.77.0.23`, and so on. One shared academy and one shared Relay Station are enough if the children cooperate. Give each child a separate Relay Station clone if they should solve it independently.

Use a VM—not an LXC—for `relay-08`. The application is intentionally vulnerable, so the stronger isolation boundary is worthwhile. The learner machine is also easiest as a VM because `nmap` works without LXC capability changes.

## 2. Network topology

Use an isolated Linux bridge with no physical network port attached:

```text
                    Proxmox host
                         │
                vmbr77 (no gateway)
                         │
          ┌──────────────┼──────────────┐
          │              │              │
     academy LXC     student VM     relay-08 VM
     10.77.0.10      10.77.0.21     10.77.0.80
       TCP 8000       browser/nmap    TCP 22,8080
```

Do not attach `relay-08` to your normal LAN, a public bridge, or a bridge with port forwarding. Do not place credentials, SSH keys, mounted host directories, or personal data on it.

### Create the isolated bridge

In the Proxmox web interface:

1. Select the node, then **System → Network → Create → Linux Bridge**.
2. Name it `vmbr77`.
3. Leave **Bridge ports**, IPv4/CIDR, IPv4 gateway, IPv6/CIDR, and IPv6 gateway empty.
4. Add the comment `Signal School isolated lab`.
5. Apply the network configuration.

No DHCP server is required; use the static addresses in this guide. The guests should have no default gateway on their lab interfaces.

> If the guests must run on different Proxmox nodes, an unattached Linux bridge will not span those nodes. Either keep the lab on one node, connect a dedicated VLAN to each node, or configure a Proxmox SDN zone/VNet. Keeping everything on one node is substantially faster.

## 3. Prepare installation media

You need:

- A Debian 12 standard LXC template for `academy`.
- A Linux desktop ISO for each student VM. Linux Mint, Ubuntu Desktop, or Debian with a desktop environment are all suitable.
- A Debian 12 netinst ISO for `relay-08`.
- This project directory available temporarily from your admin computer or copied using a USB/ISO/SCP workflow.

## 3A. Bootstrap networking and file transfer

`vmbr77` is intentionally isolated, so guests attached only to it cannot reach your LAN or the internet. Use one of the following provisioning methods.

### Fastest method: temporary second NIC

Temporarily give each guest a second interface on your normal LAN/NAT bridge (commonly `vmbr0`). Use it to update packages and copy files, then remove it.

The safe order is important:

1. Create the guest with its permanent `vmbr77` interface.
2. Add a temporary second interface attached to `vmbr0`.
3. Boot the guest and let the temporary interface obtain a LAN address with DHCP.
4. Install all required packages.
5. Copy the appropriate project folder over SSH/SCP, or use the Proxmox console and the alternatives below.
6. **On `relay-08`, do not run `setup-relay.sh` yet.**
7. Shut the guest down.
8. In Proxmox, remove the temporary `vmbr0` network device.
9. Start the guest and confirm it has only its static `10.77.0.x` address and no default route.
10. Only now run `setup-relay.sh` from the Proxmox console on `relay-08`.

Example transfers from the computer holding this project, while the guest still has a temporary LAN address:

```bash
scp -r academy admin@<academy-temporary-LAN-IP>:/tmp/
scp -r relay-station admin@<relay-temporary-LAN-IP>:/tmp/
```

Then, inside the academy LXC:

```bash
sudo mkdir -p /opt/signal-school
sudo cp -a /tmp/academy /opt/signal-school/
```

Inside `relay-08`, preserve the challenge files until its LAN interface has been removed:

```bash
sudo cp -a /tmp/relay-station /opt/
```

After removing the temporary NIC, open **Console** for `relay-08` in Proxmox and run:

```bash
cd /opt/relay-station
sudo sh setup-relay.sh
```

For the student VM, install `nmap`, `openssh-client`, `curl`, and the desktop/browser while the temporary NIC exists. The student VM does not need any project source files unless you choose the two-VM variant.

### Academy LXC without a temporary NIC

The Proxmox host can place files directly into an LXC. First archive the academy folder on the computer that holds the project and upload `academy.tar.gz` to the Proxmox host. Then run these commands on the Proxmox host, replacing `101` with the academy container ID:

```bash
pct start 101
pct exec 101 -- mkdir -p /opt/signal-school
pct push 101 /path/on/proxmox/academy.tar.gz /tmp/academy.tar.gz
pct exec 101 -- tar -xzf /tmp/academy.tar.gz -C /opt/signal-school
```

This transfers code without giving the container LAN access. Package installation still requires either a temporary routed interface or offline Debian package media.

### Completely offline method

If no guest may ever touch the LAN:

1. Use Debian installation media containing the packages you need, or download the required `.deb` files and dependencies on another machine.
2. Put the `.deb` files and project folders into an ISO image or USB image.
3. Upload that ISO to Proxmox storage.
4. Attach it as a virtual CD/DVD to each VM and copy/install from it.
5. For the LXC, upload an archive to the Proxmox host and use `pct push` as shown above.

For example, after mounting a tools ISO in a Debian VM:

```bash
sudo mkdir -p /mnt/tools
sudo mount /dev/sr0 /mnt/tools
sudo apt install /mnt/tools/packages/*.deb
cp -a /mnt/tools/relay-station /opt/
```

Offline dependency collection is more work because packages such as `nmap` have dependencies. A temporary second NIC is usually the quickest option and remains safe provided it is removed before the vulnerable Relay Station service starts.

### Verify disconnection

After removing every temporary interface, run this in each guest:

```bash
ip -br address
ip route
```

The guest should show only its loopback address and its `10.77.0.x/24` lab address. There should be no `default via ...` route. Internet tests such as `curl https://example.com` should fail.

## 4. Provision the academy LXC

### Proxmox settings

- Hostname: `academy`
- Template: Debian 12 standard
- Unprivileged container: **enabled**
- Nesting: **disabled**
- Disk: 4 GB
- CPU: 1 core
- Memory: 512 MB; swap: 256 MB
- Network bridge: `vmbr77`
- IPv4: static `10.77.0.10/24`
- Gateway: leave blank
- Start at boot: optional

### Install the files and service

Copy the project's `academy` folder to `/opt/signal-school/academy` inside the container. Then create a dedicated account and service:

```bash
apt update
apt install -y python3
useradd --system --home /opt/signal-school --shell /usr/sbin/nologin academy-web
chown -R academy-web:academy-web /opt/signal-school
```

Create `/etc/systemd/system/signal-academy.service`:

```ini
[Unit]
Description=Signal School academy website
After=network.target

[Service]
Type=simple
User=academy-web
WorkingDirectory=/opt/signal-school/academy
ExecStart=/usr/bin/python3 -m http.server 8000 --bind 0.0.0.0
Restart=on-failure
NoNewPrivileges=true
PrivateDevices=true
ProtectSystem=strict
ProtectHome=true

[Install]
WantedBy=multi-user.target
```

Enable it:

```bash
systemctl daemon-reload
systemctl enable --now signal-academy.service
systemctl status signal-academy.service
```

The academy URL is:

```text
http://10.77.0.10:8000
```

## 5. Provision each student VM

### Proxmox settings

- Name: `student-01`
- OS: Linux Mint, Ubuntu Desktop, or Debian Desktop
- Machine/BIOS: Proxmox defaults are fine
- Disk: 24 GB, discard enabled if supported
- CPU: 2 cores, type `host` if live migration is not needed
- Memory: 4 GB
- Network model: VirtIO
- Network bridge: `vmbr77`
- IPv4: static `10.77.0.21/24`
- Gateway: leave blank
- DNS: blank is acceptable for the isolated exercise
- Proxmox guest agent: install and enable if convenient

Create a normal, non-administrator learner account such as `trainee`. Keep the administrator/sudo password to yourself.

Install the required tools before disconnecting any temporary internet interface:

```bash
sudo apt update
sudo apt install -y nmap openssh-client curl iproute2
```

Firefox is normally already present. Chromium is also fine.

Set the static address using the desktop network settings, or with NetworkManager:

```bash
nmcli connection show
sudo nmcli connection modify "Wired connection 1" \
  ipv4.method manual ipv4.addresses 10.77.0.21/24 \
  ipv4.gateway "" ipv4.dns ""
sudo nmcli connection up "Wired connection 1"
```

Use the appropriate address for each additional VM. After configuration, take a clean snapshot named `ready-for-signal-school`.

## 6. Provision the Relay Station VM

### Proxmox settings

- Name: `relay-08`
- OS: minimal Debian 12
- Disk: 8 GB
- CPU: 1 core
- Memory: 1 GB
- Network model: VirtIO
- Network bridge: `vmbr77`
- IPv4: static `10.77.0.80/24`
- Gateway: leave blank
- Start at boot: **disabled**
- Host-to-guest clipboard and shared storage: do not configure

During Debian installation, select only **SSH server** and **standard system utilities**. Create your own temporary administrator account; do not name it `operator`.

Copy the project's `relay-station` folder into the VM. From that folder run:

```bash
sudo sh setup-relay.sh
```

The setup script:

- Creates the non-sudo `operator` account.
- Starts the intentionally vulnerable HTTP service on TCP 8080.
- Creates the recoverable password file and final flag.
- Refuses to run the web service as root.

Confirm password-based SSH login is available for this disposable lab account. On Debian, inspect the effective setting with:

```bash
sudo sshd -T | grep passwordauthentication
```

If it reports `passwordauthentication no`, create `/etc/ssh/sshd_config.d/90-signal-school.conf` containing:

```text
PasswordAuthentication yes
PermitRootLogin no
```

Then validate and reload SSH:

```bash
sudo sshd -t
sudo systemctl reload ssh
```

Do not give `operator` sudo access. Take a snapshot named `clean-relay-challenge` after testing.

## 7. Firewall policy

Network isolation is the primary control. If Proxmox Firewall is enabled, use these guest rules as defense in depth.

### Academy LXC

- Allow inbound TCP 8000 from `10.77.0.0/24`.
- Allow established/related traffic.
- Drop other inbound traffic.

### Student VM

- Allow established/related traffic.
- No inbound services are required.

### Relay Station VM

- Allow inbound TCP 22 from `10.77.0.0/24`.
- Allow inbound TCP 8080 from `10.77.0.0/24`.
- Allow established/related traffic.
- Drop other inbound traffic.

Do not accidentally block ICMP or host discovery will be less obvious. `nmap` can still find hosts in other ways, but allowing ICMP makes the first exercise more predictable.

## 8. Pre-flight test

Perform these checks from `student-01` before handing it over.

### Confirm the academy

```bash
curl -I http://10.77.0.10:8000
```

Expected: `HTTP/1.0 200 OK`. Open `http://10.77.0.10:8000` in the browser and confirm the lesson page loads.

### Confirm discovery and enumeration

```bash
nmap -sn 10.77.0.0/24
nmap -sV 10.77.0.80
```

Expected on `relay-08`:

- TCP 22: SSH
- TCP 8080: HTTP

### Confirm the challenge path

Open `http://10.77.0.80:8080`. In the diagnostic field, test:

```text
127.0.0.1; whoami
```

Expected output includes `operator`. Then confirm the intended credential recovery and SSH login work as described in `relay-station/README.md`.

### Confirm isolation

From `relay-08`, verify that it cannot reach the internet or your normal LAN. For example, both of these should fail:

```bash
ping -c 1 1.1.1.1
ping -c 1 <an-address-on-your-normal-LAN>
```

After testing, revert `relay-08` to `clean-relay-challenge` so the children start from a known state.

## 9. Exercise-day checklist

- [ ] `academy`, student VM(s), and `relay-08` are connected only to `vmbr77`.
- [ ] `relay-08` has no WAN/LAN interface, host mount, secret, or sudo-capable `operator` account.
- [ ] Academy opens at `http://10.77.0.10:8000`.
- [ ] Student VM has `nmap`, `ssh`, `curl`, and a browser.
- [ ] `nmap -sn 10.77.0.0/24` reveals the lab guests.
- [ ] Relay exposes only the intended SSH and HTTP services.
- [ ] The vulnerable form and `operator` SSH login have been tested.
- [ ] Clean snapshots exist for every student VM and the Relay Station.
- [ ] Children know the scope: only `10.77.0.0/24`, stop at the flag, and change or delete nothing.

## 10. Reset and shutdown

At the end of the exercise:

1. Shut down `relay-08`.
2. Revert it to `clean-relay-challenge` before the next session.
3. Revert student VMs if desired.
4. Keep the vulnerable VM powered off when it is not actively being used.
5. Remove any temporary internet-facing interface added during setup.

## Fastest possible variant

If you want fewer guests, serve the academy directly from the student VM and use only two VMs:

```bash
cd academy
python3 -m http.server 8000 --bind 127.0.0.1
```

The child opens `http://127.0.0.1:8000`, while `relay-08` remains the only separate target. This is simpler, but discovering the academy host is no longer part of the network picture.
