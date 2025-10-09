#!/usr/bin/env zsh
set -e
set -u
set -o pipefail

# ---------------- Utils fecha cross-platform (GNU/BSD) ----------------
iso_days_ago_start() {
  date -u -d "$1 days ago" +%Y-%m-%dT00:00:00Z 2>/dev/null || date -u -v-"$1"d +%Y-%m-%dT00:00:00Z
}
iso_hours_ago() {
  date -u -d "$1 hour ago" +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u -v-"$1"H +%Y-%m-%dT%H:%M:%SZ
}

# ---------------- Config ----------------
BASE_DEFAULT="http://localhost:8000/v1"
: "${BASE:=$BASE_DEFAULT}"
: "${PASS:=Passw0rd}"
: "${PASS_BUYER:=$PASS}"
: "${PASS_SELLER:=$PASS}"
: "${DOMAIN:=uniandes.edu.co}"   # para /contacts/match

say() { print -P "\n%F{blue}%B▶ $*%b%f"; }
warn() { print -P "\n%F{yellow}%B! $*%b%f"; }
fail() { print -P "\n%F{red}%B✗ $*%b%f"; exit 1; }
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

# ---------------- 0) Health ----------------
say "Healthcheck"
curl -sS http://localhost:8000/health || true

# ---------------- 1) SELLER ----------------
EMAIL_SELLER="${EMAIL_SELLER:-seller+$(date +%s)@${DOMAIN}}"

say "Register SELLER: $EMAIL_SELLER"
R=$(apijson POST "$BASE/auth/register" "$(jq -n --arg name "Seller" --arg email "$EMAIL_SELLER" --arg pass "$PASS_SELLER" '{name:$name,email:$email,password:$pass}')" )
BODY=$(echo "$R" | sed -n '$!p'); CODE=$(echo "$R" | tail -n1)
echo "HTTP $CODE"; echo "$BODY" | jq . 2>/dev/null || true
[[ "$CODE" == "201" || "$CODE" == "400" ]] || fail "register SELLER falló"

say "Login SELLER: $EMAIL_SELLER"
R=$(apijson POST "$BASE/auth/login" "$(jq -n --arg email "$EMAIL_SELLER" --arg pass "$PASS_SELLER" '{email:$email,password:$pass}')" )
BODY=$(echo "$R" | sed -n '$!p'); CODE=$(echo "$R" | tail -n1)
echo "HTTP $CODE"; echo "$BODY" | jq .
[[ "$CODE" == "200" ]] || fail "login SELLER falló"
TOKEN_SELLER=$(echo "$BODY" | jget '.access_token')
AUTH_H_SELLER="Authorization: Bearer $TOKEN_SELLER"

say "GET /auth/me (SELLER)"
R=$(api GET "$BASE/auth/me" -H "$AUTH_H_SELLER")
echo "$R" | sed -n '$!p' | jq .; echo "HTTP $(echo "$R" | tail -n1)"

# ---------------- 2) BUYER ----------------
EMAIL_BUYER="${EMAIL_BUYER:-buyer+$(date +%s)@${DOMAIN}}"

say "Register BUYER: $EMAIL_BUYER"
R=$(apijson POST "$BASE/auth/register" "$(jq -n --arg name "Buyer" --arg email "$EMAIL_BUYER" --arg pass "$PASS_BUYER" '{name:$name,email:$email,password:$pass}')" )
BODY=$(echo "$R" | sed -n '$!p'); CODE=$(echo "$R" | tail -n1)
echo "HTTP $CODE"; echo "$BODY" | jq . 2>/dev/null || true
[[ "$CODE" == "201" || "$CODE" == "400" ]] || fail "register BUYER falló"

say "Login BUYER: $EMAIL_BUYER"
R=$(apijson POST "$BASE/auth/login" "$(jq -n --arg email "$EMAIL_BUYER" --arg pass "$PASS_BUYER" '{email:$email,password:$pass}')" )
BODY=$(echo "$R" | sed -n '$!p'); CODE=$(echo "$R" | tail -n1)
echo "HTTP $CODE"; echo "$BODY" | jq .
[[ "$CODE" == "200" ]] || fail "login BUYER falló"
TOKEN_BUYER=$(echo "$BODY" | jget '.access_token')
AUTH_H_BUYER="Authorization: Bearer $TOKEN_BUYER"

say "GET /auth/me (BUYER)"
R=$(api GET "$BASE/auth/me" -H "$AUTH_H_BUYER")
echo "$R" | sed -n '$!p' | jq .; echo "HTTP $(echo "$R" | tail -n1)"

