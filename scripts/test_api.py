#!/usr/bin/env python
"""Testar API FastAPI"""

import json

import requests

BASE_URL = "http://localhost:8000"

try:
    print("🧪 Testando API FastAPI...\n")
    
    # Test 1: Health Check
    print("1️⃣  Health Check")
    resp = requests.get(f"{BASE_URL}/health")
    print(f"   Status: {resp.status_code}")
    print(f"   Response: {resp.json()}\n")
    
    # Test 2: API Docs
    print("2️⃣  Documentação OpenAPI")
    resp = requests.get(f"{BASE_URL}/docs")
    print(f"   Status: {resp.status_code} - Swagger UI disponível\n")
    
    # Test 3: API Versioning
    print("3️⃣  API Info")
    resp = requests.get(f"{BASE_URL}/api/v1/health")
    print(f"   Status: {resp.status_code}")
    if resp.status_code == 200:
        print(f"   Response: {resp.json()}\n")
    
    # Test 4: Database connection (se houver endpoint)
    print("4️⃣  Verificando endpoints disponíveis")
    resp = requests.get(f"{BASE_URL}/openapi.json")
    if resp.status_code == 200:
        openapi = resp.json()
        endpoints = list(openapi.get("paths", {}).keys())
        print(f"   Total de endpoints: {len(endpoints)}")
        print(f"   Primeiros 10 endpoints:")
        for endpoint in endpoints[:10]:
            print(f"     - {endpoint}")
    
    print("\n✅ API está funcionando!")
    print(f"\n📚 Acessar documentação: {BASE_URL}/docs")

except requests.exceptions.ConnectionError:
    print("❌ Erro: Não conseguir conectar à API")
    print(f"   Verifique se a API está rodando em {BASE_URL}")
except Exception as e:
    print(f"❌ Erro: {e}")
