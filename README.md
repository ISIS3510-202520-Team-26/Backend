# Marketplace Backend (FastAPI)

Backend for a university marketplace of tech products and school supplies, ready for a Flutter mobile app.
Stack: **FastAPI**, **Postgres + PostGIS**, **Redis**, **MinIO (S3)**, **workers** for concurrent tasks, **JWT** auth, **presigned image uploads**, **telemetry**, and **analytics (BQ)**.

---

## Requirements

### Windows (10/11)

#### Option A — PowerShell + winget (fast & native)

> Requirements: Windows 10 21H2+ or Windows 11, admin permissions.

1. **Install Docker Desktop (WSL2) + utilities**

```powershell
# Open PowerShell as Administrator
winget install --id Docker.DockerDesktop -e
winget install --id jqlang.jq -e
winget install --id ShiningLight.OpenSSL.Light -e
# curl ships with Windows 10/11; to add Git Bash:
winget install --id Git.Git -e
```

2. **Enable WSL2 (if Docker requests it)**

```powershell
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
wsl --set-default-version 2
```

> (Optional) Install **Ubuntu** from Microsoft Store if you prefer a Linux shell.

3. **Verify**

```powershell
docker version
docker compose version
curl.exe --version
jq --version
& "C:\Program Files\OpenSSL-Win64\bin\openssl.exe" version
```

4. **Clone and bring up the stack**

```powershell
copy .env.example .env     # if applicable
docker compose -f docker-compose.yml -f docker-compose.api.yml up -d --build
docker compose -f docker-compose.yml -f docker-compose.api.yml logs -f api
```

> ⚠️ In PowerShell, **use `curl.exe`** (not `curl`) to avoid the `Invoke-WebRequest` alias.

---

#### Option B — WSL (Ubuntu) or Git Bash (to run `.sh` / `.zsh` scripts)

Ideal to run the **E2E scripts** in `test/e2e.sh` and `test/e2e.zsh`.

1. **Install Ubuntu (WSL)**
   Microsoft Store → “Ubuntu” → Install → create Linux user
   Docker Desktop → Settings → *Resources > WSL Integration* → enable your distro

2. **Install utilities (from Ubuntu)**

```bash
sudo apt-get update
sudo apt-get install -y curl jq openssl
```

3. **Use Docker Desktop (Windows) with WSL**

```bash
docker compose -f docker-compose.yml -f docker-compose.api.yml up -d --build
docker compose -f docker-compose.yml -f docker-compose.api.yml logs -f api
```

**Windows tips**

* **Firewall**: allow permissions for `localhost` on first container start.
* **File Sharing**: Docker Desktop → *Settings > Resources > File Sharing*, add your project folder if volumes don’t mount.
* **Ports**: if `:8000` is taken, change `API_PORT` in `.env` or in the compose `ports:`.
* **Tokens**: if you change `JWT_SECRET`, log in again (old tokens become invalid).
* **MinIO/S3**: ensure MinIO shows as *healthy* in Docker Desktop for presigned uploads.

---

## Environment Variables

Create a **`.env`** file in the repo root:

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

* Changing `JWT_SECRET` invalidates existing tokens—log in again.
* Postgres+PostGIS, Redis, and MinIO run via `docker-compose`.

---

## Launch

```bash
docker compose -f docker-compose.yml -f docker-compose.api.yml up -d --build
docker compose -f docker-compose.yml -f docker-compose.api.yml logs -f api
```

Expected logs:

* “DB extensions ensured (postgis, pgcrypto, citext).”
* “Seeded base categories.”
* “Redis ping: True”
* Uvicorn at `http://0.0.0.0:8000`
* Swagger: `http://localhost:8000/docs`
* OpenAPI: `http://localhost:8000/openapi.json`

---

## Seeding

```bash
docker compose exec -T db psql -U app_user -d app_db -f scripts/seed.sql
```

---

## Database / Storage Variants

* **Postgres + PostGIS (RECOMMENDED)** – proximity search, `postgis`, `pgcrypto`, `citext`.
* **Image storage** – MinIO/S3 via `/v1/images/presign` + `/v1/images/confirm`.

---

## End-to-End (E2E) Tests

Two equivalent scripts:

* `test/e2e.zsh` (Z shell)
* `test/e2e.sh` (Bash)

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

What they cover:

