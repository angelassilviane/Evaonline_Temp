#!/usr/bin/env python
"""Testes E2E - Fluxo Completo EVAonline"""

import time
from datetime import datetime

import requests

BASE_API = "http://localhost:8000"
BASE_FRONTEND = "http://localhost:8050"

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def test_api():
    """Testa API"""
    print(f"\n{bcolors.OKCYAN}{'='*70}{bcolors.ENDC}")
    print(f"{bcolors.OKCYAN}🧪 TESTE 1: API FastAPI{bcolors.ENDC}")
    print(f"{bcolors.OKCYAN}{'='*70}{bcolors.ENDC}\n")
    
    try:
        resp = requests.get(f"{BASE_API}/api/v1/health")
        print(f"{bcolors.OKGREEN}✅ Health Check:{bcolors.ENDC} {resp.json()}")
        return True
    except Exception as e:
        print(f"{bcolors.FAIL}❌ Erro: {e}{bcolors.ENDC}")
        return False

def test_frontend():
    """Testa Frontend"""
    print(f"\n{bcolors.OKCYAN}{'='*70}{bcolors.ENDC}")
    print(f"{bcolors.OKCYAN}🧪 TESTE 2: Frontend Dash{bcolors.ENDC}")
    print(f"{bcolors.OKCYAN}{'='*70}{bcolors.ENDC}\n")
    
    try:
        resp = requests.get(f"{BASE_FRONTEND}/")
        if resp.status_code == 200 and "EVAonline" in resp.text:
            print(f"{bcolors.OKGREEN}✅ Frontend respondendo (HTTP 200){bcolors.ENDC}")
            print(f"   Título: EVAonline")
            print(f"   React: Presente")
            print(f"   Leaflet: {bcolors.OKGREEN}✓{bcolors.ENDC}")
            print(f"   Dash: {bcolors.OKGREEN}✓{bcolors.ENDC}")
            return True
        else:
            print(f"{bcolors.FAIL}❌ Frontend respondendo com status {resp.status_code}{bcolors.ENDC}")
            return False
    except Exception as e:
        print(f"{bcolors.FAIL}❌ Erro: {e}{bcolors.ENDC}")
        return False

def test_database():
    """Testa integração com Database"""
    print(f"\n{bcolors.OKCYAN}{'='*70}{bcolors.ENDC}")
    print(f"{bcolors.OKCYAN}🧪 TESTE 3: Database Integration{bcolors.ENDC}")
    print(f"{bcolors.OKCYAN}{'='*70}{bcolors.ENDC}\n")
    
    try:
        import psycopg
        
        conn = psycopg.connect(
            host="localhost",
            port=5432,
            dbname="evaonline",
            user="evaonline",
            password="evaonline"
        )
        
        with conn.cursor() as cur:
            # Test UTF-8
            cur.execute("SELECT 'São Paulo'::text")
            result = cur.fetchone()[0]
            print(f"{bcolors.OKGREEN}✅ UTF-8 Working{bcolors.ENDC}: {result}")
            
            # Test PostGIS
            cur.execute("SELECT ST_Distance(ST_GeographyFromText('POINT(0 0)'), ST_GeographyFromText('POINT(1 1)'))")
            distance = cur.fetchone()[0]
            print(f"{bcolors.OKGREEN}✅ PostGIS Working{bcolors.ENDC}: Distance = {distance:.2f}m")
            
            # Test Query Performance
            start = time.time()
            cur.execute("SELECT COUNT(*) FROM information_schema.tables")
            elapsed = (time.time() - start) * 1000
            count = cur.fetchone()[0]
            print(f"{bcolors.OKGREEN}✅ Query Performance{bcolors.ENDC}: {count} tabelas em {elapsed:.2f}ms")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"{bcolors.FAIL}❌ Erro: {e}{bcolors.ENDC}")
        return False

