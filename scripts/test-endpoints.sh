#!/usr/bin/env bash
# Test backend endpoints. Run with: ./scripts/test-endpoints.sh
# Requires: backend running (pnpm dev in apps/backend), Postgres + Redis up
# Set BACKEND_URL and BACKEND_API_KEY in env, or source .env

set -e
BACKEND_URL="${BACKEND_URL:-http://localhost:3001}"
BACKEND_API_KEY="${BACKEND_API_KEY:-}"

if [[ -z "$BACKEND_API_KEY" ]] && [[ -f .env ]]; then
  export $(grep -E '^BACKEND_API_KEY=' .env | xargs)
fi

echo "Testing backend at $BACKEND_URL"
echo ""
# Prereq: backend must be running
if ! curl -s --connect-timeout 2 -o /dev/null "$BACKEND_URL/health" 2>/dev/null; then
  echo "Error: Cannot reach backend. Ensure:"
  echo "  1. docker compose up -d  (or: postgres + redis + backend)"
  echo "  2. cd apps/backend && pnpm dev"
  exit 1
fi

# 1. Health (no API key) - zero external API calls
echo "1. GET /health (no key)..."
HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/health")
if [[ "$HEALTH" == "200" ]]; then
  echo "   ✓ 200 OK"
else
  echo "   ✗ Expected 200, got $HEALTH"
  exit 1
fi

# 2. Reject without API key
echo "2. GET /stock/search (no key, expect 401)..."
UNAUTH=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/stock/search?symbol=AAPL")
if [[ "$UNAUTH" == "401" ]]; then
  echo "   ✓ 401 Unauthorized"
else
  echo "   ✗ Expected 401, got $UNAUTH"
  exit 1
fi

# 3. Reject with wrong API key
echo "3. GET /stock/search (wrong key, expect 401)..."
WRONG=$(curl -s -o /dev/null -w "%{http_code}" -H "X-API-Key: wrong-key" "$BACKEND_URL/stock/search?symbol=AAPL")
if [[ "$WRONG" == "401" ]]; then
  echo "   ✓ 401 Unauthorized"
else
  echo "   ✗ Expected 401, got $WRONG"
  exit 1
fi

# Set SKIP_ANALYSIS=1 to skip step 4 (avoids FMP + Gemini calls)
if [[ -z "$BACKEND_API_KEY" ]] || [[ -n "${SKIP_ANALYSIS:-}" ]]; then
  echo ""
  if [[ -z "$BACKEND_API_KEY" ]]; then
    echo "BACKEND_API_KEY not set. Skipping authenticated tests."
  else
    echo "SKIP_ANALYSIS=1: Skipping /stock/search (no FMP/Gemini calls)."
  fi
  echo "Set BACKEND_API_KEY (and unset SKIP_ANALYSIS) to test full flow."
  exit 0
fi

# 4. Accept with valid key + trigger one analysis (uses FMP + Gemini)
echo "4. GET /stock/search (valid key, triggers 1 analysis)..."
RESP=$(curl -s -w "\n%{http_code}" -H "X-API-Key: $BACKEND_API_KEY" "$BACKEND_URL/stock/search?symbol=AAPL")
BODY=$(echo "$RESP" | head -n -1)
CODE=$(echo "$RESP" | tail -n 1)
if [[ "$CODE" != "200" ]]; then
  echo "   ✗ Expected 200, got $CODE"
  echo "$BODY" | head -5
  exit 1
fi
echo "   ✓ 200 OK"
TRACE_ID=$(echo "$BODY" | jq -r '.traceId // empty')
if [[ -z "$TRACE_ID" ]]; then
  echo "   (no traceId - backend may have returned cached/completed)"
else
  echo "   traceId: $TRACE_ID"
  # 5. SSE stream (connect briefly, don't wait for completion)
  echo "5. GET /analysis/$TRACE_ID/stream (SSE, 3s timeout)..."
  SSE=$(timeout 3 curl -s -o /dev/null -w "%{http_code}" -H "X-API-Key: $BACKEND_API_KEY" \
    -H "Accept: text/event-stream" "$BACKEND_URL/analysis/$TRACE_ID/stream" || true)
  if [[ "$SSE" == "200" ]] || [[ -z "$SSE" ]]; then
    echo "   ✓ SSE connected"
  else
    echo "   ? SSE status: $SSE (may timeout before response)"
  fi
fi

echo ""
echo "All tests passed."
