---
mode: agent
description: Set up local SSH prerequisites (key + sshd) and run a deplodock bench --local sweep.
---

# Set up local SSH and run a local benchmark

`deplodock bench` always connects to its target over SSH — even the local machine, via
`127.0.0.1`. So before `bench --local` can work, this host needs an SSH keypair authorized for
itself and a running `sshd`. Perform the steps below, verifying each one before moving on. The
setup is idempotent: skip any step that is already satisfied.

## 1. Check current state

Run and report what is missing:

```bash
ls -la ~/.ssh 2>/dev/null | grep -E 'id_ed25519|authorized_keys' || echo "no key"
command -v sshd || echo "no sshd"
ss -tlnp 2>/dev/null | grep ':22 ' || echo "nothing on :22"
```

## 2. Create the SSH key and authorize it (no sudo)

Only if `~/.ssh/id_ed25519` does not already exist:

```bash
install -d -m 700 ~/.ssh
ssh-keygen -t ed25519 -N "" -f ~/.ssh/id_ed25519 -q
grep -qxF "$(cat ~/.ssh/id_ed25519.pub)" ~/.ssh/authorized_keys 2>/dev/null \
  || cat ~/.ssh/id_ed25519.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

## 3. Install and start sshd (needs sudo)

If `sshd` is not installed, install it, then enable/start the service. The `service` fallback
covers WSL where systemd may not be running. **The user must type their sudo password directly
into the terminal — never request it through the chat.**

```bash
command -v sshd >/dev/null || { sudo apt-get update && sudo apt-get install -y openssh-server; }
sudo systemctl enable --now ssh 2>/dev/null || sudo service ssh start
```

## 4. Verify key-based login to localhost

This is exactly the path `bench --local` uses. It must print `LOGIN_OK`:

```bash
ss -tlnp 2>/dev/null | grep ':22 '
ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new \
  -i ~/.ssh/id_ed25519 "$USER@127.0.0.1" 'echo LOGIN_OK; hostname'
```

## 5. Free port 8000 and run the benchmark

Any leftover `deploy local` container holds port 8000, which collides with the bench deploy.
Stop it first, then run the sweep:

```bash
docker rm -f vllm_0 2>/dev/null || true
./venv/bin/deplodock bench recipes/Qwen3-Coder-30B-A3B-Instruct-AWQ --local
```

Report the final SUMMARY (successful / failed variants) and the run-directory path from the
output. If any variant fails, read its `benchmark.log` and diagnose before stopping.
