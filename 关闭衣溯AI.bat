@echo off
title YisuAI-Stopper

echo ============================================
echo    YisuAI Platform - Stop Services
echo    Backend : port 8765
echo    Frontend: port 5173
echo ============================================

REM --- kill by ports via PowerShell ---
powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-NetTCPConnection -LocalPort 8765,5173 -State Listen -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }"

REM --- verify ---
powershell -NoProfile -ExecutionPolicy Bypass -Command "$b = Get-NetTCPConnection -LocalPort 8765 -State Listen -ErrorAction SilentlyContinue; $f = Get-NetTCPConnection -LocalPort 5173 -State Listen -ErrorAction SilentlyContinue; if ($b -or $f) { Write-Host '[WARN] Some ports still open' } else { Write-Host 'All YisuAI services stopped.' }"

echo.
echo MySQL (port 3306) stays running so data persists.
echo To stop MySQL too:  taskkill /IM mysqld.exe /F
echo.
pause