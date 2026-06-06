---
mode: agent
description: Stop the local sshd that was started for deplodock bench --local.
---

# Stop the local sshd

Stop the OpenSSH server that was started so `deplodock bench --local` could reach `127.0.0.1`.
The SSH key and `authorized_keys` entry are intentionally left in place — they are cheap to keep
and let you re-enable later by simply restarting the service.

## 1. Stop the service

Try systemd first, then the SysV/WSL `service` fallback. Also stop the socket unit, since on
systemd `ssh.socket` will re-spawn `sshd` on the next connection if left enabled. **The user must
type their sudo password directly into the terminal — never request it through the chat.**

```bash
sudo systemctl disable --now ssh 2>/dev/null || sudo service ssh stop
sudo systemctl stop ssh.socket 2>/dev/null || true
```

## 2. Verify nothing is listening on port 22

```bash
ss -tlnp 2>/dev/null | grep ':22 ' && echo "STILL LISTENING" || echo "sshd stopped"
```

Report whether port 22 is now closed. If something is still listening, identify the process from
the `ss` output and stop it before finishing.
