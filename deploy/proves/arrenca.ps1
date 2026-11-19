<#
.SYNOPSIS
  Arrenca el servidor de proves del C.R.I.S. en aquest portàtil (decisió 099).
  Guia: docs/guies/servidor-de-proves-al-portatil.md. Només dades inventades.

.PARAMETER Tunel
  rapid  (per defecte) adreça pública https://....trycloudflare.com, sense compte; canvia a cada arrencada.
  fix    adreça fixa amb el teu compte de Cloudflare (cal local\tunel-fix.env; guia, «Adreça fixa»).
  cap    sense túnel: només aquest portàtil (http://localhost:8080) o Tailscale.

.PARAMETER Reinicia
  Esborra la base de dades de proves i torna a carregar les dades inventades des de zero.

.EXAMPLE
  .\arrenca.ps1
.EXAMPLE
  .\arrenca.ps1 -Tunel cap
#>
param(
    [ValidateSet('rapid', 'fix', 'cap')][string]$Tunel = 'rapid',
    [switch]$Reinicia
)

# «Continue»: a Windows PowerShell 5.1, amb «Stop», el que Docker escriu a stderr (el progrés)
# es tractaria com un error. Els errors es comproven amb $LASTEXITCODE.
$ErrorActionPreference = 'Continue'
Set-Location -LiteralPath $PSScriptRoot
$Local = Join-Path $PSScriptRoot 'local'
$Utf8 = New-Object System.Text.UTF8Encoding $false
$CaddyImage = 'caddy:2.10.2'
$Perfils = @('--profile', 'tunel-rapid', '--profile', 'tunel-fix')

function Pas([string]$Text) { Write-Host ''; Write-Host "==> $Text" -ForegroundColor Cyan }
function Atura([string]$Text) { Write-Host ''; Write-Host $Text -ForegroundColor Red; exit 1 }

function Compose {
    & docker compose @args
    if ($LASTEXITCODE -ne 0) { Atura "Ha fallat: docker compose $($args -join ' ')" }
}

# Escriu un fitxer en UTF-8 sense BOM i amb finals de línia LF (Docker els llegeix així).
function Desa([string]$Fitxer, [string[]]$Linies) {
    [System.IO.File]::WriteAllText((Join-Path $Local $Fitxer), (($Linies -join "`n") + "`n"), $Utf8)
}

function Llegeix([string]$Fitxer) {
    $valors = @{}
    foreach ($linia in Get-Content -LiteralPath (Join-Path $Local $Fitxer) -Encoding UTF8) {
        if ($linia -match '^\s*([A-Z_]+)=(.*)$') { $valors[$Matches[1]] = $Matches[2] }
    }
    return $valors
}

# 1. Docker Desktop en marxa
Pas 'Comprovant Docker Desktop'
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Atura 'No trobo Docker. Instal·la Docker Desktop (guia, pas 1) i torna-ho a provar.'
}
& docker info *> $null
if ($LASTEXITCODE -ne 0) {
    Atura 'Docker Desktop no està en marxa. Obre''l, espera que digui «Engine running» i torna-ho a provar.'
}
New-Item -ItemType Directory -Force -Path $Local | Out-Null

# 2. Reiniciar des de zero (només dades inventades)
if ($Reinicia) {
    $resposta = Read-Host 'S''esborrarà la base de dades de proves (només dades inventades). Escriu SI per continuar'
    if ($resposta -ne 'SI') { Atura 'Cancel·lat: no s''ha esborrat res.' }
    Pas 'Esborrant la base de dades de proves'
    if (Test-Path (Join-Path $Local 'secrets.env')) { Compose @Perfils down -v }
}

# 3. Imatge de l'aplicació
Pas 'Construint l''aplicació (la primera vegada triga uns minuts)'
Compose build web

# 4. Secrets propis d'aquest portàtil (una sola vegada; mai al repositori)
if (-not (Test-Path (Join-Path $Local 'secrets.env'))) {
    Pas 'Generant els secrets d''aquest portàtil'
    $linies = & docker run --rm --entrypoint python cris-proves:actual deploy/proves/genera_secrets.py
    if ($LASTEXITCODE -ne 0 -or -not $linies) { Atura 'No s''han pogut generar els secrets.' }
    Desa 'secrets.env' $linies
}
$Secrets = Llegeix 'secrets.env'
if (-not (Test-Path (Join-Path $Local 'acces.caddy'))) {
    $resum = & docker run --rm $CaddyImage caddy hash-password --plaintext $Secrets['ACCES_CONTRASENYA']
    if ($LASTEXITCODE -ne 0 -or -not $resum) { Atura 'No s''ha pogut preparar la contrasenya del davant.' }
    Desa 'acces.caddy' @('basic_auth {', "`tproves $($resum.Trim())", '}')
}
if (-not (Test-Path (Join-Path $Local 'adreca.env'))) { Desa 'adreca.env' @('PUBLIC_SITE_URL=http://localhost:8080') }

