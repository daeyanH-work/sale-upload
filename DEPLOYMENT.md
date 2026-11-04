# Deployment Guide – Sale Upload (Docker)

The app is served at **http://<server-ip>:5170**.

## Architecture

```
Browser ──► :5170  nginx (frontend container, serves React build)
                     └─ /api/*  ──► backend:8001 (FastAPI, internal only)
```

Only port **5170** is published. The backend is reachable only inside the Docker network.

## Prerequisites

- A Linux server (or Windows with Docker Desktop) with:
  - Docker Engine 24+ and Docker Compose v2 (`docker compose version`)
  - Git
- Port **5170/tcp** open in the firewall / cloud security group.

Install Docker on Ubuntu if needed:

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER   # log out/in afterwards
```

## Deploy

```bash
git clone <repo-url> sale-upload
cd sale-upload
git checkout main            # or the branch you want to deploy

docker compose up -d --build
```

Verify:

```bash
docker compose ps
curl http://localhost:5170/api/health      # {"status":"ok"}
```

Open `http://<server-ip>:5170` in a browser.

## Firewall

```bash
# Ubuntu (ufw)
sudo ufw allow 5170/tcp
```

On cloud providers (AWS/Azure/GCP), also add an inbound rule for TCP 5170.

## Operations

| Task | Command |
|------|---------|
| View logs | `docker compose logs -f` |
| Backend logs only | `docker compose logs -f backend` |
| Restart | `docker compose restart` |
| Stop | `docker compose down` |
| Update to latest code | `git pull && docker compose up -d --build` |

Containers use `restart: unless-stopped`, so they come back after a server reboot.

## Changing the port

Edit `docker-compose.yml` (`"5170:5170"` → `"<new>:5170"`) and `docker compose up -d`.

## Notes

- The app is stateless; uploaded files are processed in memory and nothing needs a volume or backup.
- Max upload size is 100 MB (`client_max_body_size` in `frontend/nginx.conf`).
- The **Marnics** client is disabled in the dropdown (commented out in `backend/main.py`). Its processor `backend/processors/marnics.py` is retained; to re-enable, uncomment the entry in `CLIENTS` and rebuild.
- The app has no authentication. Put it behind a VPN/reverse proxy with auth if exposed to the internet.

## Troubleshooting

- **Page loads but dropdown is empty / API errors:** `docker compose logs backend`.
- **Can't connect from another machine:** check firewall/security group for 5170.
- **Port already in use:** `sudo lsof -i :5170`, then stop the other service or change the port.
- **Build fails on `npm ci`:** ensure `frontend/package-lock.json` is committed.
