@echo off
setlocal EnableExtensions

cd /d "%~dp0.."

set ATTEMPT=1
:retry
docker compose up --build -d
if %ERRORLEVEL% EQU 0 goto :done

if %ATTEMPT% GEQ 2 exit /b 1

set /a ATTEMPT+=1
timeout /t 5 /nobreak >nul
goto :retry

:done
exit /b 0
