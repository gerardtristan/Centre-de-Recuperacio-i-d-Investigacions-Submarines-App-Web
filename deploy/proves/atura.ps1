<#
.SYNOPSIS
  Atura el servidor de proves del C.R.I.S. (decisió 099). Les dades inventades es conserven
  fins a la propera arrencada; per esborrar-les, .\arrenca.ps1 -Reinicia.
#>
# «Continue»: a Windows PowerShell 5.1, amb «Stop», el que Docker escriu a stderr (el progrés)
# es tractaria com un error. Els errors es comproven amb $LASTEXITCODE.
$ErrorActionPreference = 'Continue'
Set-Location -LiteralPath $PSScriptRoot
& docker compose --profile tunel-rapid --profile tunel-fix stop
if ($LASTEXITCODE -ne 0) { Write-Host 'No s''ha pogut aturar. Docker Desktop està en marxa?' -ForegroundColor Red; exit 1 }
Write-Host 'Servidor de proves aturat. L''adreça pública ja no funciona.' -ForegroundColor Green
