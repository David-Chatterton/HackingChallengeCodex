# Signal School ethical hacking lab

This project contains:

- `academy/`: a static teaching microsite, served with `python3 -m http.server 8000`
- `relay-station/`: a deliberately vulnerable second-VM challenge on port 8080

Read both folder READMEs before deployment. Keep the relay on a private Proxmox bridge or VLAN and never expose it to the internet.

For the recommended Proxmox topology, guest specifications, exact setup steps, firewall policy, and pre-flight checks, follow [`PROVISIONING.md`](PROVISIONING.md).
