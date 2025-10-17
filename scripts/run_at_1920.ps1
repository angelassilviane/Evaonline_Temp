# Script para agendar continuação às 19:20
# Salvar como: run_at_1920.ps1

$targetTime = Get-Date -Hour 19 -Minute 20 -Second 0
$now = Get-Date

if ($now -lt $targetTime) {
    $waitSeconds = ($targetTime - $now).TotalSeconds
    Write-Host "⏰ Agendado para 19:20 (em $([math]::Round($waitSeconds/60, 1)) minutos)" -ForegroundColor Yellow
    Write-Host "💤 Aguardando..." -ForegroundColor Cyan
    Start-Sleep -Seconds $waitSeconds
}

Write-Host "`n🚀 Iniciando processamento às $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Green
Write-Host "📊 Continuando de onde parou (4.831 cidades já processadas)" -ForegroundColor Cyan
Write-Host "🎯 Meta: completar 9.500 cidades hoje`n" -ForegroundColor Green

# Executar script Python
python scripts/continue_elevation_batch.py --batch 4669

Write-Host "`n✅ Processamento concluído às $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Green
Write-Host "📊 Verificar progresso com:" -ForegroundColor Cyan
Write-Host "   python scripts/add_elevation_batch.py --check-progress`n" -ForegroundColor White
