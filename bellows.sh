#!/usr/bin/env bash
# Career Hub + pipeline board (Mac/Linux). Runs the local server that serves the
# Hub and board and powers the one-click lead sweep. Windows: use bellows.bat instead.
# Ctrl+C to stop.
cd "$(dirname "$0")"
# Free port 8765 from any prior dashboard server (stale server = empty board).
lsof -ti tcp:8765 2>/dev/null | xargs -r kill -9 2>/dev/null || true
python3 engine/server.py || python engine/server.py
