#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Diagnóstico completo do projeto antes da limpeza
#>

Write-Host "🔍 DIAGNÓSTICO COMPLETO - EVAonline" -ForegroundColor Cyan
Write-Host "="*80

# ============================================================================
# 1. VERIFICAR AMBIENTE VIRTUAL
# ============================================================================

Write-Host "`n1️⃣ Verificando ambiente virtual..." -ForegroundColor Yellow

if ($env:VIRTUAL_ENV) {
    Write-Host "   ✅ Venv ativado: $env:VIRTUAL_ENV" -ForegroundColor Green
    Write-Host "   Python: $(python --version)" -ForegroundColor Cyan
}
else {
    Write-Host "   ❌ Venv NÃO está ativado!" -ForegroundColor Red
    Write-Host "   Execute: .\.venv\Scripts\Activate.ps1" -ForegroundColor Yellow
    exit 1
}

# ============================================================================
# 2. LISTAR ARQUIVOS requirements*.txt
# ============================================================================

Write-Host "`n2️⃣ Procurando arquivos requirements..." -ForegroundColor Yellow

$reqFiles = Get-ChildItem -Filter "requirements*.txt" -ErrorAction SilentlyContinue

if ($reqFiles.Count -eq 0) {
    Write-Host "   ❌ Nenhum arquivo requirements encontrado!" -ForegroundColor Red
    exit 1
}

Write-Host "   📄 Arquivos encontrados:" -ForegroundColor Green

foreach ($file in $reqFiles) {
    $lineCount = (Get-Content $file.FullName | Measure-Object -Line).Lines
    $size = "{0:N2}" -f ($file.Length / 1KB)
    Write-Host "      - $($file.Name) ($lineCount linhas, $size KB)"
}

# ============================================================================
# 3. CONTAR PACOTES ÚNICOS
# ============================================================================

Write-Host "`n3️⃣ Analisando pacotes..." -ForegroundColor Yellow

$allPackages = @{}

foreach ($file in $reqFiles) {
    $content = Get-Content $file.FullName | Where-Object {
        $_ -notmatch "^#" -and $_ -notmatch "^\s*$" -and $_ -notmatch "^-r "
    }
    
    foreach ($line in $content) {
        $packageName = ($line -split ">=|==|<=|<|>|~=|\[")[0].Trim()
        if ($packageName -and -not $allPackages[$packageName]) {
            $allPackages[$packageName] = $file.Name
        }
    }
}

Write-Host "   📦 Total de pacotes únicos: $($allPackages.Count)" -ForegroundColor Green

# ============================================================================
# 4. VERIFICAR pip freeze vs requirements.txt
# ============================================================================

Write-Host "`n4️⃣ Verificando instalações..." -ForegroundColor Yellow

$installed = @{}
$pipFreeze = pip freeze 2>$null

if ($pipFreeze) {
    foreach ($line in $pipFreeze) {
        $pkg = ($line -split "==|@")[0]
        if ($pkg) {
            $installed[$pkg] = $true
        }
    }
    Write-Host "   ✅ $($installed.Count) pacotes instalados em venv" -ForegroundColor Green
}
else {
    Write-Host "   ⚠️  Não foi possível listar pacotes instalados" -ForegroundColor Yellow
}

# ============================================================================
# 5. IDENTIFICAR PACOTES NÃO USADOS
# ============================================================================

Write-Host "`n5️⃣ Procurando imports no código..." -ForegroundColor Yellow

$pythonFiles = Get-ChildItem -Recurse -Filter "*.py" -ErrorAction SilentlyContinue | 
Where-Object { $_.FullName -notmatch "__pycache__|\.venv|tests" }

$usedImports = @{}

foreach ($file in $pythonFiles) {
    try {
        $content = Get-Content $file.FullName -Raw -ErrorAction SilentlyContinue
        
        # Extrair imports
        $importMatches = [regex]::Matches($content, '(?:^|\n)(?:from|import)\s+([^\s\.;]+)')
        
        foreach ($match in $importMatches) {
            $importName = ($match.Groups[1].Value -split "\.")[0].ToLower()
            if ($importName -and $importName -ne "typing") {
                $usedImports[$importName] = $true
            }
        }
    }
    catch {
        # Ignorar erros
    }
}

Write-Host "   ✅ $($usedImports.Count) imports únicos encontrados no código" -ForegroundColor Green

# ============================================================================
# 6. COMPARAR: requirements.txt vs imports reais
# ============================================================================

Write-Host "`n6️⃣ Comparando requirements.txt com imports reais..." -ForegroundColor Yellow

$notUsed = @()
$used = 0