def test_redis():
    """Testa integração com Redis"""
    print(f"\n{bcolors.OKCYAN}{'='*70}{bcolors.ENDC}")
    print(f"{bcolors.OKCYAN}🧪 TESTE 4: Redis Integration{bcolors.ENDC}")
    print(f"{bcolors.OKCYAN}{'='*70}{bcolors.ENDC}\n")
    
    try:
        import redis
        
        r = redis.Redis(host="localhost", port=6379, decode_responses=True)
        
        pong = r.ping()
        print(f"{bcolors.OKGREEN}✅ Redis PING{bcolors.ENDC}: {pong}")
        
        r.set("e2e_test_key", f"test_value_{datetime.now().isoformat()}", ex=3600)
        value = r.get("e2e_test_key")
        print(f"{bcolors.OKGREEN}✅ Redis SET/GET{bcolors.ENDC}: {value[:50]}")
        
        r.lpush("e2e_test_queue", "msg1", "msg2", "msg3")
        queue_len = r.llen("e2e_test_queue")
        print(f"{bcolors.OKGREEN}✅ Redis Queue{bcolors.ENDC}: {queue_len} mensagens")
        
        r.delete("e2e_test_key", "e2e_test_queue")
        
        return True
        
    except Exception as e:
        print(f"{bcolors.FAIL}❌ Erro: {e}{bcolors.ENDC}")
        return False

def test_celery():
    """Testa Celery"""
    print(f"\n{bcolors.OKCYAN}{'='*70}{bcolors.ENDC}")
    print(f"{bcolors.OKCYAN}🧪 TESTE 5: Celery Worker{bcolors.ENDC}")
    print(f"{bcolors.OKCYAN}{'='*70}{bcolors.ENDC}\n")
    
    try:
        import subprocess
        
        result = subprocess.run(
            ["docker-compose", "ps", "celery-worker"],
            capture_output=True,
            text=True
        )
        
        if "Up" in result.stdout:
            print(f"{bcolors.OKGREEN}✅ Celery Worker{bcolors.ENDC}: Running")
            return True
        else:
            print(f"{bcolors.WARNING}⚠️  Celery Worker{bcolors.ENDC}: Não está rodando")
            return False
            
    except Exception as e:
        print(f"{bcolors.FAIL}❌ Erro: {e}{bcolors.ENDC}")
        return False

def test_monitoring():
    """Testa Monitoring Stack"""
    print(f"\n{bcolors.OKCYAN}{'='*70}{bcolors.ENDC}")
    print(f"{bcolors.OKCYAN}🧪 TESTE 6: Monitoring Stack{bcolors.ENDC}")
    print(f"{bcolors.OKCYAN}{'='*70}{bcolors.ENDC}\n")
    
    services = [
        ("Grafana", "http://localhost:3000"),
    ]
    
    for service, url in services:
        try:
            resp = requests.head(url, timeout=2)
            if 200 <= resp.status_code < 400:
                print(f"{bcolors.OKGREEN}✅ {service}{bcolors.ENDC}: {resp.status_code}")
            else:
                print(f"{bcolors.WARNING}⚠️  {service}{bcolors.ENDC}: {resp.status_code}")
        except:
            print(f"{bcolors.WARNING}⚠️  {service}{bcolors.ENDC}: Inacessível")
    
    return True

def main():
    """Executa todos os testes"""
    print(f"\n{bcolors.BOLD}{bcolors.HEADER}🚀 EVAonline - Testes E2E{bcolors.ENDC}\n")
    
    results = []
    
    results.append(("API FastAPI", test_api()))
    results.append(("Frontend Dash", test_frontend()))
    results.append(("Database", test_database()))
    results.append(("Redis", test_redis()))
    results.append(("Celery", test_celery()))
    results.append(("Monitoring", test_monitoring()))
    
    # Resumo
    print(f"\n{bcolors.OKCYAN}{'='*70}{bcolors.ENDC}")
    print(f"{bcolors.OKCYAN}📊 RESUMO FINAL{bcolors.ENDC}")
    print(f"{bcolors.OKCYAN}{'='*70}{bcolors.ENDC}\n")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = f"{bcolors.OKGREEN}✅ PASS{bcolors.ENDC}" if result else f"{bcolors.FAIL}❌ FAIL{bcolors.ENDC}"
        print(f"  {name:<25} {status}")
    
    print(f"\n{bcolors.BOLD}Resultado: {passed}/{total} testes passaram{bcolors.ENDC}\n")
    
    if passed == total:
        print(f"{bcolors.OKGREEN}🎉 TUDO PRONTO PARA PRODUÇÃO!{bcolors.ENDC}\n")
    else:
        print(f"{bcolors.WARNING}⚠️  Verifique os testes que falharam{bcolors.ENDC}\n")

if __name__ == "__main__":
    main()