# ---------------- 3) Catálogos ----------------
say "GET /categories"
R=$(api GET "$BASE/categories" -H "$AUTH_H_SELLER")
CATS=$(echo "$R" | sed -n '$!p'); CODE=$(echo "$R" | tail -n1)
echo "HTTP $CODE"; echo "$CATS" | jq '((.items? // .) | map({slug,id}) )'
CAT_LAPTOPS=$(echo "$CATS" | jget '((.items? // .)[] | select(.slug=="laptops") | .id)')

say "GET /brands"
R=$(api GET "$BASE/brands" -H "$AUTH_H_SELLER")
BRAS=$(echo "$R" | sed -n '$!p'); CODE=$(echo "$R" | tail -n1)
echo "HTTP $CODE"; echo "$BRAS" | jq '((.items? // .) | map({slug,id}) )'
BR_LENOVO=$(echo "$BRAS" | jget '((.items? // .)[] | select(.slug=="lenovo") | .id)')

# ---------------- 4) Listing (SELLER) ----------------
say "POST /listings (SELLER)"
PAYLOAD=$(jq -n --arg title "Laptop Demo i5 8GB" \
  --arg desc "Equipo de prueba" \
  --arg cat "$CAT_LAPTOPS" \
  --arg brand "$BR_LENOVO" \
  '{
    title:$title, description:$desc, category_id:$cat, brand_id:$brand,
    price_cents:1200000, currency:"COP", condition:"used", quantity:1,
    price_suggestion_used:true, quick_view_enabled:true
  }')
R=$(apijson POST "$BASE/listings" "$PAYLOAD" -H "$AUTH_H_SELLER")
BODY=$(echo "$R" | sed -n '$!p'); CODE=$(echo "$R" | tail -n1)
echo "HTTP $CODE"; echo "$BODY" | jq .
[[ "$CODE" == "201" ]] || fail "crear listing falló"
L_ID=$(echo "$BODY" | jget '.id')
SELLER_ID=$(echo "$BODY" | jget '.seller_id')   # <-- NUEVO: lo usaremos para reviews

say "GET /listings/{id} (SELLER)"
R=$(api GET "$BASE/listings/$L_ID" -H "$AUTH_H_SELLER")
echo "$R" | sed -n '$!p' | jq .; echo "HTTP $(echo "$R" | tail -n1)"

say "GET /listings (geo)"
R=$(api GET "$BASE/listings?near_lat=4.601&near_lon=-74.066&radius_km=5&page_size=5" -H "$AUTH_H_BUYER")
echo "$R" | sed -n '$!p' | jq '((.items? // .) | map({id,title,created_at}))'; echo "HTTP $(echo "$R" | tail -n1)"

# ---------------- 5) Imágenes (PUT presign + confirm) ----------------
say "POST /images/presign (SELLER)"
UP_FN="foto_demo.jpg"
PAYLOAD=$(jq -n --arg name "$UP_FN" --arg ctype "image/jpeg" --arg listing "$L_ID" \
  '{filename:$name, content_type:$ctype, scope:"listing", listing_id:$listing}')
R=$(apijson POST "$BASE/images/presign" "$PAYLOAD" -H "$AUTH_H_SELLER")
PRE=$(echo "$R" | sed -n '$!p'); CODE=$(echo "$R" | tail -n1)
echo "HTTP $CODE"; echo "$PRE" | jq .
[[ "$CODE" == "201" ]] || fail "presign falló"
UPLOAD_URL=$(echo "$PRE" | jget '.upload_url // .url')
OBJECT_KEY=$(echo "$PRE" | jget '.object_key // .storage_key // .fields.key // .key')

say "Subida presignada tipo PUT"
if command -v dd >/dev/null; then
  dd if=/dev/urandom of=/tmp/$UP_FN bs=1024 count=5 status=none
else
  echo "fake" > /tmp/$UP_FN
fi
typeset -a RESOLVE_OPTS
RESOLVE_OPTS=(--resolve minio:9000:127.0.0.1)
curl -sS "${RESOLVE_OPTS[@]}" \
  -X PUT -H "Content-Type: image/jpeg" \
  --data-binary "@/tmp/$UP_FN" \
  "$UPLOAD_URL" >/dev/null

say "POST /images/confirm"
PAYLOAD=$(jq -n --arg listing "$L_ID" --arg sk "$OBJECT_KEY" \
  '{scope:"listing", listing_id:$listing, object_key:$sk, width:800, height:600}')
