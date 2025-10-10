#!/usr/bin/env bash
set -euo pipefail

# ---------------- Colors & helpers ----------------
BLUE=$'\033[34;1m'; YELLOW=$'\033[33;1m'; RED=$'\033[31;1m'; RESET=$'\033[0m'
say()  { printf "\n%s▶ %s%s\n"   "$BLUE" "$*" "$RESET"; }
warn() { printf "\n%s! %s%s\n"   "$YELLOW" "$*" "$RESET"; }
fail() { printf "\n%s✗ %s%s\n"   "$RED" "$*" "$RESET"; exit 1; }

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

# ---------------- 0) Health ----------------
say "Healthcheck"
curl -sS http://localhost:8000/health || true

# ---------------- 1) SELLER ----------------
EMAIL_SELLER="${EMAIL_SELLER:-seller+$(date +%s)@${DOMAIN}}"

say "Register SELLER: $EMAIL_SELLER"
R=$(apijson POST "$BASE/auth/register" "$(jq -n --arg name "Seller" --arg email "$EMAIL_SELLER" --arg pass "$PASS_SELLER" '{name:$name,email:$email,password:$pass}')" )
BODY=$(echo "$R" | sed -n '$!p'); CODE=$(echo "$R" | tail -n1)
printf "HTTP %s\n" "$CODE"; echo "$BODY" | jq . 2>/dev/null || true
[[ "$CODE" == "201" || "$CODE" == "400" ]] || fail "register SELLER falló"

say "Login SELLER: $EMAIL_SELLER"
R=$(apijson POST "$BASE/auth/login" "$(jq -n --arg email "$EMAIL_SELLER" --arg pass "$PASS_SELLER" '{email:$email,password:$pass}')" )
BODY=$(echo "$R" | sed -n '$!p'); CODE=$(echo "$R" | tail -n1)
printf "HTTP %s\n" "$CODE"; echo "$BODY" | jq .
[[ "$CODE" == "200" ]] || fail "login SELLER falló"
TOKEN_SELLER=$(echo "$BODY" | jget '.access_token')
AUTH_H_SELLER="Authorization: Bearer $TOKEN_SELLER"

say "GET /auth/me (SELLER)"
R=$(api GET "$BASE/auth/me" -H "$AUTH_H_SELLER")
ME_SELLER=$(echo "$R" | sed -n '$!p'); printf "HTTP %s\n" "$(echo "$R" | tail -n1)"; echo "$ME_SELLER" | jq .
SELLER_ID=$(echo "$ME_SELLER" | jget '.id')

# ---------------- 2) BUYER ----------------
EMAIL_BUYER="${EMAIL_BUYER:-buyer+$(date +%s)@${DOMAIN}}"

say "Register BUYER: $EMAIL_BUYER"
R=$(apijson POST "$BASE/auth/register" "$(jq -n --arg name "Buyer" --arg email "$EMAIL_BUYER" --arg pass "$PASS_BUYER" '{name:$name,email:$email,password:$pass}')" )
BODY=$(echo "$R" | sed -n '$!p'); CODE=$(echo "$R" | tail -n1)
printf "HTTP %s\n" "$CODE"; echo "$BODY" | jq . 2>/dev/null || true
[[ "$CODE" == "201" || "$CODE" == "400" ]] || fail "register BUYER falló"

say "Login BUYER: $EMAIL_BUYER"
R=$(apijson POST "$BASE/auth/login" "$(jq -n --arg email "$EMAIL_BUYER" --arg pass "$PASS_BUYER" '{email:$email,password:$pass}')" )
BODY=$(echo "$R" | sed -n '$!p'); CODE=$(echo "$R" | tail -n1)
printf "HTTP %s\n" "$CODE"; echo "$BODY" | jq .
[[ "$CODE" == "200" ]] || fail "login BUYER falló"
TOKEN_BUYER=$(echo "$BODY" | jget '.access_token')
AUTH_H_BUYER="Authorization: Bearer $TOKEN_BUYER"

say "GET /auth/me (BUYER)"
R=$(api GET "$BASE/auth/me" -H "$AUTH_H_BUYER")
ME_BUYER=$(echo "$R" | sed -n '$!p'); printf "HTTP %s\n" "$(echo "$R" | tail -n1)"; echo "$ME_BUYER" | jq .
BUYER_ID=$(echo "$ME_BUYER" | jget '.id')