# Mapeamentos especiais (package name ≠ import name)
$mappings = @{
    "psycopg2-binary"                   = "psycopg2"
    "python-multipart"                  = "multipart"
    "PyJWT"                             = "jwt"
    "python-dotenv"                     = "dotenv"
    "sqlalchemy-utils"                  = "sqlalchemy_utils"
    "email-validator"                   = "email_validator"
    "dataclass-wizard"                  = "dataclass_wizard"
    "python-dateutil"                   = "dateutil"
    "detect-secrets"                    = "detect_secrets"
    "flake8-bugbear"                    = "flake8"
    "flake8-comprehensions"             = "flake8"
    "flake8-simplify"                   = "flake8"
    "types-requests"                    = "requests"
    "types-redis"                       = "redis"
    "types-pytz"                        = "pytz"
    "types-python-dateutil"             = "dateutil"
    "types-Flask"                       = "flask"
    "types-PyYAML"                      = "yaml"
    "prometheus-flask-exporter"         = "prometheus_flask_exporter"
    "prometheus-fastapi-instrumentator" = "prometheus_fastapi_instrumentator"
    "mkdocs-material"                   = "mkdocs"
    "mkdocstrings"                      = "mkdocs"
    "pydoc-markdown"                    = "pydoc_markdown"
    "et_xmlfile"                        = "openpyxl"
    "dash-bootstrap-components"         = "dash_bootstrap_components"
    "dash-leaflet"                      = "dash_leaflet"
    "openmeteo_requests"                = "openmeteo"
    "openmeteo_sdk"                     = "openmeteo"
    "noaa-sdk"                          = "noaa"
    "cads-api-client"                   = "cads"
    "timezonefinderL"                   = "timezonefinder"
    "py-spy"                            = "spy"
    "memory-profiler"                   = "memory_profiler"
    "line-profiler"                     = "line_profiler"
    "pytest-cov"                        = "pytest"
    "pytest-asyncio"                    = "pytest"
    "pytest-mock"                       = "pytest"
    "pytest-timeout"                    = "pytest"
    "pytest-xdist"                      = "pytest"
    "pytest-benchmark"                  = "pytest"
    "pytest-html"                       = "pytest"
    "pytest-sugar"                      = "pytest"
    "pre-commit"                        = "pre_commit"
    "ipdb"                              = "ipdb"
    "ipython"                           = "ipython"
    "py-spy"                            = "py_spy"
    "memory-profiler"                   = "memory_profiler"
    "line-profiler"                     = "line_profiler"
    "platformdirs"                      = "platformdirs"
    "importlib-metadata"                = "importlib_metadata"
}

foreach ($pkg in $allPackages.Keys | Sort-Object) {
    $searchName = if ($mappings[$pkg]) { $mappings[$pkg].ToLower() } else { $pkg.ToLower() }
    
    if ($usedImports[$searchName]) {
        $used++
    }
    else {
        $notUsed += $pkg
    }
}

Write-Host "   ✅ $used pacotes USADOS no código" -ForegroundColor Green
Write-Host "   ❌ $($notUsed.Count) pacotes POTENCIALMENTE não usados" -ForegroundColor Red

if ($notUsed.Count -gt 0 -and $notUsed.Count -lt 40) {
    Write-Host "`n   Pacotes não usados:" -ForegroundColor Yellow
    foreach ($pkg in $notUsed | Sort-Object) {
        Write-Host "      - $pkg"
    }
}

# ============================================================================
# 7. VERIFICAR FORMATOS DE DADOS USADOS
# ============================================================================

Write-Host "`n7️⃣ Verificando formatos de dados utilizados..." -ForegroundColor Yellow

$formats = @{
    "CSV"     = 0
    "NetCDF"  = 0
    "JSON"    = 0
    "Parquet" = 0
    "Excel"   = 0
}

foreach ($file in $pythonFiles) {
    $content = Get-Content $file.FullName -Raw -ErrorAction SilentlyContinue
    
    if ($content -match "\.csv|pd\.read_csv|\.to_csv") { $formats["CSV"]++ }
    if ($content -match "netCDF|xr\.open_dataset") { $formats["NetCDF"]++ }
    if ($content -match "json\.load|\.to_json") { $formats["JSON"]++ }
    if ($content -match "parquet|read_parquet|to_parquet") { $formats["Parquet"]++ }
    if ($content -match "excel|openpyxl|\.xlsx") { $formats["Excel"]++ }
}

Write-Host "   Formatos encontrados:" -ForegroundColor Green
foreach ($fmt in $formats.Keys | Sort-Object) {
    if ($formats[$fmt] -gt 0) {
        Write-Host "      ✅ $fmt: $($formats[$fmt]) arquivo(s)"
    }
    else {
        Write-Host "      ❌ $fmt: não usado"
    }
}

# ============================================================================
# 8. RELATÓRIO FINAL
# ============================================================================

Write-Host "`n" + "="*80 -ForegroundColor Cyan
Write-Host "📊 RESUMO DO DIAGNÓSTICO" -ForegroundColor Green
Write-Host "="*80

Write-Host "`n📋 ARQUIVOS requirements:" -ForegroundColor Yellow
foreach ($file in $reqFiles) {
    Write-Host "   - $($file.Name)"
}

Write-Host "`n📦 ESTATÍSTICAS:" -ForegroundColor Yellow
Write-Host "   Total de pacotes: $($allPackages.Count)"
Write-Host "   Pacotes usados: $used"
Write-Host "   Pacotes não usados: $($notUsed.Count)"
Write-Host "   Taxa de uso: $(([math]::Round($used/$allPackages.Count*100, 1)))%"

Write-Host "`n💾 PRÓXIMAS AÇÕES:" -ForegroundColor Cyan
Write-Host "   1. Revisar pacotes não usados"
Write-Host "   2. Remover netCDF4, xarray, cdsapi (não usamos)"
Write-Host "   3. Reorganizar em requirements/ com base.txt, production.txt, development.txt"
Write-Host "   4. Testar que tudo funciona"

Write-Host "`n"
