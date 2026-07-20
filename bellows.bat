@echo off
REM ============================================================
REM  Career Hub + pipeline board
REM
REM  Runs engine\server.py, which does three things a plain file
REM  server can't:
REM    1. serves the Career Hub (engine\hub.html) — progress, coaching, and the full pipeline
REM    2. SAVES status changes back to pipeline.md when you click
REM       "Applied" (a static server has no API, so the click
REM       would roll back and tell you it didn't save)
REM    3. powers the one-click "Run lead sweep" button
REM
REM  Double-click this file. It opens the browser for you.
REM  Close this window (or Ctrl+C) to stop.
REM ============================================================
cd /d "%~dp0"

REM Free port 8765 from any prior dashboard server so we always run current code
REM (a stale server holding the port is the usual cause of an empty board).
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":8765 " ^| findstr LISTENING') do taskkill /F /PID %%p >nul 2>nul

python engine\server.py
if errorlevel 1 py engine\server.py
if errorlevel 1 (
  echo.
  echo Could not start the server. Is Python installed and on PATH?
  pause
)
