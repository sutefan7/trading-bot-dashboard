#!/bin/bash

set -euo pipefail

PORT="${1:-5001}"
HOST="${HOST:-localhost}"
HTTPS_FLAG="--https"

echo "============================================================"
echo "🔁 Restart Trading Bot Dashboard"
echo "============================================================"
echo "Target: https://${HOST}:${PORT}"

echo "🔎 Stopping existing processes on port ${PORT} (if any)..."
PIDS_PORT=$(lsof -tiTCP:${PORT} -sTCP:LISTEN || true)
PIDS_WS=$(pgrep -f "web_server.py" || true)
PIDS_DW=$(pgrep -f "dev_watch.py" || true)

ALL_PIDS="${PIDS_PORT} ${PIDS_WS} ${PIDS_DW}"
for PID in ${ALL_PIDS}; do
  if [[ -n "${PID}" ]]; then
    echo "  → Killing PID ${PID}"
    kill "${PID}" || true
  fi
done

sleep 1

# Force kill if still listening
PIDS_LEFT=$(lsof -tiTCP:${PORT} -sTCP:LISTEN || true)
if [[ -n "${PIDS_LEFT}" ]]; then
  echo "⚠️  Forcing kill on PIDs: ${PIDS_LEFT}"
  kill -9 ${PIDS_LEFT} || true
fi

echo "✅ Port ${PORT} is free."

echo "🚀 Starting server (HTTPS) on port ${PORT}..."
nohup python3 web_server.py ${HTTPS_FLAG} --port ${PORT} > logs/server_stdout.log 2>&1 &
SERVER_PID=$!
echo "✅ Started with PID ${SERVER_PID}"

echo "⏳ Waiting for server to come up..."
for i in {1..20}; do
  if curl -sk "https://${HOST}:${PORT}/api/health" >/dev/null; then
    break
  fi
  sleep 0.5
done

echo "🔍 Health check (first 400 bytes):"
curl -sk "https://${HOST}:${PORT}/api/health" | head -c 400; echo

echo "🔎 Verifying port status:"
lsof -iTCP:${PORT} -sTCP:LISTEN || true

echo "🔁 Optional: trigger sync-now (press Enter to skip)"
read -r -p "Run sync now? [y/N]: " RUN_SYNC
if [[ "${RUN_SYNC}" == "y" || "${RUN_SYNC}" == "Y" ]]; then
  echo "▶️  Calling /api/sync-now ..."
  HTTP_CODE=$(curl -sk -o /tmp/sync_resp.json -w "%{http_code}" -X POST "https://${HOST}:${PORT}/api/sync-now") || true
  echo "HTTP ${HTTP_CODE}"
  echo "Response (first 400 bytes):"
  head -c 400 /tmp/sync_resp.json; echo
fi

echo "✅ Done. Logs: logs/server_stdout.log"


