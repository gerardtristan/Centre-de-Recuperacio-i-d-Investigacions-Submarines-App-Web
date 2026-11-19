@echo off
rem Doble clic per aturar el servidor de proves (decisio 099). Fa correr atura.ps1.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0atura.ps1" %*
pause