* Register & login (SELLER/BUYER) + `GET /auth/me`
* Catalogs (`/categories`, `/brands`)
* Listing: create & fetch, **geo search** (`near_lat`, `near_lon`, `radius_km`)
* Presigned image upload **PUT** + confirmation
* Chat + message
* Order → pay (202) → (optional) escrow step → capture → complete
* Review
* **Telemetry & Features**: `/features/use`, `/events` (e.g., `ui.click`, `feature.used`, `escrow.step`)
* **Analytics BQ**: `1_1`, `1_2`, **`2_1`**, **`2_2`**, **`3_1`**, **`3_2`**, **`4_1`**, **`4_2`**, **`5_1`**
* Devices, contacts match (hashed), **delta sync** (`/sync/delta`)

> If you change `JWT_SECRET`, log in again to get fresh tokens.

---

## Key Endpoints (Summary)

### Auth

* `POST /v1/auth/register` → `{name,email,password,campus?}`
* `POST /v1/auth/login` → `{email,password}` ⇒ `{access_token,refresh_token}`
* `POST /v1/auth/refresh` → `{refresh_token}`
* `GET /v1/auth/me` (Bearer)

### Catalogs

* `GET /v1/categories`
* `GET /v1/brands`

### Listings

* `POST /v1/listings`
  Minimum body: `{title, description, category_id, brand_id, price_cents, currency, condition, quantity}`
  Optional: `latitude`, `longitude`, `price_suggestion_used`, `quick_view_enabled`
* `GET /v1/listings/{id}`
* `GET /v1/listings`
  Filters: `q`, `category_id`, `brand_id`, `min_price`, `max_price`,
  **Geo**: `near_lat`, `near_lon`, `radius_km` + `page`, `page_size`

### Images (Camera/Gallery)

* `POST /v1/images/presign` → `{filename, content_type, scope:"listing", listing_id}`
  ⇒ `{upload_url, object_key}`
* **PUT** the binary to `upload_url` with the exact `Content-Type`
* `POST /v1/images/confirm` → `{scope, listing_id, object_key, width, height}`
  ⇒ `{preview_url}`

### Chats / Messages

* `POST /v1/chats` → `{listing_id}`
* `POST /v1/messages` → `{chat_id, message_type:"text", content}`

### Orders / Payments / Escrow

* `POST /v1/orders` → `{listing_id, quantity}`
* `POST /v1/orders/{id}/pay` ⇒ `202 Accepted` (async processing)
* `POST /v1/payments/capture` → `{order_id, provider_ref?}`
* `POST /v1/escrow/step` → `{escrow_id, order_id, step, result}`
* `POST /v1/orders/{id}/complete`

### Disputes / Reviews

* `POST /v1/disputes/open` → `{order_id, raised_by:"buyer|seller", reason}`
* `POST /v1/reviews/orders/{id}` → `{rating, comment?}`
  (fallback: `POST /v1/reviews` with `{order_id, ratee_id, rating, comment?}`)

### Features / Telemetry / Analytics

#### Telemetry ingestion

* `POST /v1/events`

  ```json
  {
    "events":[
      {
        "event_type":"ui.click",
        "session_id":"<random-stable-per-session>",
        "user_id":"<uuid or null>",
        "listing_id":"<uuid or null>",
        "order_id":"<uuid or null>",
        "chat_id":"<uuid or null>",
        "step":"<optional>",
        "properties":{"button":"buy"},
        "occurred_at":"2025-10-09T23:57:37Z"  // optional; server assumes now (UTC)
      }
    ]
  }
  ```

  **Taxonomy**

  * `ui.click` → `properties.button`
  * `feature.used` → `properties.feature_key` (e.g., `"quick_view"`)
  * `escrow.step` → `step` and `properties.result` (e.g., `"cancelled"` / `"ok"`)

* `POST /v1/features/use` → `{ "feature_key":"quick_view", "action":"open" }`

#### Analytics (BQ)

All support **optional** query params: `start=<ISO8601 UTC>` and `end=<ISO8601 UTC>`.
If omitted, the server uses a sensible default window.

* **BQ 1.1** `GET /v1/analytics/bq/1_1` — *Listings per day by category*
  Response: `[{ day, category_id, count }]`

* **BQ 1.2** `GET /v1/analytics/bq/1_2` — *Escrow cancel rate by step*
  Response: `[{ step, total, cancelled, pct_cancelled }]`

* **BQ 2.1** `GET /v1/analytics/bq/2_1` — *Events per day by type*
  Response: `[{ day, event_type, count }]`

* **BQ 2.2** `GET /v1/analytics/bq/2_2` — *Clicks per day by button* (`ui.click`)
  Response: `[{ day, button, count }]`

* **BQ 3.1** `GET /v1/analytics/bq/3_1` — *DAU (unique users/day)* — requires `user_id` in events
  Response: `[{ day, dau }]`