R=$(apijson POST "$BASE/images/confirm" "$PAYLOAD" -H "$AUTH_H_SELLER")
echo "$R" | sed -n '$!p' | jq .; echo "HTTP $(echo "$R" | tail -n1)"

# ---------------- 6) Chat/Mensajes (BUYER) ----------------
say "POST /chats (BUYER abre chat con listing del SELLER)"
R=$(apijson POST "$BASE/chats" "$(jq -n --arg l "$L_ID" '{listing_id:$l}')" -H "$AUTH_H_BUYER")
BODY=$(echo "$R" | sed -n '$!p'); echo "$BODY" | jq .; echo "HTTP $(echo "$R" | tail -n1)"
CHAT_ID=$(echo "$BODY" | jget '.id')

say "POST /messages (BUYER)"
R=$(apijson POST "$BASE/messages" "$(jq -n --arg c "$CHAT_ID" --arg txt "Hola, ¿sigue disponible?" '{chat_id:$c, message_type:"text", content:$txt}')" -H "$AUTH_H_BUYER")
echo "$R" | sed -n '$!p' | jq .; echo "HTTP $(echo "$R" | tail -n1)"

# ---------------- 7) Orders / Payments / Escrow / Review ----------------
say "POST /orders"
ORDER_PAYLOAD=$(jq -n --arg l "$L_ID" --argjson qty 1 '{listing_id:$l, quantity:$qty}')
echo "Order payload:"; echo "$ORDER_PAYLOAD" | jq .
R=$(apijson POST "$BASE/orders" "$ORDER_PAYLOAD" -H "$AUTH_H_BUYER")
BODY=$(echo "$R" | sed -n '$!p'); echo "$BODY" | jq .; echo "HTTP $(echo "$R" | tail -n1)"
[[ "$(echo "$R" | tail -n1)" == "201" ]] || fail "crear orden falló"
ORDER_ID=$(echo "$BODY" | jget '.id')

say "POST /orders/{id}/pay"
R=$(api POST "$BASE/orders/$ORDER_ID/pay" -H "$AUTH_H_BUYER")
BODY=$(echo "$R" | sed -n '$!p'); echo "$BODY" | jq .; echo "HTTP $(echo "$R" | tail -n1)"
ESCROW_ID="${ESCROW_ID:-$(echo "$BODY" | jq -r '(.escrow_id // .escrow.id // .escrowId // empty)')}"

# Normaliza: considera "null" o valores no UUID como no encontrado
if [[ -z "$ESCROW_ID" || "$ESCROW_ID" == "null" || ! "$ESCROW_ID" =~ ^[0-9a-fA-F-]{36}$ ]]; then
  say "POST /escrow/step"
  echo -e "\n! No se encontró escrow_id — se omite /escrow/step"
else
  say "POST /escrow/step"
  ESCROW_STEP_PAYLOAD=$(jq -n \
    --arg e "$ESCROW_ID" \
    --arg o "$ORDER_ID" \
    --arg step "payment_made" \
    --arg result "ok" \
    '{escrow_id:$e, order_id:$o, step:$step, result:$result}')
  R=$(apijson POST "$BASE/escrow/step" "$ESCROW_STEP_PAYLOAD" -H "$AUTH_H_BUYER")
  echo "$R" | sed -n '$!p' | jq .; echo "HTTP $(echo "$R" | tail -n1)"
fi

say "POST /payments/capture"
CAP_REF="TESTPROV-${ORDER_ID:0:8}"
CAPTURE_PAYLOAD=$(jq -n --arg o "$ORDER_ID" --arg p "$CAP_REF" \
  '{order_id:$o, provider_ref:$p}')
R=$(apijson POST "$BASE/payments/capture" "$CAPTURE_PAYLOAD" -H "$AUTH_H_BUYER")
echo "$R" | sed -n '$!p' | jq .; echo "HTTP $(echo "$R" | tail -n1)"


# Extra: inyectar un evento escrow.step de demo para analytics bq/1_2
say "POST /events (escrow.step demo)"
NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ)
EV=$(jq -n --arg now "$NOW" --arg o "$ORDER_ID" \
  '{events:[{event_type:"escrow.step", session_id:"dev-sess", order_id:$o, step:"payment_made", properties:{result:"ok"}, occurred_at:$now}]}')
