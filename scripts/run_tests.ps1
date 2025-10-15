# ===========================================
# TEST RUNNER SCRIPT - EVAonline
# ===========================================
# Script para executar diferentes suítes de testes

Write-Host "================================" -ForegroundColor Cyan
Write-Host "  EVAonline - Test Runner" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Verificar se estamos no diretório correto
if (-Not (Test-Path "backend")) {
    Write-Host "❌ Erro: Execute este script da raiz do projeto!" -ForegroundColor Red
    exit 1
}

# Função para exibir menu
function Show-Menu {
    Write-Host "Escolha qual tipo de teste executar:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  1. 🧪 Testes Unitários" -ForegroundColor Green
    Write-Host "  2. 🔗 Testes de Integração (Docker)" -ForegroundColor Green
    Write-Host "  3. 🌐 Testes de API" -ForegroundColor Green
    Write-Host "  4. 🚀 Todos os testes" -ForegroundColor Green
    Write-Host "  5. 📊 Testes com Coverage" -ForegroundColor Green
    Write-Host "  6. 🐢 Testes Lentos (Slow)" -ForegroundColor Green
    Write-Host "  7. 💨 Smoke Tests" -ForegroundColor Green
    Write-Host "  8. 🔍 Verificar configuração pytest" -ForegroundColor Blue
    Write-Host "  9. 🧹 Limpar cache de testes" -ForegroundColor Blue
    Write-Host "  0. ❌ Sair" -ForegroundColor Red
    Write-Host ""
}

# Função para rodar testes unitários
function Run-UnitTests {
    Write-Host "🧪 Executando testes unitários..." -ForegroundColor Cyan
    pytest tests/ -m "unit" -v --tb=short
}

# Função para rodar testes de integração
function Run-IntegrationTests {
    Write-Host "🔗 Executando testes de integração..." -ForegroundColor Cyan
    Write-Host "⚠️  Certifique-se de que Docker está rodando!" -ForegroundColor Yellow
    Write-Host ""
    
    # Verificar se serviços Docker estão rodando
    docker ps | Select-String "postgres" | Out-Null
    $postgresRunning = $?
    
    docker ps | Select-String "redis" | Out-Null
    $redisRunning = $?
    
    if (-Not $postgresRunning -Or -Not $redisRunning) {
        Write-Host "⚠️  Serviços Docker não estão rodando!" -ForegroundColor Yellow
        Write-Host "   Deseja iniciar com docker-compose? (S/N)" -ForegroundColor Yellow
        $response = Read-Host
        
        if ($response -eq "S" -Or $response -eq "s") {
            Write-Host "🐳 Iniciando serviços Docker..." -ForegroundColor Cyan
            docker-compose up -d postgres redis
            Start-Sleep -Seconds 5
        }
        else {
            Write-Host "❌ Cancelando testes de integração" -ForegroundColor Red
            return
        }
    }
    
    pytest tests/integration/ -v --tb=short
}

# Função para rodar testes de API
function Run-APITests {
    Write-Host "🌐 Executando testes de API..." -ForegroundColor Cyan
    pytest tests/api/ -v --tb=short
}

# Função para rodar todos os testes
function Run-AllTests {
    Write-Host "🚀 Executando TODOS os testes..." -ForegroundColor Cyan
    pytest tests/ -v --tb=short
}

# Função para rodar com coverage
function Run-TestsWithCoverage {
    Write-Host "📊 Executando testes com coverage..." -ForegroundColor Cyan
    pytest tests/ -v `
        --cov=backend `
        --cov-report=html `
        --cov-report=term-missing `
        --tb=short
    
    Write-Host ""
    Write-Host "✅ Relatório de coverage gerado em: htmlcov/index.html" -ForegroundColor Green
    
    # Perguntar se quer abrir o relatório
    Write-Host "Deseja abrir o relatório de coverage? (S/N)" -ForegroundColor Yellow
    $response = Read-Host
    
    if ($response -eq "S" -Or $response -eq "s") {
        Start-Process "htmlcov/index.html"
    }
}

# Função para rodar testes lentos
function Run-SlowTests {
    Write-Host "🐢 Executando testes lentos..." -ForegroundColor Cyan
    pytest tests/ -m "slow" -v --tb=short
}

# Função para rodar smoke tests
function Run-SmokeTests {
    Write-Host "💨 Executando smoke tests..." -ForegroundColor Cyan
    pytest tests/ -m "smoke" -v --tb=short
}

# Função para verificar configuração
function Check-PytestConfig {
    Write-Host "🔍 Verificando configuração do pytest..." -ForegroundColor Cyan
    Write-Host ""
    
    if (Test-Path "pytest.ini") {
        Write-Host "✅ pytest.ini encontrado" -ForegroundColor Green
    }
    else {
        Write-Host "❌ pytest.ini não encontrado!" -ForegroundColor Red
    }
    
    Write-Host ""
    Write-Host "Marcadores registrados:" -ForegroundColor Yellow
    pytest --markers
    
    Write-Host ""
    Write-Host "Configuração atual:" -ForegroundColor Yellow
    pytest --co -q tests/ | Select-Object -First 10
}

# Função para limpar cache
function Clean-TestCache {
    Write-Host "🧹 Limpando cache de testes..." -ForegroundColor Cyan
    
    if (Test-Path ".pytest_cache") {
        Remove-Item -Recurse -Force ".pytest_cache"
        Write-Host "✅ .pytest_cache removido" -ForegroundColor Green
    }
    
    if (Test-Path "htmlcov") {
        Remove-Item -Recurse -Force "htmlcov"
        Write-Host "✅ htmlcov removido" -ForegroundColor Green
    }
    
    if (Test-Path ".coverage") {
        Remove-Item -Force ".coverage"
        Write-Host "✅ .coverage removido" -ForegroundColor Green
    }
    
    if (Test-Path "coverage.xml") {
        Remove-Item -Force "coverage.xml"
        Write-Host "✅ coverage.xml removido" -ForegroundColor Green
    }
    
    Write-Host "✅ Cache limpo com sucesso!" -ForegroundColor Green
}

# Loop principal
while ($true) {
    Show-Menu
    $choice = Read-Host "Digite sua escolha"
    Write-Host ""
    
    switch ($choice) {
        "1" { Run-UnitTests }
        "2" { Run-IntegrationTests }
        "3" { Run-APITests }
        "4" { Run-AllTests }
        "5" { Run-TestsWithCoverage }
        "6" { Run-SlowTests }
        "7" { Run-SmokeTests }
        "8" { Check-PytestConfig }
        "9" { Clean-TestCache }
        "0" {
            Write-Host "👋 Saindo..." -ForegroundColor Cyan
            exit 0
        }
        default {
            Write-Host "❌ Opção inválida!" -ForegroundColor Red
        }
    }
    
    Write-Host ""
    Write-Host "Pressione qualquer tecla para continuar..." -ForegroundColor Gray
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    Clear-Host
}
