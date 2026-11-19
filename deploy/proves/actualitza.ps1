<#
.SYNOPSIS
  Actualitza el servidor de proves del C.R.I.S. a l'última versió de master i el torna a
  arrencar (decisió 099). Les migracions s'apliquen soles en arrencar i les dades es conserven.

.PARAMETER Tunel
  El mateix que a arrenca.ps1: rapid (per defecte), fix o cap.
#>
param(
    [ValidateSet('rapid', 'fix', 'cap')][string]$Tunel = 'rapid'
)

# «Continue»: a Windows PowerShell 5.1, amb «Stop», el que Git escriu a stderr es tractaria com
# un error. Els errors es comproven amb $LASTEXITCODE.
$ErrorActionPreference = 'Continue'
$Arrel = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Set-Location -LiteralPath $Arrel

function Atura([string]$Text) { Write-Host ''; Write-Host $Text -ForegroundColor Red; exit 1 }

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Atura 'No trobo Git. Instal·la''l (guia, pas 1) i torna-ho a provar.'
}

Write-Host ''
Write-Host '==> Baixant l''última versió de master' -ForegroundColor Cyan
$canvis = & git status --porcelain --untracked-files=no
if ($canvis) {
    Atura "Hi ha fitxers del repositori modificats en aquest portàtil:`n$($canvis -join "`n")`nDesfés-los (git checkout -- .) i torna-ho a provar."
}
& git checkout master
if ($LASTEXITCODE -ne 0) { Atura 'No s''ha pogut passar a la branca master.' }
& git pull --ff-only origin master
if ($LASTEXITCODE -ne 0) { Atura 'No s''ha pogut baixar l''última versió. Hi ha connexió a internet?' }
& git log -1 --format='Versió: %h, %cd, %s' --date=format:'%d/%m/%Y %H:%M'

# arrenca.ps1 reconstrueix la imatge, aplica les migracions i torna a arrencar l'aplicació.
& (Join-Path $PSScriptRoot 'arrenca.ps1') -Tunel $Tunel
exit $LASTEXITCODE