* **BQ 3.2** `GET /v1/analytics/bq/3_2` — *Unique sessions/day* — requires `session_id` in events
  Response: `[{ day, sessions }]`

* **BQ 4.1** `GET /v1/analytics/bq/4_1` — *Orders per day by status*
  Response: `[{ day, status, count }]`

* **BQ 4.2** `GET /v1/analytics/bq/4_2` — *GMV and paid orders per day*
  Response: `[{ day, gmv_cents, orders_paid }]`

* **BQ 5.1** `GET /v1/analytics/bq/5_1` — *Quick View usage per day by category* (joins `feature.used` with listings)
  Response: `[{ day, category_id, count }]`

  > **Note:** `category_id` is returned as a **string** (server casts in SQL).

### Devices / Contacts / Sync

* `POST /v1/devices` → `{platform:"android|ios", push_token, app_version}`
* `POST /v1/contacts/match` → `{email_hashes:[sha256_hex,...]}` (no raw emails)
* `GET /v1/sync/delta?since=<ISO8601 UTC>` → changes since `since` (for offline cache)

---

## Flutter App Integration

### 1) Auth & Session

* Store `access_token` and `refresh_token` in **Secure Storage** (e.g., `flutter_secure_storage`).
* Add `Authorization: Bearer <access_token>` to every request.
* On **401**:

  1. Call `POST /v1/auth/refresh` with `refresh_token`.
  2. Retry the original request with the new `access_token`.
  3. If it fails again, force re-login.
* Keep a **stable per-session** `session_id` (UUID v4) in memory and include it in **all** `POST /v1/events`. Generate a new one when the app restarts.

### 2) Image Uploads (camera/gallery)

1. `POST /v1/images/presign` with `{filename, content_type, scope:"listing", listing_id}` → `{upload_url, object_key}`
2. **PUT** binary to `upload_url` with the exact `Content-Type` (no extra headers).

   ```dart
   final put = await http.put(
     Uri.parse(uploadUrl),
     headers: {'Content-Type': contentType},
     body: fileBytes,
   );
   ```
3. `POST /v1/images/confirm` with `{scope:"listing", listing_id, object_key, width, height}`
4. Use the returned `preview_url` in the UI.

### 3) Geolocation (GPS)

* Request runtime permissions.
* When creating a listing, you may send `latitude` / `longitude`.
* To search nearby:

  ```
  GET /v1/listings?near_lat=<lat>&near_lon=<lon>&radius_km=<r>&page_size=...
  ```
* Send coordinates in **WGS84 decimal degrees**. Backend uses **PostGIS** for radius filtering.

### 4) Telemetry

* Always send `session_id`.
* Include `user_id` when the user is logged in.
* Recommended events from the app:

  * `ui.click` → `properties.button` (e.g., `"buy"`, `"details"`)
  * `feature.used` → `properties.feature_key` (e.g., `"quick_view"`)
* Use `occurred_at` in UTC ISO 8601 (`Z`) for past events; otherwise omit (server sets now).

  ```dart
  await dio.post('/v1/events', data: {
    'events': [
      {
        'event_type': 'ui.click',
        'session_id': sessionId,
        'user_id': userId, // or null
        'properties': {'button': 'buy'},
        'occurred_at': DateTime.now().toUtc().toIso8601String(),
      },
      {
        'event_type': 'feature.used',
        'session_id': sessionId,
        'user_id': userId,
        'properties': {'feature_key': 'quick_view'},
      }
    ]
  });
  ```
* **DAU (BQ 3.1)** depends on sending `user_id`.
* **Sessions (BQ 3.2)** depend on sending `session_id`.

### 5) Orders & Payments (concurrency / eventual consistency)

* `POST /v1/orders` creates the order (`status: "created"`).
* `POST /v1/orders/{id}/pay` returns **202 Accepted**: processing is **async** (worker).
  Show “Processing payment …”; **don’t** block the UI.
* To reflect state changes (`paid` / `completed`), avoid tight polling:

  * Use **`GET /v1/sync/delta?since=...`** periodically (e.g., on app foreground, pull-to-refresh, or every 30–60s on an active screen).
  * Optionally, push notifications (FCM) after registering the device via `POST /v1/devices`.
* If capturing payment manually:

  * `POST /v1/payments/capture` → `{order_id, provider_ref}`.
    The result may be async depending on the provider; re-sync with **delta**.

### 6) Cache & Local Storage (offline-first)

* Use SQLite/Isar/Hive to persist:

  * catalogs `categories`, `brands`
  * `listings` (last query/page)
  * `orders`, `chats`, `messages`
  * `last_delta_since` (timestamp of last sync)
