$ErrorActionPreference = 'Stop'
$Root = Resolve-Path (Join-Path $PSScriptRoot '..')
if (-not (Test-Path (Join-Path $Root '.env'))) { Copy-Item -Path (Join-Path $Root '.env.example') -Destination (Join-Path $Root '.env') }
if (-not (Test-Path (Join-Path $Root 'backend/.env'))) { Copy-Item -Path (Join-Path $Root 'backend/.env.example') -Destination (Join-Path $Root 'backend/.env') }
if (-not (Test-Path (Join-Path $Root 'frontend/.env.local'))) { Copy-Item -Path (Join-Path $Root 'frontend/.env.example') -Destination (Join-Path $Root 'frontend/.env.local') }
Write-Host 'Environment templates copied. Edit .env and backend/.env before any shared or public deployment.'
Write-Host 'Start all local services with: docker compose up --build'
