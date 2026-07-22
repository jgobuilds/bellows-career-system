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

REM ------------------------------------------------------------
REM  ONE HUB AT A TIME.
REM
REM  Two different leftovers can be running, and they need
REM  different treatment:
REM
REM    1. Another Bellows window. Matched on its distinctive
REM       title and killed with /T so the python server it
REM       launched dies with it - killing the window alone would
REM       orphan python, which then keeps holding the port.
REM       This runs BEFORE we claim the title, so the only window
REM       carrying that title is a previous one. We cannot kill
REM       ourselves here.
REM
REM    2. A server on port 8765 that no Bellows window owns -
REM       started by hand, or left behind when a window was closed
REM       without stopping python. A stale server holding the port
REM       is the usual cause of a board that looks empty or shows
REM       yesterday's data, because the new code never gets to run.
REM ------------------------------------------------------------
REM Probe with tasklist, not taskkill: taskkill /FI exits 0 even when its filter
REM matched nothing, so branching on its errorlevel reports a window it never
REM closed. tasklist + findstr exits 1 on no match, which is the honest signal.
tasklist /FI "WINDOWTITLE eq Bellows Career Hub*" 2>nul | findstr /I "cmd.exe" >nul
if not errorlevel 1 (
  taskkill /F /T /FI "WINDOWTITLE eq Bellows Career Hub*" >nul 2>nul
  echo Closed a previous Bellows window.
)

for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":8765 " ^| findstr LISTENING') do (
  taskkill /F /PID %%p >nul 2>nul
  echo Freed port 8765 from a stale server ^(PID %%p^).
)

REM Claim the title only after the kills above, so this window is
REM never a candidate for them.
title Bellows Career Hub

python engine\server.py
if errorlevel 1 py engine\server.py
if errorlevel 1 (
  echo.
  echo Could not start the server. Is Python installed and on PATH?
  pause
)
