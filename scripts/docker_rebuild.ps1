#!/usr/bin/env pwsh
# ============================================================
# Docker Cleanup & Rebuild Script for EVAonline
# ============================================================
# Usage: ./scripts/docker_rebuild.ps1
# 
# Este script:
# 1. Para todos os containers
# 2. Remove images antigas
# 3. Remove volumes (opcional)
# 4. Reconstrói a imagem
# 5. Inicia docker-compose
# ============================================================

param(
    [Parameter(HelpMessage = "Tipo de build: runtime, dev, test")]
    [ValidateSet("runtime", "dev", "test", "all")]
    [string]$Target = "runtime",
    
    [Parameter(HelpMessage = "Remove volumes também?")]
    [switch]$RemoveVolumes = $false,
    
    [Parameter(HelpMessage = "Build sem cache (force rebuild)")]
    [switch]$NoCache = $false,
    
    [Parameter(HelpMessage = "Modo detached (background)")]
    [switch]$Detached = $false
)

# Cores para output
$Colors = @{
    Info    = "Cyan"
    Success = "Green"
    Warning = "Yellow"
    Error   = "Red"
}

function Write-Info {
    param([string]$Message)
    Write-Host "[ℹ️  INFO]  $Message" -ForegroundColor $Colors.Info
}

function Write-Success {
    param([string]$Message)
    Write-Host "[✅ OK]    $Message" -ForegroundColor $Colors.Success
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[⚠️  WARN]  $Message" -ForegroundColor $Colors.Warning
}

function Write-Error {
    param([string]$Message)
    Write-Host "[❌ ERROR] $Message" -ForegroundColor $Colors.Error
}

# ============================================================
# 1. PARAR CONTAINERS
# ============================================================
Write-Info "Parando containers..."
try {
    docker-compose down
    if ($RemoveVolumes) {
        Write-Info "Removendo volumes..."
        docker-compose down --volumes
    }
    Write-Success "Containers parados"
}
catch {
    Write-Warning "Nenhum container em execução"
}

# ============================================================
# 2. REMOVER IMAGES ANTIGAS
# ============================================================
Write-Info "Removendo images antigas..."

$images = @("evaonline:latest", "evaonline:dev", "evaonline:test")

foreach ($img in $images) {
    try {
        docker rmi $img -f 2>$null
        Write-Success "Removida: $img"
    }
    catch {
        Write-Warning "Imagem não encontrada: $img"
    }
}

# ============================================================
# 3. LIMPAR VOLUMES (se solicitado)
# ============================================================
if ($RemoveVolumes) {
    Write-Info "Limpando volumes..."
    try {
        docker volume prune -f
        Write-Success "Volumes limpos"
    }
    catch {
        Write-Warning "Erro ao limpar volumes"
    }
}

# ============================================================
# 4. LIMPAR SYSTEM (opcional)
# ============================================================
Write-Info "Limpando sistema Docker..."
try {
    docker system prune -f
    Write-Success "Sistema limpo"
}
catch {
    Write-Warning "Erro ao limpar sistema"
}

# ============================================================
# 5. RECONSTRUIR IMAGEM
# ============================================================
Write-Info "Reconstruindo imagem(s)..."

$buildFlags = @()
if ($NoCache) {
    $buildFlags += "--no-cache"
}

if ($Target -eq "all") {
    $targets = @("runtime", "dev", "test")
}
else {
    $targets = @($Target)
}

foreach ($t in $targets) {
    try {
        Write-Info "Build target: $t"
        $cmd = "docker build --target $t -t evaonline:$t $($buildFlags -join ' ') ."
        Invoke-Expression $cmd
        Write-Success "Build completo: evaonline:$t"
    }
    catch {
        Write-Error "Erro ao fazer build: $_"
        exit 1
    }
}

# ============================================================
# 6. INICIAR DOCKER-COMPOSE
# ============================================================
Write-Info "Iniciando docker-compose..."

try {
    if ($Detached) {
        docker-compose up -d
        Write-Success "Docker-compose iniciado em modo detached"
    }
    else {
        Write-Info "Aguarde alguns segundos..."
        docker-compose up
    }
}
catch {
    Write-Error "Erro ao iniciar docker-compose: $_"
    exit 1
}

# ============================================================
# 7. VERIFICAR STATUS
# ============================================================
Write-Info "Aguardando containers ficarem prontos..."
Start-Sleep -Seconds 5

try {
    $status = docker-compose ps
    Write-Success "Status dos containers:"
    Write-Host $status -ForegroundColor Green
}
catch {
    Write-Warning "Não foi possível obter status dos containers"
}

# ============================================================
# 8. VERIFICAR HEALTH
# ============================================================
Write-Info "Verificando saúde da aplicação..."

$maxRetries = 10
$retry = 0

while ($retry -lt $maxRetries) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/health" -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            Write-Success "Backend está respondendo ✅"
            break
        }
    }
    catch {
        $retry++
        if ($retry -lt $maxRetries) {
            Write-Warning "Tentativa $retry/$maxRetries..."
            Start-Sleep -Seconds 2
        }
    }
}

if ($retry -eq $maxRetries) {
    Write-Warning "Backend não respondeu após $maxRetries tentativas"
}

# ============================================================
# RESUMO
# ============================================================
Write-Host ""
Write-Host "════════════════════════════════════════════════════" -ForegroundColor Green
Write-Success "✨ Rebuild completo!"
Write-Host "════════════════════════════════════════════════════" -ForegroundColor Green

Write-Host ""
Write-Info "🌐 Acessos:"
Write-Host "   • Backend:  http://localhost:8000" -ForegroundColor Cyan
Write-Host "   • Frontend: http://localhost:8050" -ForegroundColor Cyan
Write-Host "   • Docs:     http://localhost:8000/api/docs" -ForegroundColor Cyan
Write-Host ""

Write-Info "📋 Próximos passos:"
Write-Host "   1. Abra http://localhost:8050 no browser" -ForegroundColor Cyan
Write-Host "   2. Verifique se o mapa carrega" -ForegroundColor Cyan
Write-Host "   3. Teste o botão de tradução (EN/PT)" -ForegroundColor Cyan
Write-Host "   4. Verifique se as logos aparecem" -ForegroundColor Cyan
Write-Host ""

Write-Info "📊 Logs:"
Write-Host "   docker-compose logs -f app     # Backend" -ForegroundColor Cyan
Write-Host "   docker-compose logs -f frontend # Frontend" -ForegroundColor Cyan
Write-Host ""

Write-Info "🛑 Para parar:"
Write-Host "   docker-compose down" -ForegroundColor Cyan
Write-Host ""
