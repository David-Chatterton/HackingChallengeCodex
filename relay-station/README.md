# Relay Station challenge VM

This is an intentionally vulnerable service for a dedicated, disposable lab VM. It must never be exposed to the internet or a network containing untrusted devices.

## Recommended VM

- Fresh Debian 12 or Ubuntu Server VM (not the Proxmox host)
- A private, isolated Proxmox bridge/VLAN shared only with the student VM
- Snapshot before the exercise
- No mounted host storage, tokens, SSH keys, or personal data
- Firewall: allow TCP 8080 and TCP 22 only from the training subnet; block WAN access

Copy this folder to the challenge VM, then run:

```bash
sudo sh setup-relay.sh
```

The script creates a non-sudo `operator` account, starts the vulnerable site on port 8080, and creates the final flag. The server refuses to run as root. Confirm that OpenSSH Server is installed and password login is enabled for this disposable lab account; some cloud images disable password login by default.

## Intended solution

1. Discover the relay VM with `nmap -sn <lab-subnet>/24`.
2. Enumerate it with `nmap -sV <relay-ip>` and find SSH/22 plus HTTP/8080.
3. Visit `http://<relay-ip>:8080` and inspect page source.
4. Notice the shell hint and backup path.
5. Submit `127.0.0.1; whoami`, then `127.0.0.1; cat /home/operator/relay/ssh-code.txt`.
6. Log in with `ssh operator@<relay-ip>` and the recovered password.
7. Run `ls -la`, then `cat MISSION_COMPLETE.txt`.

Stop the exercise at the flag. Reset the VM snapshot afterward. The `operator` account has no sudo rights and the systemd unit adds basic containment, but network isolation remains essential.
