@echo off
rem Doble clic per actualitzar el servidor de proves (decisio 099). Fa correr actualitza.ps1.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0actualitza.ps1" %*
pause
