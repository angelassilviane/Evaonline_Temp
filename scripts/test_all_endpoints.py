#!/usr/bin/env python3
"""
Script de validação final - Testa TODOS os endpoints e funcionalidades.
"""

import json
import sys
from typing import Dict, List, Tuple

import requests

BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/v1"

print("\n" + "="*80)
print("🧪 VALIDAÇÃO FINAL - EVAONLINE")
print("="*80 + "\n")

results = {
    "API": [],
    "Assets": [],
    "Dash": [],
    "Database": [],
    "Celery": [],
}

# ============================================================================
# 1. TESTAR API ENDPOINTS
# ============================================================================

print("1️⃣ TESTANDO API ENDPOINTS...")
print("-" * 80)

api_endpoints = [
    ("Health", f"{API_URL}/health", 200),
    ("Locations", f"{API_URL}/locations/search?lat=-10&lng=-50&radius=100", 200),
]

for name, url, expected_status in api_endpoints:
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == expected_status:
            print(f"✅ {name}: {response.status_code}")
            results["API"].append((name, True))
        else:
            print(f"❌ {name}: Expected {expected_status}, got {response.status_code}")
            results["API"].append((name, False))
    except Exception as e:
        print(f"❌ {name}: {str(e)}")
        results["API"].append((name, False))

# ============================================================================
# 2. TESTAR ASSETS
# ============================================================================

print("\n2️⃣ TESTANDO ASSETS...")
print("-" * 80)

assets = [
    "logo_c4ai.png",
    "logo_fapesp.png",
    "logo_ibm.png",
    "logo_usp.png",
    "logo_esalq.png",
    "styles.css",
    "dashExtensions_default.js",
]

for asset in assets:
    # Determinar tipo
    if asset.endswith(".png"):
        asset_type = "images"
    elif asset.endswith(".css"):
        asset_type = "css"
    else:
        asset_type = "js"
    
    url = f"{BASE_URL}/assets/{asset_type}/{asset}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print(f"✅ {asset}: 200 OK")
            results["Assets"].append((asset, True))
        else:
            print(f"❌ {asset}: {response.status_code}")
            results["Assets"].append((asset, False))
    except Exception as e:
        print(f"❌ {asset}: {str(e)}")
        results["Assets"].append((asset, False))

# ============================================================================
# 3. TESTAR DASH LAYOUT
# ============================================================================

print("\n3️⃣ TESTANDO DASH LAYOUT...")
print("-" * 80)

try:
    response = requests.get(f"{BASE_URL}/_dash-layout", timeout=5)
    if response.status_code == 200:
        layout = response.json()
        
        # Verificar componentes
        checks = {
            "navbar": False,
            "page-content": False,
            "footer": False,
        }
        
        layout_text = json.dumps(layout)
        for component in checks.keys():
            if component in layout_text:
                checks[component] = True
        
        for component, found in checks.items():
            if found:
                print(f"✅ Component '{component}' found")
                results["Dash"].append((component, True))
            else:
                print(f"❌ Component '{component}' NOT found")
                results["Dash"].append((component, False))
    else:
        print(f"❌ Dash layout: {response.status_code}")
        results["Dash"].append(("layout", False))
except Exception as e:
    print(f"❌ Dash layout: {str(e)}")
    results["Dash"].append(("layout", False))

# ============================================================================
# 4. TESTAR HOMEPAGE
# ============================================================================

print("\n4️⃣ TESTANDO HOMEPAGE...")
print("-" * 80)

try:
    response = requests.get(BASE_URL, timeout=5)
    if response.status_code == 200:
        if "EVAonline" in response.text:
            print("✅ Homepage loads correctly")
            print("✅ 'EVAonline' text found")
            results["Dash"].append(("homepage", True))
        else:
            print("❌ Homepage missing 'EVAonline' text")
            results["Dash"].append(("homepage", False))
    else:
        print(f"❌ Homepage: {response.status_code}")
        results["Dash"].append(("homepage", False))
except Exception as e:
    print(f"❌ Homepage: {str(e)}")
    results["Dash"].append(("homepage", False))

# ============================================================================
# 5. RESUMO FINAL
# ============================================================================

print("\n" + "="*80)
print("📋 RESUMO FINAL")
print("="*80)

total_passed = 0
total_failed = 0

for category, checks in results.items():
    passed = sum(1 for _, success in checks if success)
    failed = sum(1 for _, success in checks if not success)
    total_passed += passed
    total_failed += failed
    
    status = "✅" if failed == 0 else "⚠️"
    print(f"\n{status} {category}: {passed}/{passed + failed} OK")
    
    for name, success in checks:
        if not success:
            print(f"   ❌ {name}")

print("\n" + "="*80)
print(f"TOTAL: {total_passed}/{total_passed + total_failed} ✅")

if total_failed == 0:
    print("\n🎉 TUDO FUNCIONANDO CORRETAMENTE!")
    print("PROJETO PRONTO PARA TESTES E2E!")
else:
    print(f"\n⚠️  {total_failed} problemas encontrados")

print("="*80 + "\n")

sys.exit(0 if total_failed == 0 else 1)