# ---------------- 3) Catálogos ----------------
say "GET /categories"
R=$(api GET "$BASE/categories" -H "$AUTH_H_SELLER")
CATS=$(echo "$R" | sed -n '$!p'); CODE=$(echo "$R" | tail -n1)
printf "HTTP %s\n" "$CODE"; echo "$CATS" | jq '((.items? // .) | map({slug,id}) )'
CAT_LAPTOPS=$(echo "$CATS" | jget '((.items? // .)[] | select(.slug=="laptops") | .id)')

say "GET /brands"
R=$(api GET "$BASE/brands" -H "$AUTH_H_SELLER")
BRAS=$(echo "$R" | sed -n '$!p'); CODE=$(echo "$R" | tail -n1)
printf "HTTP %s\n" "$CODE"; echo "$BRAS" | jq '((.items? // .) | map({slug,id}) )'
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
printf "HTTP %s\n" "$CODE"; echo "$BODY" | jq .
[[ "$CODE" == "201" ]] || fail "crear listing falló"
L_ID=$(echo "$BODY" | jget '.id')
# SELLER_ID ya lo tenemos de /auth/me

say "GET /listings/{id} (SELLER)"
R=$(api GET "$BASE/listings/$L_ID" -H "$AUTH_H_SELLER")
printf "%s\n" "$(echo "$R" | sed -n '$!p' | jq .)"; printf "HTTP %s\n" "$(echo "$R" | tail -n1)"

say "GET /listings (geo)"
R=$(api GET "$BASE/listings?near_lat=4.601&near_lon=-74.066&radius_km=5&page_size=5" -H "$AUTH_H_BUYER")
printf "%s\n" "$(echo "$R" | sed -n '$!p' | jq '((.items? // .) | map({id,title,created_at}))')"; printf "HTTP %s\n" "$(echo "$R" | tail -n1)"

# ---------------- 5) Imágenes (PUT presign + confirm) ----------------
say "POST /images/presign (SELLER)"
UP_FN="foto_demo.jpg"
PAYLOAD=$(jq -n --arg name "$UP_FN" --arg ctype "image/jpeg" --arg listing "$L_ID" \
  '{filename:$name, content_type:$ctype, scope:"listing", listing_id:$listing}')
R=$(apijson POST "$BASE/images/presign" "$PAYLOAD" -H "$AUTH_H_SELLER")
PRE=$(echo "$R" | sed -n '$!p'); CODE=$(echo "$R" | tail -n1)
printf "HTTP %s\n" "$CODE"; echo "$PRE" | jq .
[[ "$CODE" == "201" ]] || fail "presign falló"
UPLOAD_URL=$(echo "$PRE" | jget '.upload_url // .url')
OBJECT_KEY=$(echo "$PRE" | jget '.object_key // .storage_key // .fields.key // .key')

say "Subida presignada tipo PUT"
if command -v dd >/dev/null; then
  dd if=/dev/urandom of="/tmp/$UP_FN" bs=1024 count=5 status=none
else
  echo "fake" > "/tmp/$UP_FN"
fi
declare -a RESOLVE_OPTS
RESOLVE_OPTS=(--resolve "minio:9000:127.0.0.1")
curl -sS "${RESOLVE_OPTS[@]}" \
  -X PUT -H "Content-Type: image/jpeg" \
  --data-binary "@/tmp/$UP_FN" \
  "$UPLOAD_URL" >/dev/null || warn "PUT presign falló (ignorable en local)"

say "POST /images/confirm"
PAYLOAD=$(jq -n --arg listing "$L_ID" --arg sk "$OBJECT_KEY" \
  '{scope:"listing", listing_id:$listing, object_key:$sk, width:800, height:600}')
R=$(apijson POST "$BASE/images/confirm" "$PAYLOAD" -H "$AUTH_H_SELLER")
printf "%s\n" "$(echo "$R" | sed -n '$!p' | jq .)"; printf "HTTP %s\n" "$(echo "$R" | tail -n1)"

# ---------------- 6) Chat/Mensajes (BUYER) ----------------
say "POST /chats (BUYER abre chat con listing del SELLER)"
R=$(apijson POST "$BASE/chats" "$(jq -n --arg l "$L_ID" '{listing_id:$l}')" -H "$AUTH_H_BUYER")
BODY=$(echo "$R" | sed -n '$!p'); printf "%s\n" "$(echo "$BODY" | jq .)"; printf "HTTP %s\n" "$(echo "$R" | tail -n1)"
CHAT_ID=$(echo "$BODY" | jget '.id')

