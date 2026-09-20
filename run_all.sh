#!/usr/bin/env bash
# Starts backend + frontend (+ gps_bridge if RUN_GPS_BRIDGE=1) from deploy.env.
set -u
ROOT="$(cd "$(dirname "$0")" && pwd)"
CONF="$ROOT/deploy.env"
[ -f "$CONF" ] || { echo "Missing deploy.env - run: cp deploy.env.example deploy.env  (then edit it)"; exit 1; }

set -a; . "$CONF"; set +a          # export everything in deploy.env
[ -n "${PYV2XLIB_VENDOR_DIR:-}" ] || unset PYV2XLIB_VENDOR_DIR

PIDS=()
cleanup() { echo; echo "Stopping..."; kill "${PIDS[@]}" 2>/dev/null; wait 2>/dev/null; exit 0; }
trap cleanup INT TERM

(cd "$ROOT/backend" && exec python3 -u app.py) & PIDS+=($!)

(cd "$ROOT/frontend" && exec npm run dev) & PIDS+=($!)

if [ "${RUN_GPS_BRIDGE:-0}" = "1" ]; then
  # subshell: sourcing ROS2 here must not leak into the backend's Python env
  ( [ -n "${ROS_SETUP:-}" ] && . "$ROS_SETUP"
    cd "$ROOT/backend" && exec python3 -u gps_bridge.py ) & PIDS+=($!)
fi

wait
