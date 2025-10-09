# Marketplace Backend (FastAPI)

Backend for a university marketplace of tech products and school supplies, ready for a Flutter mobile app.
Includes: FastAPI, Postgres+PostGIS, Redis, MinIO (S3), workers for concurrent tasks, JWT authentication, presigned image uploads, telemetry, and analytics endpoints.

---

## Requirements

#### Windows (10/11)

### Option A — PowerShell + winget (fast & native)

> Requirements: Windows 10 21H2+ or Windows 11, admin permissions.

1. **Install Docker Desktop (WSL2 backend) + utilities**

```powershell
# Open PowerShell as Administrator
winget install --id Docker.DockerDesktop -e
winget install --id jqlang.jq -e
winget install --id ShiningLight.OpenSSL.Light -e
# curl comes preinstalled on Windows 10/11 (curl.exe). To add Git Bash:
winget install --id Git.Git -e
```

2. **Enable WSL2 (if requested by Docker)**

```powershell
# Enable features and restart when prompted
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
wsl --set-default-version 2
```

> (Optional) Install **Ubuntu** from Microsoft Store if you prefer a Linux environment.

3. **Verify installation**

```powershell
docker version
docker compose version
curl.exe --version
jq --version
& "C:\Program Files\OpenSSL-Win64\bin\openssl.exe" version  # adjust path if needed
```

4. **Clone the repo and bring up the stack**

```powershell
# In PowerShell, navigate to the project folder (shared volumes must be enabled in Docker Desktop: Settings > Resources > File Sharing)
copy .env.example .env     # if applicable
docker compose -f docker-compose.yml -f docker-compose.api.yml up -d --build
docker compose -f docker-compose.yml -f docker-compose.api.yml logs -f api
```

> ⚠️ In PowerShell, **use `curl.exe`** (not `curl`) to avoid the `Invoke-WebRequest` alias.

---

### Option B — WSL (Ubuntu) or Git Bash (for running `.sh` / `.zsh` scripts)

Ideal if you want to run the **E2E scripts** included in `tests/e2e.sh` and `tests/e2e.zsh`.

1. **Install Ubuntu (WSL)**

* Microsoft Store → “Ubuntu” → Install → create Linux user
* Docker Desktop → Settings → *Resources > WSL Integration* → enable your distro

2. **From Ubuntu (WSL) install utilities**

```bash
sudo apt-get update
sudo apt-get install -y curl jq openssl
```

3. **Use Docker Desktop (Windows) with WSL**

* In Ubuntu, go to the mounted project directory (e.g., `/mnt/c/Users/<your_user>/path/to/project`)
* Bring up the stack:

```bash
docker compose -f docker-compose.yml -f docker-compose.api.yml up -d --build
docker compose -f docker-compose.yml -f docker-compose.api.yml logs -f api
```

#### Notes and tips for Windows

* **Firewall** – When starting containers for the first time, Windows may ask for permissions; allow for `localhost`.
* **File Sharing** – In Docker Desktop → *Settings > Resources > File Sharing*, add the project folder if volumes don’t mount.
* **Ports** – If `:8000` is taken, change `API_PORT` in `.env` or in the compose `ports:` section.
* **Tokens** – If you change `JWT_SECRET`, log in again (old tokens become invalid).
* **MinIO/S3** – When testing presigned uploads, ensure MinIO shows as *healthy* in Docker Desktop.

Windows users can install everything and run the API/tests without issues.

---

## Environment Variables

Create a **`.env`** file in the repository root:

```ini
# --- API ---
APP_ENV=local
API_HOST=0.0.0.0
API_PORT=8000

# --- JWT ---
JWT_SECRET=super-secret-labs-uniandes
JWT_ALG=HS256
JWT_ACCESS_MIN=30
JWT_REFRESH_DAYS=30

# --- DB (Postgres + PostGIS) ---
DB_HOST=db
DB_PORT=5432
DB_USER=app_user
DB_PASSWORD=app_password
DB_NAME=app_db
DATABASE_URL=postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}

# --- Redis ---
REDIS_URL=redis://redis:6379/0

# --- S3/MinIO ---
S3_ENDPOINT=http://minio:9000
S3_REGION=us-east-1
S3_BUCKET=market-uploads
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_USE_PATH_STYLE=true

# --- Optional rate limit ---
RATE_LIMIT=120/minute
```

**Notes**

* Keep `JWT_SECRET` consistent (if changed, old tokens stop working).
* By default, Postgres+PostGIS, Redis, and MinIO run through `docker-compose`.

---

## Launch the project

```bash
docker compose -f docker-compose.yml -f docker-compose.api.yml up -d --build
docker compose -f docker-compose.yml -f docker-compose.api.yml logs -f api
```

Expected logs:

* “DB extensions ensured (postgis, pgcrypto, citext).”
* “Seeded base categories.”
* “Redis ping: True”
* Uvicorn running at `http://0.0.0.0:8000`
* Swagger: `http://localhost:8000/docs`
* OpenAPI: `http://localhost:8000/openapi.json`