say "POST /messages (BUYER)"
R=$(apijson POST "$BASE/messages" "$(jq -n --arg c "$CHAT_ID" --arg txt "Hola, ¿sigue disponible?" '{chat_id:$c, message_type:"text", content:$txt}')" -H "$AUTH_H_BUYER")
printf "%s\n" "$(echo "$R" | sed -n '$!p' | jq .)"; printf "HTTP %s\n" "$(echo "$R" | tail -n1)"

# ---------------- 7) Orders / Payments / Escrow / Review ----------------
say "POST /orders"
ORDER_PAYLOAD=$(jq -n --arg l "$L_ID" --argjson qty 1 '{listing_id:$l, quantity:$qty}')
echo "Order payload:"; echo "$ORDER_PAYLOAD" | jq .
R=$(apijson POST "$BASE/orders" "$ORDER_PAYLOAD" -H "$AUTH_H_BUYER")
BODY=$(echo "$R" | sed -n '$!p'); echo "$BODY" | jq .; printf "HTTP %s\n" "$(echo "$R" | tail -n1)"
[[ "$(echo "$R" | tail -n1)" == "201" ]] || fail "crear orden falló"
ORDER_ID=$(echo "$BODY" | jget '.id')

say "POST /orders/{id}/pay"
R=$(api POST "$BASE/orders/$ORDER_ID/pay" -H "$AUTH_H_BUYER")
BODY=$(echo "$R" | sed -n '$!p'); echo "$BODY" | jq .; printf "HTTP %s\n" "$(echo "$R" | tail -n1)"
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
  echo "$R" | sed -n '$!p' | jq .; printf "HTTP %s\n" "$(echo "$R" | tail -n1)"
fi

say "POST /payments/capture"
CAP_REF="TESTPROV-${ORDER_ID:0:8}"
CAPTURE_PAYLOAD=$(jq -n --arg o "$ORDER_ID" --arg p "$CAP_REF" \
  '{order_id:$o, provider_ref:$p}')
R=$(apijson POST "$BASE/payments/capture" "$CAPTURE_PAYLOAD" -H "$AUTH_H_BUYER")
echo "$R" | sed -n '$!p' | jq .; printf "HTTP %s\n" "$(echo "$R" | tail -n1)"

# Extra 1: inyectar escrow.step (para bq/1_2)
say "POST /events (escrow.step demo)"
NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ)
EV=$(jq -n --arg now "$NOW" --arg o "$ORDER_ID" --arg uid "$BUYER_ID" \
  '{events:[{event_type:"escrow.step", session_id:"dev-sess", user_id:$uid, order_id:$o, step:"payment_made", properties:{result:"ok"}, occurred_at:$now}]}')
R=$(apijson POST "$BASE/events" "$EV" -H "$AUTH_H_BUYER")
echo "$R" | sed -n '$!p' | jq .; printf "HTTP %s\n" "$(echo "$R" | tail -n1)"

say "POST /orders/{id}/complete"
R=$(api POST "$BASE/orders/$ORDER_ID/complete" -H "$AUTH_H_BUYER")
BODY=$(echo "$R" | sed -n '$!p'); echo "$BODY" | jq .; printf "HTTP %s\n" "$(echo "$R" | tail -n1)"

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

echo "$BODY" | jq . 2>/dev/null || true; printf "HTTP %s\n" "$CODE"

# ---------------- 8) Features / Analytics Seed (eventos) ----------------
# Usamos /features/use (si existe) y además inyectamos eventos explícitos para que las BQ 2.x, 3.x y 5.x tengan datos.

say "POST /features/use"
R=$(apijson POST "$BASE/features/use" '{"feature_key":"quick_view","action":"open"}' -H "$AUTH_H_BUYER")
echo "$R" | sed -n '$!p' | jq . 2>/dev/null || true; printf "HTTP %s\n" "$(echo "$R" | tail -n1)"

