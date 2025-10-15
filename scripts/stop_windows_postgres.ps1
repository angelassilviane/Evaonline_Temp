# ============================================
# Script para Parar PostgreSQL do Windows
# ============================================
# Execute este script como ADMINISTRADOR
# Clique com botão direito → "Executar como Administrador"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Parando PostgreSQL do Windows" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Verifica se está rodando como administrador
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "❌ ERRO: Este script precisa ser executado como ADMINISTRADOR!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Como executar:" -ForegroundColor Yellow
    Write-Host "1. Clique com botão direito neste arquivo" -ForegroundColor Yellow
    Write-Host "2. Escolha 'Executar com PowerShell' ou 'Executar como Administrador'" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Ou no PowerShell Admin:" -ForegroundColor Yellow
    Write-Host "   Stop-Service -Name 'postgresql-x64-16' -Force" -ForegroundColor Cyan
    Write-Host ""
    Pause
    exit 1
}

Write-Host "✅ Executando como Administrador" -ForegroundColor Green
Write-Host ""

# Lista serviços PostgreSQL
Write-Host "📋 Serviços PostgreSQL encontrados:" -ForegroundColor Yellow
Get-Service -Name "postgresql*" | Format-Table -AutoSize
Write-Host ""

# Para o serviço principal
$serviceName = "postgresql-x64-16"

Write-Host "⏹️  Parando serviço: $serviceName" -ForegroundColor Yellow

try {
    Stop-Service -Name $serviceName -Force -ErrorAction Stop
    Write-Host "✅ Serviço parado com sucesso!" -ForegroundColor Green
}
catch {
    Write-Host "❌ Erro ao parar serviço: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "O serviço pode já estar parado ou não existir." -ForegroundColor Yellow
}

Write-Host ""

# Verifica status
Write-Host "📊 Status atual do serviço:" -ForegroundColor Yellow
Get-Service -Name $serviceName | Format-Table -AutoSize

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan

# Pergunta se quer desabilitar inicialização automática
Write-Host ""
$response = Read-Host "Deseja desabilitar a inicialização automática? (S/N)"

if ($response -eq "S" -or $response -eq "s") {
    try {
        Set-Service -Name $serviceName -StartupType Manual
        Write-Host "✅ Inicialização automática desabilitada!" -ForegroundColor Green
        Write-Host "   O serviço não iniciará automaticamente no boot." -ForegroundColor Gray
    }
    catch {
        Write-Host "❌ Erro ao alterar tipo de inicialização: $_" -ForegroundColor Red
    }
}
else {
    Write-Host "⏭️  Inicialização automática mantida." -ForegroundColor Gray
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "✅ Concluído!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Verifica processos PostgreSQL
$pgProcesses = Get-Process -Name "postgres*" -ErrorAction SilentlyContinue
if ($pgProcesses) {
    Write-Host "⚠️  ATENÇÃO: Ainda há processos PostgreSQL rodando:" -ForegroundColor Yellow
    $pgProcesses | Format-Table -Property Id, ProcessName, CPU, WorkingSet -AutoSize
    Write-Host ""
    Write-Host "Pode ser necessário reiniciar o computador se os processos não pararem." -ForegroundColor Yellow
}
else {
    Write-Host "✅ Nenhum processo PostgreSQL rodando" -ForegroundColor Green
}

Write-Host ""
Pause
