@echo off
title Sale Upload Launcher
color 0A

echo.
echo  ============================================
echo    Sale Upload Portal - Starting...
echo  ============================================
echo.

:: ── Resolve the project root (folder containing this .bat) ───────────
set "ROOT=%~dp0"
set "BACKEND=%ROOT%backend"
set "FRONTEND=%ROOT%frontend"

:: ── Check backend venv exists ────────────────────────────────────────
if not exist "%BACKEND%\venv\Scripts\activate.bat" (
    echo  [ERROR] Backend venv not found.
    echo  Please run:  cd backend ^&^& python -m venv venv ^&^& venv\Scripts\activate ^&^& pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

:: ── Check node_modules exists ────────────────────────────────────────
if not exist "%FRONTEND%\node_modules" (
    echo  [ERROR] Frontend node_modules not found.
    echo  Please run:  cd frontend ^&^& npm install
    echo.
    pause
    exit /b 1
)

:: ── Start Backend in a new window ────────────────────────────────────
echo  [1/2] Starting FastAPI backend on http://localhost:8001 ...
start "Sale Upload - Backend" cmd /k "cd /d "%BACKEND%" && call venv\Scripts\activate && uvicorn main:app --reload --port 8001"

:: ── Brief pause so backend gets a head-start ─────────────────────────
timeout /t 2 /nobreak >nul

:: ── Start Frontend in a new window ───────────────────────────────────
echo  [2/2] Starting Vite frontend on http://localhost:5173 ...
start "Sale Upload - Frontend" cmd /k "cd /d "%FRONTEND%" && npm run dev"

:: ── Brief pause then open browser ────────────────────────────────────
timeout /t 3 /nobreak >nul
echo.
echo  [3/3] Opening browser...
start "" "http://localhost:5173"

echo.
echo  ============================================
echo    Both servers are running!
echo    Backend  : http://localhost:8001
echo    Frontend : http://localhost:5173
echo    API Docs : http://localhost:8001/docs
echo  ============================================
echo.
echo  Close the two terminal windows to stop the servers,
echo  or run stop.bat to kill them automatically.
echo.
pause
