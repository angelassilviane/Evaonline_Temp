#!/usr/bin/env python3
"""
Diagnóstico completo do projeto antes da limpeza de requirements.txt
"""

import os
import re
import sys
from collections import defaultdict
from pathlib import Path

print("🔍 DIAGNÓSTICO COMPLETO - EVAonline")
print("=" * 80)

# ============================================================================
# 1. VERIFICAR VENV
# ============================================================================

print("\n1️⃣ Verificando ambiente virtual...")

if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
    print(f"   ✅ Venv ativado: {sys.prefix}")
    print(f"   Python: {sys.version.split()[0]}")
else:
    print("   ❌ Venv NÃO está ativado!")
    sys.exit(1)

# ============================================================================
# 2. LISTAR ARQUIVOS requirements*.txt
# ============================================================================

print("\n2️⃣ Procurando arquivos requirements...")

req_files = list(Path(".").glob("requirements*.txt"))

if not req_files:
    print("   ❌ Nenhum arquivo requirements encontrado!")
    sys.exit(1)

print("   📄 Arquivos encontrados:")

for file in req_files:
    line_count = len(file.read_text().splitlines())
    size = file.stat().st_size / 1024
    print(f"      - {file.name} ({line_count} linhas, {size:.1f} KB)")

# ============================================================================
# 3. CONTAR PACOTES ÚNICOS
# ============================================================================

print("\n3️⃣ Analisando pacotes...")

all_packages = {}

for file in req_files:
    content = file.read_text().splitlines()
    
    for line in content:
        # Pular comentários e linhas vazias
        if line.startswith("#") or not line.strip() or line.startswith("-r"):
            continue
        
        # Extrair nome do pacote
        package_name = re.split(r">=|==|<=|<|>|~=|\[", line)[0].strip()
        
        if package_name and package_name not in all_packages:
            all_packages[package_name] = file.name

print(f"   📦 Total de pacotes únicos: {len(all_packages)}")

# ============================================================================
# 4. VERIFICAR pip freeze
# ============================================================================

print("\n4️⃣ Verificando instalações...")

try:
    import subprocess
    pip_freeze = subprocess.check_output([sys.executable, "-m", "pip", "freeze"], text=True)
    installed = {}
    
    for line in pip_freeze.splitlines():
        pkg = line.split("==")[0].split("@")[0]
        if pkg:
            installed[pkg] = True
    
    print(f"   ✅ {len(installed)} pacotes instalados em venv")
except Exception as e:
    print(f"   ⚠️  Não foi possível listar pacotes: {e}")
    installed = {}

# ============================================================================
# 5. IDENTIFICAR IMPORTS REAIS
# ============================================================================

print("\n5️⃣ Procurando imports no código...")

used_imports = {}
python_files = list(Path(".").rglob("*.py"))

# Filtrar arquivos que não queremos analisar
python_files = [
    f for f in python_files 
    if "__pycache__" not in str(f) and ".venv" not in str(f) and "tests/" not in str(f)
]

for file in python_files:
    try:
        content = file.read_text(encoding="utf-8", errors="ignore")
        
        # Extrair imports
        imports = re.findall(r"(?:^|\n)(?:from|import)\s+([^\s\.;]+)", content, re.MULTILINE)
        
        for imp in imports:
            top_level = imp.split(".")[0].lower()
            if top_level and top_level != "typing":
                used_imports[top_level] = True
    except Exception:
        pass

print(f"   ✅ {len(used_imports)} imports únicos encontrados no código")

# ============================================================================
# 6. COMPARAR: requirements vs imports
# ============================================================================

print("\n6️⃣ Comparando requirements.txt com imports reais...")