* **Incremental sync** via `/v1/sync/delta?since=<ISO UTC>`:

  * On app start, if you have `last_since`, call delta.
  * First run: omit `since` or choose a sensible lookback (e.g., now-1h).
  * The server returns per-entity “changes”; apply **upserts** and handle deletes as indicated.
* **Offline event queue**:

  * Queue `POST /v1/events` when offline and retry on reconnect.
  * Aggregations tolerate duplicates; implement backoff & retry caps.

### 7) Search & Performance (hot cache)

* Cache the last paginated `listings` and per-`id` details in memory.
* Debounce query `q=` changes before firing network requests.
* Compose filter params (price/geo) before issuing a single request.

### 8) Security

* Store tokens in **Secure Storage**.
* Never send raw contacts: compute **SHA-256** of emails client-side and send hashes to `/v1/contacts/match`.
* Sanitize filenames before `presign`.

---

## Concurrency Rules (backend)

* **Workers & Beat** do async work (thumbnails, escrow steps, cleanup, etc.).
  The API may return 200/202 while state transitions finalize later.
* **Consistent reads**: rely on **delta sync** to observe the latest state.
* **Idempotency**: telemetry tolerates duplicates; in the UI, disable repeated order actions while a step is in flight.

---

## Troubleshooting

* **401 / “Invalid or expired token”** — refresh token or re-login; check `JWT_SECRET`.
* **PostGIS** — confirm logs show “DB extensions ensured (postgis, pgcrypto, citext)”.
* **Image uploads** — respect the exact `Content-Type`; ensure MinIO is healthy.
* **Port conflicts** — change `API_PORT` in `.env` or compose.

---

## Recent Important Changes

* Implemented **BQ 2.x, 3.x, 4.x, 5.x**:

  * `GET /v1/analytics/bq/2_1`, `2_2`, `3_1`, `3_2`, `4_1`, `4_2`, `5_1` (support `start`/`end`).
* **BQ 5.1 fix**: `category_id` now returned as a **string** (server-side SQL cast) to avoid UUID vs string validation errors.
* **Event ingestion**: accepts ISO 8601 `occurred_at` with `Z`; if omitted, server sets UTC `now`.

---

## Code Snippets (Flutter)

**Auth interceptor (Dio)**

```dart
class AuthInterceptor extends Interceptor {
  final TokenStore store;
  AuthInterceptor(this.store);

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) async {
    final token = await store.accessToken;
    if (token != null) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) async {
    if (err.response?.statusCode == 401) {
      final ok = await store.tryRefresh(); // calls /auth/refresh inside
      if (ok) {
        final req = await _retry(err.requestOptions);
        return handler.resolve(req);
      }
    }
    handler.next(err);
  }

  Future<Response<dynamic>> _retry(RequestOptions r) {
    final dio = Dio()..interceptors.add(this);
    return dio.fetch(r..headers['Authorization'] = 'Bearer ${store.accessTokenSync}');
  }
}
```

**Presigned PUT**

```dart
final presign = await dio.post('/v1/images/presign', data: {
  'filename': fileName,
  'content_type': mime,
  'scope': 'listing',
  'listing_id': listingId,
});
final uploadUrl = presign.data['upload_url'];
final objectKey = presign.data['object_key'];

// PUT binary
await Dio(BaseOptions(headers: {'Content-Type': mime}))
    .putUri(Uri.parse(uploadUrl), data: await file.readAsBytes());

// Confirm
await dio.post('/v1/images/confirm', data: {
  'scope': 'listing',
  'listing_id': listingId,
  'object_key': objectKey,
  'width': meta.width,
  'height': meta.height,
});
```

**Telemetry batch**

```dart
await dio.post('/v1/events', data: {
  'events': [
    {
      'event_type': 'ui.click',
      'session_id': sessionId,
      'user_id': userId, // or null
      'properties': {'button': 'buy'},
      'occurred_at': DateTime.now().toUtc().toIso8601String(),
    },
    {
      'event_type': 'feature.used',
      'session_id': sessionId,
      'user_id': userId,
      'properties': {'feature_key': 'quick_view'},
    }
  ]
});
```

**Geo search**

```dart
final res = await dio.get('/v1/listings', queryParameters: {
  'near_lat': lat,
  'near_lon': lon,
  'radius_km': 3,
  'page_size': 20,
});
```

**Delta sync**

```dart
final since = await localStore.lastSinceIso; // may be null on first run
final res = await dio.get('/v1/sync/delta', queryParameters: {
  if (since != null) 'since': since,
});
await localStore.applyDelta(res.data); // upserts + deletes
await localStore.setLastSinceIso(DateTime.now().toUtc().toIso8601String());
```
