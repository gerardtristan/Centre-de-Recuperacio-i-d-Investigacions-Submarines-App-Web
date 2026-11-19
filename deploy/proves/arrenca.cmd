@echo off
rem Doble clic per arrencar el servidor de proves (decisio 099). Fa correr arrenca.ps1.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0arrenca.ps1" %*
pause