# 5. Túnel i adreça pública
$Adreca = 'http://localhost:8080'
$Perfil = @()
$Adreces = @('PUBLIC_SITE_URL=http://localhost:8080')
switch ($Tunel) {
    'rapid' {
        Pas 'Obrint el túnel de Cloudflare'
        $Perfil = @('--profile', 'tunel-rapid')
        & docker compose @Perfils rm -sf tunel-fix *> $null
        Compose @Perfil up -d --no-deps tunel
        $trobada = $null
        for ($i = 0; $i -lt 30 -and -not $trobada; $i++) {
            Start-Sleep -Seconds 2
            $registre = (& docker compose @Perfil logs tunel 2>&1) -join "`n"
            $adreces = [regex]::Matches($registre, 'https://[a-z0-9-]+\.trycloudflare\.com')
            if ($adreces.Count -gt 0) { $trobada = $adreces[$adreces.Count - 1].Value }
        }
        if ($trobada) {
            $Adreca = $trobada
            $Adreces = @("PUBLIC_SITE_URL=$Adreca")
        } else {
            Write-Host 'No he rebut l''adreça del túnel. Continuo només en local; mira «docker compose logs tunel».' -ForegroundColor Yellow
        }
    }
    'fix' {
        $fitxer = Join-Path $Local 'tunel-fix.env'
        if (-not (Test-Path $fitxer)) { Atura 'Falta local\tunel-fix.env (guia, apartat «Adreça fixa»).' }
        $fix = Llegeix 'tunel-fix.env'
        if (-not $fix['TUNNEL_TOKEN'] -or $fix['ADRECA'] -notmatch '^https://([a-z0-9.-]+)$') {
            Atura 'local\tunel-fix.env ha de tenir TUNNEL_TOKEN=... i ADRECA=https://el-teu-domini'
        }
        $domini = $Matches[1]
        $Perfil = @('--profile', 'tunel-fix')
        & docker compose @Perfils rm -sf tunel *> $null
        $Adreca = $fix['ADRECA']
        $Adreces = @(
            "PUBLIC_SITE_URL=$Adreca",
            "DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,$domini",
            "DJANGO_CSRF_TRUSTED_ORIGINS=$Adreca"
        )
    }
    'cap' {
        & docker compose @Perfils rm -sf tunel tunel-fix *> $null
    }
}
Desa 'adreca.env' $Adreces

# 6. Aplicació, base de dades, cua, bústia i Caddy
Pas 'Arrencant el servidor de proves'
Compose @Perfil up -d

Pas 'Esperant que l''aplicació respongui (la primera vegada carrega les dades inventades)'
$credencial = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes("proves:$($Secrets['ACCES_CONTRASENYA'])"))
$llesta = $false
for ($i = 0; $i -lt 100 -and -not $llesta; $i++) {
    try {
        $r = Invoke-WebRequest -UseBasicParsing -TimeoutSec 5 -Uri 'http://localhost:8080/salut/' -ErrorAction Stop `
            -Headers @{ Authorization = "Basic $credencial" }
        $llesta = ($r.StatusCode -eq 200)
    } catch { Start-Sleep -Seconds 3 }
}
if (-not $llesta) { Atura 'L''aplicació no respon. Mira què passa amb: docker compose logs web' }

# 7. Com s'hi entra
Write-Host ''
Write-Host '============================================================' -ForegroundColor Green
Write-Host ' Servidor de proves del C.R.I.S. en marxa (només dades inventades)' -ForegroundColor Green
Write-Host '============================================================' -ForegroundColor Green
Write-Host " Adreça per compartir:  $Adreca"
Write-Host ' Des d''aquest portàtil:  http://localhost:8080'
Write-Host " Contrasenya del davant: usuari proves / $($Secrets['ACCES_CONTRASENYA'])"
Write-Host ''
Write-Host " Administració:  $Adreca/gestio/"
Write-Host '   comptes: admin-demo, secretaria-demo, tresorer-demo, president-demo, instructor-demo'
Write-Host '   contrasenya: contrasenya-de-proves-1954'
Write-Host "   doble factor (el mateix per a tots): $($Secrets['STAGING_TOTP_SECRET'])"
Write-Host '   afegeix-lo a Google Authenticator o Aegis com a «clau de configuració».'
Write-Host " Àrea personal dels socis: $Adreca/entrar/  (p. ex. ple.dret.pagat@example.org, mateixa contrasenya)"
Write-Host " Bústia de proves (tots els correus hi arriben): $Adreca/bustia/"
Write-Host ''
Write-Host ' Deixa el portàtil encès, connectat al corrent i sense que entri en repòs.'
Write-Host ' Per aturar-lo: .\atura.ps1'
if ($Tunel -eq 'rapid') { Write-Host ' L''adreça pública canvia cada vegada que s''arrenca el túnel.' -ForegroundColor Yellow }
exit 0
