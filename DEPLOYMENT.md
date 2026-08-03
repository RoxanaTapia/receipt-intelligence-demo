# Deployment Guide

Single-VM Hetzner path for the Receipt Intelligence demo umbrella: Docker Compose (n8n writer + API reader) behind Caddy (HTTPS + basic auth).

Product logic stays in the sibling repos; this guide covers **firewall → `.env` → auth → up → verify**.

```mermaid
flowchart TD
  prep[Prepare VPS + firewall] --> env[Clone + configure .env]
  env --> auth[Generate basic auth]
  auth --> up[Compose + Caddy up]
  up --> verify[Verify HTTPS + login]
```

> **Takeaway:** On the VPS path, publish only **22 / 80 / 443**. App ports stay on the Compose network; Caddy is the public edge.

---

## ✅ Prerequisites

| Requirement | Notes |
|-------------|-------|
| **Docker 24+** | Compose v2 plugin (`docker compose`) |
| **git** | Clone this repo + sibling API (build context) |
| **SSH access** | Hetzner (or any) Ubuntu/Debian VPS |
| **Outbound internet** | Image pulls + Let's Encrypt (domain mode) |
| **Domain (optional)** | Needed for ACME TLS; otherwise use [IP-interim](#ip-interim-no-domain-yet) |

Human ops (not automated here): create the VM, point DNS A/AAAA at the VPS when you have a domain.

---

## 💻 VPS sizing

| Profile | Hardware | Use |
|---------|----------|-----|
| **Demo / portfolio** | 4 vCPU / 8 GB RAM (e.g. Hetzner **CPX31** or **CPX32**) | n8n + API + Caddy; comfortable headroom for Anthropic calls |
| **Minimal smoke** | 2 vCPU / 4 GB | Possible for light checks; tight if n8n + builds run together |

Disk: ~20 GB+ free for images and receipt JSON under `data/receipts/`.

---

## 🌐 What ports are public?

| Port | Public? | Role |
|------|---------|------|
| **22** | Yes | SSH |
| **80** | Yes | HTTP → ACME / redirect (Caddy) |
| **443** | Yes | HTTPS (Caddy) |
| **8000** | No (VPS + Caddy) | API — Compose network only |
| **5678** | No (VPS + Caddy) | n8n — Compose network only |

Local smoke **without** Caddy still publishes API/n8n on the host (see [README](README.md)). The Caddy overlay strips those host publishes with `ports: !override []`.

---

## 🚀 Deploy on Hetzner (happy path)

### 1. Prepare the server

```bash
sudo apt-get update && sudo apt-get install -y git ca-certificates curl
# Install Docker 24+ per https://docs.docker.com/engine/install/
sudo usermod -aG docker "$USER"   # log out and back in after this
```

**Firewall** — open only SSH and Caddy:

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status
```

### 2. Clone and configure

Clone **this repo** and the API sibling next to it (Compose build context default):

```text
/opt/receipt-intelligence/   # example layout on the VPS
├── receipt-intelligence-api
└── receipt-intelligence-demo
```

```bash
mkdir -p /opt/receipt-intelligence && cd /opt/receipt-intelligence
git clone https://github.com/RoxanaTapia/receipt-intelligence-api.git
git clone https://github.com/RoxanaTapia/receipt-intelligence-demo.git
cd receipt-intelligence-demo
cp .env.example .env
nano .env
```

Minimum `.env` for **domain mode** (Let's Encrypt):

```bash
N8N_BASIC_AUTH_PASSWORD=change-me-strong
ANTHROPIC_API_KEY=          # if you will run workflows / Q&A

COMPOSE_PROJECT_NAME=receipt-intelligence-demo
SITE_ADDRESS=demo.example.com
ACME_EMAIL=you@example.com

# Public URLs for n8n behind Caddy at /n8n*
N8N_HOST=demo.example.com
N8N_PROTOCOL=https
N8N_PATH=/n8n
WEBHOOK_URL=https://demo.example.com/n8n/
```

DNS: point `SITE_ADDRESS` A/AAAA at this VPS before the first Caddy up (ACME needs to reach :80/:443).

### 3. Generate basic-auth credentials

```bash
chmod +x deploy/generate-caddy-auth.sh deploy/generate-ip-tls.sh
./deploy/generate-caddy-auth.sh demo 'YOUR_STRONG_PASSWORD'
```

Writes `deploy/caddy-basicauth.conf` (gitignored). Re-run to rotate the password. Edge basic auth is separate from n8n’s own `N8N_BASIC_AUTH_*`.

### 4. Start the stack with Caddy

From the **repo root**:

```bash
docker compose --env-file .env -p receipt-intelligence-demo \
  -f deploy/docker-compose.yml -f deploy/docker-compose.caddy.yml up --build -d

docker compose --env-file .env -p receipt-intelligence-demo \
  -f deploy/docker-compose.yml -f deploy/docker-compose.caddy.yml ps
```

Expect: `api` healthy · `n8n` Up · `caddy` Up. Host should **not** publish 8000/5678.

Set `COMPOSE_PROJECT_NAME=receipt-intelligence-demo` in `.env` so you can omit `-p` later. Always pass `--env-file .env` when the first compose file lives under `deploy/`.

### 5. Verify

```bash
# 401 without credentials, 200 with (API health via edge)
curl -sk -o /dev/null -w "%{http_code}\n" https://YOUR_DOMAIN/health
curl -sk -o /dev/null -w "%{http_code}\n" -u demo:YOUR_PASSWORD https://YOUR_DOMAIN/health
```

Open `https://YOUR_DOMAIN/docs` (API) or `https://YOUR_DOMAIN/n8n/` (n8n UI) and complete the browser basic-auth prompt.

Until [issue #3](https://github.com/RoxanaTapia/receipt-intelligence-demo/issues/3), `/` proxies to the API. Demo UX will take the visitor surface later.

---

## 📌 IP-interim (no domain yet)

Use when the VM exists but DNS is not ready. Same public ports; self-signed TLS (browser warning expected).

```bash
# In .env — do not set SITE_ADDRESS for this mode
CADDYFILE=./Caddyfile.ip
# Path is relative to deploy/ when Compose resolves volumes.

./deploy/generate-caddy-auth.sh demo 'YOUR_STRONG_PASSWORD'
./deploy/generate-ip-tls.sh YOUR_VPS_IP

# Optional: point n8n public URL at the IP (still path-prefixed)
N8N_HOST=YOUR_VPS_IP
N8N_PROTOCOL=https
N8N_PATH=/n8n
WEBHOOK_URL=https://YOUR_VPS_IP/n8n/
```

```bash
docker compose --env-file .env -p receipt-intelligence-demo \
  -f deploy/docker-compose.yml -f deploy/docker-compose.caddy.yml up --build -d

curl -sk -o /dev/null -w "%{http_code}\n" -u demo:YOUR_PASSWORD https://YOUR_VPS_IP/health
```

**Cutover IP → domain:** set `SITE_ADDRESS` + `ACME_EMAIL`, remove `CADDYFILE=./Caddyfile.ip`, update `N8N_HOST` / `WEBHOOK_URL`, recreate Caddy (`docker compose … up -d --force-recreate caddy`). Let's Encrypt issues the cert automatically.

---

## 🖥️ Local development (no Caddy)

Unchanged from [README](README.md): base compose only, host ports 8000/5678.

```bash
cp .env.example .env
# set N8N_BASIC_AUTH_PASSWORD

docker compose --env-file .env -f deploy/docker-compose.yml up --build -d
curl -s http://localhost:8000/health
```

To exercise Caddy locally, use IP-interim with `127.0.0.1` (self-signed) and the same two-file compose command.

---

## 🔧 Troubleshooting

| Symptom | Likely cause | Check |
|---------|--------------|-------|
| Connection refused on 443 | Firewall or Caddy down | `ufw status`; `docker compose … ps` |
| Browser TLS warning (domain mode) | DNS not pointing here / ACME failed | A/AAAA → this VM; `docker compose … logs caddy` |
| 502 after login | Backend not ready | From stack: `exec` into a container and `wget -qO- http://api:8000/health` |
| `caddy-basicauth.conf: is a directory` | Bad bind path / project-directory misuse | Run compose from repo root **without** `--project-directory`; regenerate auth file |
| :8000 or :5678 reachable from the internet | Caddy overlay not applied | Confirm both `-f` files and `ports: !override []` |

---

## 📚 Related

| Doc | Role |
|-----|------|
| [README.md](README.md) | Local compose smoke |
| [AGENTS.md](AGENTS.md) | Ship order and agent workflow |
| [n8n integration](https://github.com/RoxanaTapia/receipt-intelligence-n8n/blob/main/docs/integration.md) | Workflow import / sample PDFs |
| [ai-doc deploy pattern](https://github.com/RoxanaTapia/ai-doc-to-chat-pipeline/tree/main/deploy) | Reference Compose + Caddy layout |