# Mapeamentos especiais
mappings = {
    "psycopg2-binary": "psycopg2",
    "python-multipart": "multipart",
    "PyJWT": "jwt",
    "python-dotenv": "dotenv",
    "sqlalchemy-utils": "sqlalchemy_utils",
    "email-validator": "email_validator",
    "dataclass-wizard": "dataclass_wizard",
    "python-dateutil": "dateutil",
    "detect-secrets": "detect_secrets",
    "flake8-bugbear": "flake8",
    "flake8-comprehensions": "flake8",
    "flake8-simplify": "flake8",
    "types-requests": "requests",
    "types-redis": "redis",
    "types-pytz": "pytz",
    "types-python-dateutil": "dateutil",
    "types-Flask": "flask",
    "types-PyYAML": "yaml",
    "prometheus-flask-exporter": "prometheus_flask_exporter",
    "prometheus-fastapi-instrumentator": "prometheus_fastapi_instrumentator",
    "mkdocs-material": "mkdocs",
    "mkdocstrings": "mkdocs",
    "pydoc-markdown": "pydoc_markdown",
    "et_xmlfile": "openpyxl",
    "dash-bootstrap-components": "dash_bootstrap_components",
    "dash-leaflet": "dash_leaflet",
    "openmeteo_requests": "openmeteo",
    "openmeteo_sdk": "openmeteo",
    "noaa-sdk": "noaa",
    "cads-api-client": "cads",
    "timezonefinderL": "timezonefinder",
    "py-spy": "spy",
    "memory-profiler": "memory_profiler",
    "line-profiler": "line_profiler",
    "pytest-cov": "pytest",
    "pytest-asyncio": "pytest",
    "pytest-mock": "pytest",
    "pytest-timeout": "pytest",
    "pytest-xdist": "pytest",
    "pytest-benchmark": "pytest",
    "pytest-html": "pytest",
    "pytest-sugar": "pytest",
    "pre-commit": "pre_commit",
    "ipdb": "ipdb",
    "ipython": "ipython",
    "platformdirs": "platformdirs",
    "importlib-metadata": "importlib_metadata",
}

not_used = []
used_count = 0

for pkg in sorted(all_packages.keys()):
    search_name = mappings.get(pkg, pkg).lower()
    
    if search_name in used_imports:
        used_count += 1
    else:
        not_used.append(pkg)

print(f"   ✅ {used_count} pacotes USADOS no código")
print(f"   ❌ {len(not_used)} pacotes POTENCIALMENTE não usados")

if 0 < len(not_used) < 40:
    print("\n   Pacotes não usados:")
    for pkg in not_used:
        print(f"      - {pkg}")

# ============================================================================
# 7. VERIFICAR FORMATOS
# ============================================================================

print("\n7️⃣ Verificando formatos de dados utilizados...")

formats = {
    "CSV": 0,
    "NetCDF": 0,
    "JSON": 0,
    "Parquet": 0,
    "Excel": 0,
}

for file in python_files:
    try:
        content = file.read_text(encoding="utf-8", errors="ignore")
        
        if re.search(r"\.csv|pd\.read_csv|\.to_csv", content):
            formats["CSV"] += 1
        if re.search(r"netCDF|xr\.open_dataset|\.nc", content):
            formats["NetCDF"] += 1
        if re.search(r"json\.load|\.to_json", content):
            formats["JSON"] += 1
        if re.search(r"parquet|read_parquet|to_parquet", content):
            formats["Parquet"] += 1
        if re.search(r"excel|openpyxl|\.xlsx", content):
            formats["Excel"] += 1
    except Exception:
        pass

print("   Formatos encontrados:")
for fmt in sorted(formats.keys()):
    if formats[fmt] > 0:
        print(f"      ✅ {fmt}: {formats[fmt]} arquivo(s)")
    else:
        print(f"      ❌ {fmt}: não usado")

# ============================================================================
# 8. RELATÓRIO FINAL
# ============================================================================

print("\n" + "=" * 80)
print("📊 RESUMO DO DIAGNÓSTICO")
print("=" * 80)

print("\n📋 ARQUIVOS requirements:")
for file in req_files:
    print(f"   - {file.name}")

print("\n📦 ESTATÍSTICAS:")
print(f"   Total de pacotes: {len(all_packages)}")
print(f"   Pacotes usados: {used_count}")
print(f"   Pacotes não usados: {len(not_used)}")
print(f"   Taxa de uso: {(used_count / len(all_packages) * 100):.1f}%")

print("\n💾 PRÓXIMAS AÇÕES:")
print("   1. Revisar pacotes não usados")
print("   2. Reorganizar em requirements/ com base.txt, production.txt, development.txt")
print("   3. Remover netCDF4, xarray, cdsapi (não usamos)")
print("   4. Testar que tudo funciona")

print("\n")
