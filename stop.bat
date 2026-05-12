@echo off
title Sale Upload - Stop Servers
color 0C

echo.
echo  ============================================
echo    Sale Upload Portal - Stopping servers...
echo  ============================================
echo.

:: Kill uvicorn (backend)
echo  Stopping backend (uvicorn)...
taskkill /FI "WINDOWTITLE eq Sale Upload - Backend" /T /F >nul 2>&1
taskkill /IM "uvicorn.exe" /T /F >nul 2>&1

:: Kill node / vite (frontend)
echo  Stopping frontend (vite/node)...
taskkill /FI "WINDOWTITLE eq Sale Upload - Frontend" /T /F >nul 2>&1

echo.
echo  Done. Both servers have been stopped.
echo.
pause