---

## Seeding

If you have a SQL seed script:

```bash
docker compose exec -T db psql -U app_user -d app_db -f scripts/seed.sql
```

---

## Database / Storage Variants

* **Postgres + PostGIS (RECOMMENDED)** – preconfigured (proximity search, `postgis`, `pgcrypto`, `citext`).
* **Image storage** – MinIO/S3 via `/v1/images/presign` and `/v1/images/confirm`.

---

## End-to-End (E2E) Tests

Two equivalent scripts:

* `tests/e2e.zsh` (Z shell)
* `tests/e2e.sh` (Bash)

**Run (zsh):**

```bash
chmod +x test/e2e.zsh
BASE=http://localhost:8000/v1 PASS=Passw0rd ./test/e2e.zsh
```

**Run (bash):**

```bash
chmod +x test/e2e.sh
BASE=http://localhost:8000/v1 PASS=Passw0rd ./test/e2e.sh
```

> Both scripts by default:
>
> * Register and log in a user
> * Query categories and brands
> * Create a listing
> * Simulate presigned image upload and confirmation
> * Create a chat and send a message
> * Create an order, pay/capture, simulate escrow step and complete
> * Create a review
> * Call analytics endpoints (BQ 1.1 & 1.2)
> * Register device, match contacts by hash, and test `/sync/delta`

If you changed `JWT_SECRET`, log in again to issue a new token.

---

## Key Endpoints & Parameters (Summary)

* **Auth**

  * `POST /v1/auth/register` → `{name,email,password,campus?}`
  * `POST /v1/auth/login` → `{email,password}` ⇒ `{access_token,refresh_token}`
  * `POST /v1/auth/refresh` → `{refresh_token}`
  * `GET /v1/auth/me` (Bearer)

* **Catalogs**

  * `GET /v1/categories`
  * `GET /v1/brands`

* **Listings**

  * `POST /v1/listings` → requires `category_id`, price, etc. May include `latitude/longitude` for geolocation.
  * `GET /v1/listings/{id}`
  * `GET /v1/listings` filters: `q`, `category_id`, `brand_id`, `min_price`, `max_price`,
    **geo**: `near_lat`, `near_lon`, `radius_km` + `page`, `page_size`.

* **Images (Camera/Gallery)**

  * `POST /v1/images/presign` → `{filename, content_type, scope:"listing", listing_id}`
  * (Presigned upload to S3/MinIO)
  * `POST /v1/images/confirm` → `{scope, listing_id, storage_key, width, height}`

* **Chats/Messages**

  * `POST /v1/chats` → `{listing_id}`
  * `POST /v1/messages` → `{chat_id, message_type, content}`

* **Orders/Payments/Escrow**

  * `POST /v1/orders` → `{listing_id, quantity}`
  * `POST /v1/orders/{id}/pay`
  * `POST /v1/payments/capture` → `{order_id}`
  * `POST /v1/escrow/step` → `{order_id, step}`
  * `POST /v1/orders/{id}/complete`

* **Disputes/Reviews**

  * `POST /v1/disputes/open` → `{order_id, raised_by:"buyer|seller", reason}`
  * `POST /v1/reviews/orders/{id}` → `{rating, comment?}`

* **Features / Telemetry / Analytics**

  * `POST /v1/features/use` → `{key, action}`
  * `POST /v1/events` → `{event_type, session_id, properties:{...}}`
  * `GET /v1/analytics/bq/1_1?from=...&to=...` (BQ 1.1)
  * `GET /v1/analytics/bq/1_2?from=...&to=...` (BQ 1.2)

* **Devices / Contacts / Sync**

  * `POST /v1/devices` → `{platform, push_token, app_version}`
  * `POST /v1/contacts/match` → `{email_hashes:[sha256_hex,...]}`
  * `GET /v1/sync/delta?since=<RFC3339>`

---

## Requirements and How They’re Met

1. **Phone sensor** – GPS (filter by `near_lat/near_lon/radius_km`), camera via presigned upload flow.
2. **External app data** – Contacts → app reads emails and sends **hashes** to `/contacts/match`.
3. **Offline cache** – Uses `/sync/delta` for incremental sync + SQLite/Hive local cache.
4. **Concurrency** – `worker` and `beat` handle tasks (price suggestions, thumbnails, cleanup).
5. **Local storage (on device)** – tokens (secure storage), cached data (SQLite/Hive), offline action queue.

**“Smart features” and context** – price suggestions, quick-view, location-based results, feature flags.
**Type 2 BQs** – UI telemetry and filter events via `/events` – implemented in `/v1/analytics/bq/*`.

---

## Troubleshooting

* **401 / “Invalid or expired token”** – log in again; check `JWT_SECRET`.
* **PostGIS** – verify logs show “DB extensions ensured (postgis, pgcrypto, citext)”.
* **Image uploads** – ensure `/v1/images/presign` returns `url` and `fields` and MinIO is healthy.
* **Port conflicts** – adjust `API_PORT` or service ports in `docker-compose`.

---