say "POST /events (array: ui.click + feature.used + sesiones/DAU)"
NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ)
NOW2=$(date -u +%Y-%m-%dT%H:%M:%SZ)
EV=$(jq -n --arg now "$NOW" --arg now2 "$NOW2" \
             --arg uid "$BUYER_ID" --arg lid "$L_ID" '
{
  events: [
    # Para BQ 2_1 y 2_2
    {event_type:"ui.click", session_id:"dev-sess",   user_id:$uid, properties:{button:"buy"},     occurred_at:$now},
    {event_type:"ui.click", session_id:"dev-sess-2", user_id:$uid, properties:{button:"details"}, occurred_at:$now2},

    # Para BQ 3_1 (DAU) y 3_2 (sessions)
    {event_type:"ui.view",  session_id:"dev-sess",   user_id:$uid, properties:{screen:"listing"}, occurred_at:$now},

    # Para BQ 5_1 (quick_view por categoría via join con listing)
    {event_type:"feature.used", session_id:"dev-sess", user_id:$uid, listing_id:$lid,
     properties:{feature_key:"quick_view"}, occurred_at:$now}
  ]
}')
R=$(apijson POST "$BASE/events" "$EV" -H "$AUTH_H_BUYER")
echo "$R" | sed -n '$!p' | jq .; printf "HTTP %s\n" "$(echo "$R" | tail -n1)"

# ---------------- 9) BQ endpoints: 1.x, 2.x, 3.x, 4.x, 5.x ----------------
FROM=$(iso_days_ago_start 7)
TO=$(date -u +%Y-%m-%dT23:59:59Z)

fetch_bq() {
  local path="$1"
  say "GET $path"
  local R; R=$(api GET "$BASE$path?start=$FROM&end=$TO" -H "$AUTH_H_BUYER")
  local BODY; BODY=$(echo "$R" | sed -n '$!p')
  local CODE; CODE=$(echo "$R" | tail -n1)
  echo "$BODY" | jq . 2>/dev/null || true
  printf "HTTP %s\n" "$CODE"
  [[ "$CODE" == "200" ]] || fail "Fallo GET $path"
}

# 1.x (existentes)
fetch_bq "/analytics/bq/1_1"
fetch_bq "/analytics/bq/1_2"

# 2.x (eventos por tipo y clicks por botón)
fetch_bq "/analytics/bq/2_1"
fetch_bq "/analytics/bq/2_2"

# 3.x (DAU y sesiones)
fetch_bq "/analytics/bq/3_1"
fetch_bq "/analytics/bq/3_2"

# 4.x (órdenes por estado y GMV)
fetch_bq "/analytics/bq/4_1"
fetch_bq "/analytics/bq/4_2"

# 5.x (quick_view por categoría)
fetch_bq "/analytics/bq/5_1"

# ---------------- 10) Otros endpoints de e2e ----------------
say "POST /events (array, genérico)"
R=$(apijson POST "$BASE/events" '{"events":[{"event_type":"ui.click","session_id":"dev-sess","properties":{"button":"buy-again"}}]}' -H "$AUTH_H_BUYER")
echo "$R" | sed -n '$!p' | jq . 2>/dev/null || true; printf "HTTP %s\n" "$(echo "$R" | tail -n1)"

say "POST /devices"
R=$(apijson POST "$BASE/devices" '{"platform":"android","push_token":"TEST_PUSH","app_version":"1.0.0"}' -H "$AUTH_H_BUYER")
echo "$R" | sed -n '$!p' | jq . 2>/dev/null || true; printf "HTTP %s\n" "$(echo "$R" | tail -n1)"

say "POST /contacts/match"
H=$(printf 'demo@%s' "$DOMAIN" | openssl dgst -sha256 -binary | xxd -p -c 256)
R=$(apijson POST "$BASE/contacts/match" "$(jq -n --arg h "$H" '{email_hashes:[$h]}')" -H "$AUTH_H_BUYER")
echo "$R" | sed -n '$!p' | jq . 2>/dev/null || true; printf "HTTP %s\n" "$(echo "$R" | tail -n1)"

say "GET /sync/delta"
SINCE=$(iso_hours_ago 1)
R=$(api GET "$BASE/sync/delta?since=$SINCE" -H "$AUTH_H_BUYER")
echo "$R" | sed -n '$!p' | jq '. | {since:"'"$SINCE"'", keys:(keys)}' 2>/dev/null || true
printf "HTTP %s\n" "$(echo "$R" | tail -n1)"

say "OK ✅"