R=$(apijson POST "$BASE/events" "$EV" -H "$AUTH_H_BUYER")
echo "$R" | sed -n '$!p' | jq .; echo "HTTP $(echo "$R" | tail -n1)"

say "POST /orders/{id}/complete"
R=$(api POST "$BASE/orders/$ORDER_ID/complete" -H "$AUTH_H_BUYER")
BODY=$(echo "$R" | sed -n '$!p'); echo "$BODY" | jq .; echo "HTTP $(echo "$R" | tail -n1)"

# Reviews: intentar endpoint por orden; si 404/405, fallback a /reviews con ratee_id (seller)
say "POST /reviews/orders/{id} (fallback a POST /reviews si 405/404)"
R=$(apijson POST "$BASE/reviews/orders/$ORDER_ID" \
  "$(jq -n --argjson rating 5 --arg comment "Todo perfecto" '{rating:$rating, comment:$comment}')" \
  -H "$AUTH_H_BUYER")
BODY=$(echo "$R" | sed -n '$!p'); CODE=$(echo "$R" | tail -n1)

if [[ "$CODE" == "405" || "$CODE" == "404" ]]; then
  PAYLOAD_REVIEW=$(jq -n \
    --arg o "$ORDER_ID" \
    --arg rid "$SELLER_ID" \
    --argjson rating 5 \
    --arg comment "Todo perfecto" \
    '{order_id:$o, ratee_id:$rid, rating:$rating, comment:$comment}')
  R=$(apijson POST "$BASE/reviews" "$PAYLOAD_REVIEW" -H "$AUTH_H_BUYER")
  BODY=$(echo "$R" | sed -n '$!p'); CODE=$(echo "$R" | tail -n1)
fi

echo "$BODY" | jq . 2>/dev/null || true; echo "HTTP $CODE"

# ---------------- 8) Features / Analytics / Events ----------------
say "POST /features/use"
R=$(apijson POST "$BASE/features/use" '{"feature_key":"quick_view","action":"open"}' -H "$AUTH_H_BUYER")
echo "$R" | sed -n '$!p' | jq . 2>/dev/null || true; echo "HTTP $(echo "$R" | tail -n1)"

FROM=$(iso_days_ago_start 7)
TO=$(date -u +%Y-%m-%dT23:59:59Z)

say "GET /analytics/bq/1_1"
R=$(api GET "$BASE/analytics/bq/1_1?start=$FROM&end=$TO" -H "$AUTH_H_BUYER")
echo "$R" | sed -n '$!p' | jq . 2>/dev/null || true; echo "HTTP $(echo "$R" | tail -n1)"

say "GET /analytics/bq/1_2"
R=$(api GET "$BASE/analytics/bq/1_2?start=$FROM&end=$TO" -H "$AUTH_H_BUYER")
echo "$R" | sed -n '$!p' | jq . 2>/dev/null || true; echo "HTTP $(echo "$R" | tail -n1)"

say "POST /events (array)"
R=$(apijson POST "$BASE/events" '{"events":[{"event_type":"ui.click","session_id":"dev-sess","properties":{"button":"buy"}}]}' -H "$AUTH_H_BUYER")
echo "$R" | sed -n '$!p' | jq . 2>/dev/null || true; echo "HTTP $(echo "$R" | tail -n1)"

# ---------------- 9) Devices / Contacts / Sync ----------------
say "POST /devices"
R=$(apijson POST "$BASE/devices" '{"platform":"android","push_token":"TEST_PUSH","app_version":"1.0.0"}' -H "$AUTH_H_BUYER")
echo "$R" | sed -n '$!p' | jq . 2>/dev/null || true; echo "HTTP $(echo "$R" | tail -n1)"

say "POST /contacts/match"
H=$(printf 'demo@%s' "$DOMAIN" | openssl dgst -sha256 -binary | xxd -p -c 256)
R=$(apijson POST "$BASE/contacts/match" "$(jq -n --arg h "$H" '{email_hashes:[$h]}')" -H "$AUTH_H_BUYER")
echo "$R" | sed -n '$!p' | jq . 2>/dev/null || true; echo "HTTP $(echo "$R" | tail -n1)"

say "GET /sync/delta"
SINCE=$(iso_hours_ago 1)
R=$(api GET "$BASE/sync/delta?since=$SINCE" -H "$AUTH_H_BUYER")
echo "$R" | sed -n '$!p' | jq '. | {since:"'"$SINCE"'", keys:(keys)}' 2>/dev/null || true; echo "HTTP $(echo "$R" | tail -n1)"

say "OK ✅"
