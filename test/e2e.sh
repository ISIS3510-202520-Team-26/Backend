# `tests/e2e.sh` (Bash)

```bash
#!/usr/bin/env bash
set -euo pipefail

BASE_DEFAULT="http://localhost:8000/v1"
BASE="${BASE:-$BASE_DEFAULT}"
PASS="${PASS:-Passw0rd}"

say() { printf "\n\033[1;34m▶ %s\033[0m\n" "$*"; }
fail() { printf "\n\033[1;31m✗ %s\033[0m\n" "$*"; exit 1; }

jget() { jq -r "$1" 2>/dev/null || true; }

api() {
  local method="$1"; shift
  curl -sS -w "\n%{http_code}" -X "$method" "$@" \
    -H "Accept: application/json"
}

apijson() {
  local method="$1"; local url="$2"; local data="$3"; shift 3
  curl -sS -w "\n%{http_code}" -X "$method" "$url" \
    -H "Content-Type: application/json" -H "Accept: application/json" \
    -d "$data" "$@"
}

# 0) Health
say "Healthcheck"
curl -sS http://localhost:8000/health || true

# 1) Register/Login
EMAIL="${EMAIL:-demo+$(date +%s)@uniandes.edu.co}"

say "Register user: $EMAIL"
R=$(apijson POST "$BASE/auth/register" "$(jq -n --arg name "Demo" --arg email "$EMAIL" --arg pass "$PASS" '{name:$name,email:$email,password:$pass}')" )
BODY=$(echo "$R" | sed -n '$!p'); CODE=$(echo "$R" | tail -n1)
echo "HTTP $CODE"; echo "$BODY" | jq . 2>/dev/null || true
[[ "$CODE" == "201" || "$CODE" == "400" ]] || fail "register falló"

say "Login user: $EMAIL"
R=$(apijson POST "$BASE/auth/login" "$(jq -n --arg email "$EMAIL" --arg pass "$PASS" '{email:$email,password:$pass}')" )
BODY=$(echo "$R" | sed -n '$!p'); CODE=$(echo "$R" | tail -n1)
echo "HTTP $CODE"; echo "$BODY" | jq .
[[ "$CODE" == "200" ]] || fail "login falló"
TOKEN=$(echo "$BODY" | jget '.access_token')
REFRESH=$(echo "$BODY" | jget '.refresh_token')
AUTH_H="Authorization: Bearer $TOKEN"

say "/auth/me"
R=$(api GET "$BASE/auth/me" -H "$AUTH_H"); BODY=$(echo "$R" | sed -n '$!p'); CODE=$(echo "$R" | tail -n1)
echo "HTTP $CODE"; echo "$BODY" | jq .

# 2) Catálogos
say "GET /categories"
R=$(api GET "$BASE/categories" -H "$AUTH_H"); CATS=$(echo "$R" | sed -n '$!p'); CODE=$(echo "$R" | tail -n1)
echo "HTTP $CODE"; echo "$CATS" | jq '((.items? // .) | map({slug,id}) )'
CAT_LAPTOPS=$(echo "$CATS" | jget '((.items? // .)[] | select(.slug=="laptops") | .id)')

say "GET /brands"
R=$(api GET "$BASE/brands" -H "$AUTH_H"); BRAS=$(echo "$R" | sed -n '$!p'); CODE=$(echo "$R" | tail -n1)
echo "HTTP $CODE"; echo "$BRAS" | jq '((.items? // .) | map({slug,id}) )'
BR_LENOVO=$(echo "$BRAS" | jget '((.items? // .)[] | select(.slug=="lenovo") | .id)')

# 3) Listing
say "POST /listings"
PAYLOAD=$(jq -n --arg title "Laptop Demo i5 8GB" \
  --arg desc "Equipo de prueba" \
  --arg cat "$CAT_LAPTOPS" \
  --arg brand "$BR_LENOVO" \
  '{
    title:$title,
    description:$desc,
    category_id:$cat,
    brand_id:$brand,
    price_cents:1200000,
    currency:"COP",
    condition:"used",
    quantity:1,
    latitude:4.601,
    longitude:-74.066,
    price_suggestion_used:true,
    quick_view_enabled:true
  }')
R=$(apijson POST "$BASE/listings" "$PAYLOAD" -H "$AUTH_H")
BODY=$(echo "$R" | sed -n '$!p'); CODE=$(echo "$R" | tail -n1)
echo "HTTP $CODE"; echo "$BODY" | jq .
L_ID=$(echo "$BODY" | jget '.id')

say "GET /listings/{id}"
R=$(api GET "$BASE/listings/$L_ID" -H "$AUTH_H"); echo "$R" | sed -n '$!p' | jq .; echo "HTTP $(echo "$R" | tail -n1)"

say "GET /listings (geo)"
R=$(api GET "$BASE/listings?near_lat=4.601&near_lon=-74.066&radius_km=5&page_size=5" -H "$AUTH_H")
echo "$R" | sed -n '$!p' | jq '((.items? // .) | map({id,title,created_at}))'; echo "HTTP $(echo "$R" | tail -n1)"

# 4) Imágenes
say "POST /images/presign"
UP_FN="foto_demo.jpg"
PAYLOAD=$(jq -n --arg name "$UP_FN" --arg ctype "image/jpeg" --arg listing "$L_ID" '{filename:$name, content_type:$ctype, scope:"listing", listing_id:$listing}')
R=$(apijson POST "$BASE/images/presign" "$PAYLOAD" -H "$AUTH_H")
PRE=$(echo "$R" | sed -n '$!p'); CODE=$(echo "$R" | tail -n1)
echo "HTTP $CODE"; echo "$PRE" | jq .
STORAGE_KEY=$(echo "$PRE" | jget '.storage_key // .fields.key // .key')

URL=$(echo "$PRE" | jget '.url // empty')
if [[ -n "$URL" ]]; then
  say "Subida presignada a S3/MinIO (si aplica)"
  if command -v dd >/dev/null; then
    dd if=/dev/urandom of=/tmp/$UP_FN bs=1024 count=5 status=none
  else
    echo "fake" > /tmp/$UP_FN
  fi
  FIELDS=$(echo "$PRE" | jget '.fields // empty')
  if [[ -n "$FIELDS" && "$FIELDS" != "null" ]]; then
    # Construye -F k=v
    FORM_OPTS=()
    while IFS="=" read -r k v; do
      [[ -z "$k" || -z "$v" ]] && continue
      FORM_OPTS+=(-F "$k=$v")
    done < <(echo "$FIELDS" | jq -r 'to_entries[] | "\(.key)=\(.value)"')
    curl -sS -X POST "$URL" "${FORM_OPTS[@]}" -F "file=@/tmp/$UP_FN" >/dev/null
  fi
fi

say "POST /images/confirm"
PAYLOAD=$(jq -n --arg listing "$L_ID" --arg sk "${STORAGE_KEY:-testing/$UP_FN}" '{scope:"listing", listing_id:$listing, storage_key:$sk, width:800, height:600}')
R=$(apijson POST "$BASE/images/confirm" "$PAYLOAD" -H "$AUTH_H")
echo "$R" | sed -n '$!p' | jq .; echo "HTTP $(echo "$R" | tail -n1)"

# 5) Chat/Mensajes
say "POST /chats"
R=$(apijson POST "$BASE/chats" "$(jq -n --arg l "$L_ID" '{listing_id:$l}')" -H "$AUTH_H")
BODY=$(echo "$R" | sed -n '$!p'); echo "$BODY" | jq .; echo "HTTP $(echo "$R" | tail -n1)"
CHAT_ID=$(echo "$BODY" | jget '.id')

say "POST /messages"
R=$(apijson POST "$BASE/messages" "$(jq -n --arg c "$CHAT_ID" --arg txt "Hola, ¿sigue disponible?" '{chat_id:$c, message_type:"text", content:$txt}')" -H "$AUTH_H")
echo "$R" | sed -n '$!p' | jq .; echo "HTTP $(echo "$R" | tail -n1)"

# 6) Orders/Pagos/Escrow/Review
say "POST /orders"
R=$(apijson POST "$BASE/orders" "$(jq -n --arg l "$L_ID" '{listing_id:$l, quantity:1}')" -H "$AUTH_H")
BODY=$(echo "$R" | sed -n '$!p'); echo "$BODY" | jq .; echo "HTTP $(echo "$R" | tail -n1)"
ORDER_ID=$(echo "$BODY" | jget '.id')

say "POST /orders/{id}/pay"
R=$(api POST "$BASE/orders/$ORDER_ID/pay" -H "$AUTH_H"); echo "$R" | sed -n '$!p' | jq .; echo "HTTP $(echo "$R" | tail -n1)"

say "POST /payments/capture"
R=$(apijson POST "$BASE/payments/capture" "$(jq -n --arg o "$ORDER_ID" '{order_id:$o}')" -H "$AUTH_H")
echo "$R" | sed -n '$!p' | jq .; echo "HTTP $(echo "$R" | tail -n1)"

say "POST /escrow/step"
R=$(apijson POST "$BASE/escrow/step" "$(jq -n --arg o "$ORDER_ID" --arg step "payment_made" '{order_id:$o, step:$step}')" -H "$AUTH_H")
echo "$R" | sed -n '$!p' | jq .; echo "HTTP $(echo "$R" | tail -n1)"

say "POST /orders/{id}/complete"
R=$(api POST "$BASE/orders/$ORDER_ID/complete" -H "$AUTH_H"); echo "$R" | sed -n '$!p' | jq .; echo "HTTP $(echo "$R" | tail -n1)"

say "POST /reviews/orders/{id}"
R=$(apijson POST "$BASE/reviews/orders/$ORDER_ID" '{"rating":5,"comment":"Todo perfecto"}' -H "$AUTH_H")
echo "$R" | sed -n '$!p' | jq .; echo "HTTP $(echo "$R" | tail -n1)"

# 7) Features / Analytics / Events
say "POST /features/use"
R=$(apijson POST "$BASE/features/use" '{"key":"quick_view","action":"open"}' -H "$AUTH_H")
echo "$R" | sed -n '$!p' | jq .; echo "HTTP $(echo "$R" | tail -n1)"

FROM=$(date -u -d '7 days ago' +%Y-%m-%dT00:00:00Z 2>/dev/null || date -u -v-7d +%Y-%m-%dT00:00:00Z)
TO=$(date -u +%Y-%m-%dT23:59:59Z)

say "GET /analytics/bq/1_1"
R=$(api GET "$BASE/analytics/bq/1_1?from=$FROM&to=$TO" -H "$AUTH_H")
echo "$R" | sed -n '$!p' | jq .; echo "HTTP $(echo "$R" | tail -n1)"

say "GET /analytics/bq/1_2"
R=$(api GET "$BASE/analytics/bq/1_2?from=$FROM&to=$TO" -H "$AUTH_H")
echo "$R" | sed -n '$!p' | jq .; echo "HTTP $(echo "$R" | tail -n1)"

say "POST /events"
R=$(apijson POST "$BASE/events" '{"event_type":"ui.click","session_id":"dev-sess","properties":{"button":"buy"}}' -H "$AUTH_H")
echo "$R" | sed -n '$!p' | jq .; echo "HTTP $(echo "$R" | tail -n1)"

# 8) Devices / Contacts / Sync
say "POST /devices"
R=$(apijson POST "$BASE/devices" '{"platform":"android","push_token":"TEST_PUSH","app_version":"1.0.0"}' -H "$AUTH_H")
echo "$R" | sed -n '$!p' | jq .; echo "HTTP $(echo "$R" | tail -n1)"

say "POST /contacts/match"
H=$(printf 'demo@uniandes.edu.co' | openssl dgst -sha256 -binary | xxd -p -c 256)
R=$(apijson POST "$BASE/contacts/match" "$(jq -n --arg h "$H" '{email_hashes:[$h]}')" -H "$AUTH_H")
echo "$R" | sed -n '$!p' | jq .; echo "HTTP $(echo "$R" | tail -n1)"

say "GET /sync/delta"
SINCE=$(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u -v-1H +%Y-%m-%dT%H:%M:%SZ)
R=$(api GET "$BASE/sync/delta?since=$SINCE" -H "$AUTH_H")
echo "$R" | sed -n '$!p' | jq '. | {since:"'"$SINCE"'", keys:(keys)}'; echo "HTTP $(echo "$R" | tail -n1)"

say "OK ✅"