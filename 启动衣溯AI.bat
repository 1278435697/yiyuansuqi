@echo off
setlocal
set ROOT=%~dp0
cd /d "%ROOT%"

echo ============================================
echo    YisuAI Platform - Quick Start
echo    Backend : port 8765
echo    Frontend: port 5173
echo ============================================

REM --- 1) ensure MySQL 8.0 running ---
powershell -NoProfile -ExecutionPolicy Bypass -Command "$c = Get-NetTCPConnection -LocalPort 3306 -State Listen -ErrorAction SilentlyContinue; if (-not $c) { Start-Process -FilePath 'C:\mysql\mysql-8.0.44-winx64\bin\mysqld.exe' -ArgumentList '--defaults-file=C:\mysql\my.ini' -WindowStyle Hidden; Start-Sleep -Seconds 3 }"

REM --- 2) clean leftover listeners ---
powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-NetTCPConnection -LocalPort 8765,5173 -State Listen -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }; Start-Sleep -Seconds 2"

REM --- 3) start backend (hidden, logs to file) ---
powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%ROOT%backend\.venv\Scripts\python.exe' -ArgumentList '-m','uvicorn','app.main:app','--port','8765','--host','127.0.0.1' -WorkingDirectory '%ROOT%backend' -WindowStyle Hidden -RedirectStandardOutput '%ROOT%backend\uvi_out.log' -RedirectStandardError '%ROOT%backend\uvi_err.log'"

REM --- 4) start frontend ---
powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath 'cmd.exe' -ArgumentList '/c','npm run dev' -WorkingDirectory '%ROOT%frontend' -WindowStyle Hidden"

REM --- 5) wait for backend then open browser ---
echo Waiting for services, please wait...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ok=0; for ($i=0; $i -lt 40; $i++) { Start-Sleep -Seconds 1; try { $b = Invoke-WebRequest -Uri 'http://127.0.0.1:8765/docs' -UseBasicParsing -TimeoutSec 2; if ($b.StatusCode -eq 200) { $ok++; break } } catch {} }; if ($ok) { Start-Process 'http://localhost:5173' } else { Write-Host '[WARN] backend not ready in 40s, check backend\uvi_err.log' }"

echo.
echo ============================================
echo    Started: http://localhost:5173
echo    Stop   : double-click close-yisu.bat
echo ============================================
pause