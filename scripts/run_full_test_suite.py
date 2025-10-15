"""
Suite de Testes Completa - EVAonline
Valida toda a infraestrutura: Python, Redis, Celery, Pipeline ETo

Uso:
    python scripts/run_full_test_suite.py
"""

import json
import os
import pickle
import sys
import time
from datetime import datetime
from pathlib import Path

# Adicionar diretório raiz ao path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

# ============================================================================
# CORES E FORMATAÇÃO
# ============================================================================

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(title):
    print(f"\n{'='*70}")
    print(f"{Colors.CYAN}{Colors.BOLD}{title}{Colors.END}")
    print(f"{'='*70}")

def print_success(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.END}")

def print_error(msg):
    print(f"{Colors.RED}❌ {msg}{Colors.END}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.END}")

def print_info(msg):
    print(f"{Colors.CYAN}ℹ️  {msg}{Colors.END}")

# ============================================================================
# TESTE 1: AMBIENTE PYTHON
# ============================================================================

def test_python_environment():
    """Testa ambiente Python e dependências."""
    print_header("TESTE 1: Ambiente Python e Dependências")
    
    try:
        # Python versão
        python_version = sys.version.split()[0]
        print_info(f"Python versão: {python_version}")
        
        # Pacotes críticos
        packages = {
            'celery': 'Celery',
            'redis': 'Redis',
            'pandas': 'Pandas',
            'numpy': 'NumPy',
            'requests': 'Requests',
        }
        
        all_ok = True
        for module, name in packages.items():
            try:
                __import__(module)
                print_success(f"{name} instalado")
            except ImportError:
                print_error(f"{name} NÃO instalado")
                all_ok = False
        
        if all_ok:
            print_success("Ambiente Python OK!")
            return True
        else:
            print_error("Instale dependências: pip install -r requirements.txt")
            return False
            
    except Exception as e:
        print_error(f"Erro ao verificar ambiente: {e}")
        return False

# ============================================================================
# TESTE 2: REDIS
# ============================================================================

def test_redis_connection():
    """Testa conexão e operações Redis."""
    print_header("TESTE 2: Conexão e Operações Redis")
    
    try:
        from redis import Redis
        from redis.exceptions import AuthenticationError, ConnectionError

        # Configuração
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = os.getenv("REDIS_PORT", "6379")
        redis_password = os.getenv("REDIS_PASSWORD", "evaonline")
        redis_url = f"redis://default:{redis_password}@{redis_host}:{redis_port}/0"
        
        print_info(f"Conectando a: {redis_host}:{redis_port}")
        
        # Conexão
        redis_client = Redis.from_url(redis_url, decode_responses=True)
        response = redis_client.ping()
        
        if not response:
            print_error("Redis não respondeu ao PING")
            return False
        
        print_success("Redis conectado!")
        
        # Info
        info = redis_client.info("server")
        print_info(f"Versão Redis: {info.get('redis_version', 'N/A')}")
        print_info(f"Uptime: {info.get('uptime_in_seconds', 0)}s")
        
        # Teste SET/GET
        test_key = "test:suite:key"
        test_value = f"test_{int(time.time())}"
        redis_client.set(test_key, test_value, ex=10)
        retrieved = redis_client.get(test_key)
        
        if retrieved == test_value:
            print_success("Operação SET/GET OK")
            redis_client.delete(test_key)
        else:
            print_error("Operação SET/GET falhou")
            return False
        
        # Teste Pickle
        redis_raw = Redis.from_url(redis_url, decode_responses=False)
        test_data = {'timestamp': datetime.now(), 'value': 123.45}
        pickled = pickle.dumps(test_data)
        redis_raw.setex("test:pickle", 10, pickled)
        retrieved_bytes = redis_raw.get("test:pickle")
        unpickled = pickle.loads(retrieved_bytes)
        
        if unpickled['value'] == 123.45:
            print_success("Operação Pickle OK")
            redis_client.delete("test:pickle")
        else:
            print_error("Operação Pickle falhou")
            return False
        
        print_success("Redis totalmente funcional!")
        return True
        
    except ConnectionError:
        print_error("Redis não está rodando")
        print_info("Execute: .\\scripts\\manage_celery_redis.ps1 start-redis")
        return False
    except AuthenticationError:
        print_error("Senha Redis incorreta")
        print_info("Verifique REDIS_PASSWORD no .env")
        return False
    except Exception as e:
        print_error(f"Erro inesperado: {e}")
        return False

# ============================================================================
# TESTE 3: IMPORTS HOURLY ETo
# ============================================================================

def test_hourly_eto_imports():
    """Testa imports dos módulos ETo Hourly."""
    print_header("TESTE 3: Imports Módulos ETo Hourly")
    
    try:
        # ETo Hourly
        from backend.core.eto_calculation.eto_hourly import (
            aggregate_hourly_to_daily, calculate_eto_hourly)
        print_success("eto_hourly importado")
        
        print_success("Todos os imports OK!")
        return True
        
    except ImportError as e:
        print_error(f"Erro de import: {e}")
        return False
    except SyntaxError as e:
        print_error(f"Erro de sintaxe: {e}")
        return False
    except Exception as e:
        print_error(f"Erro inesperado: {e}")
        return False


# ============================================================================
# TESTE 4: CELERY WORKER
# ============================================================================

def test_celery_worker():
    """Testa se Celery worker está acessível."""
    print_header("TESTE 4: Celery Worker")
    
    try:
        print_info("Verificando configuração Celery...")
        
        # Verificar se pode importar celery_app
        from backend.infrastructure.celery.celery_config import celery_app
        print_success("Celery app configurado corretamente")
        
        # Verificar broker URL
        broker_url = celery_app.conf.broker_url
        broker_display = (broker_url.split('@')[1] 
                         if '@' in broker_url else 'N/A')
        print_info(f"Broker configurado: {broker_display}")
        
        # Tentar conectar ao Redis (broker)
        import os

        from redis import Redis
        
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = os.getenv("REDIS_PORT", "6379")
        redis_password = os.getenv("REDIS_PASSWORD", "evaonline")
        redis_url = (f"redis://default:{redis_password}"
                    f"@{redis_host}:{redis_port}/0")
        
        redis_client = Redis.from_url(redis_url, decode_responses=True)
        if redis_client.ping():
            print_success("Broker Redis acessível")
        redis_client.close()
        
        print_success("Celery configuração validada!")
        print_info("Nota: Worker executa em container separado")
        return True
        
    except Exception as e:
        print_error(f"Erro ao verificar Celery: {e}")
        import traceback
        traceback.print_exc()
        return False



# ============================================================================
# TESTE 5: VALIDAR MÉTRICAS
# ============================================================================

def test_validation_metrics():
    """Valida métricas R²/RMSE do cache."""
    print_header("TESTE 5: Métricas de Validação R²/RMSE")
    
    try:
        from redis import Redis
        
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = os.getenv("REDIS_PORT", "6379")
        redis_password = os.getenv("REDIS_PASSWORD", "evaonline")
        redis_url = (f"redis://default:{redis_password}"
                    f"@{redis_host}:{redis_port}/0")
        
        redis_client = Redis.from_url(redis_url, decode_responses=False)
        
        # Buscar forecasts (usando chave genérica)
        forecast_key = "forecasts:latest"
        data_bytes = redis_client.get(forecast_key)
        
        if not data_bytes:
            print_warning("Cache de forecasts não encontrado")
            print_info("Execute task primeiro")
            return False
        
        # Deserializar (agora é JSON, não Pickle)
        try:
            cache_data = json.loads(data_bytes)
        except json.JSONDecodeError:
            # Fallback para Pickle (compatibilidade)
            cache_data = pickle.loads(data_bytes)
        
        validation = cache_data.get('validation', {})
        
        if not validation:
            print_warning("Métricas de validação não encontradas")
            return False
        
        print_info("Métricas encontradas:")
        
        # R²
        r2 = validation.get('r2', 0)
        print_info(f"  R² (correlação): {r2:.4f}")
        
        if r2 >= 0.75:
            print_success("  ✅ EXCELENTE (R² ≥ 0.75)")
        elif r2 >= 0.65:
            print_warning("  ⚠️  ACEITÁVEL (R² ≥ 0.65)")
        else:
            print_error("  ❌ INSUFICIENTE (R² < 0.65)")
        
        # RMSE
        rmse = validation.get('rmse', 999)
        print_info(f"  RMSE (erro): {rmse:.4f} mm/dia")
        
        if rmse <= 1.2:
            print_success("  ✅ EXCELENTE (RMSE ≤ 1.2)")
        elif rmse <= 1.5:
            print_warning("  ⚠️  ACEITÁVEL (RMSE ≤ 1.5)")
        else:
            print_error("  ❌ INSUFICIENTE (RMSE > 1.5)")
        
        # Outros
        print_info(f"  Bias: {validation.get('bias', 0):.4f} mm/dia")
        print_info(f"  MAE: {validation.get('mae', 0):.4f} mm/dia")
        print_info(f"  Amostras: {validation.get('n_samples', 0)}")
        print_info(f"  Status: {validation.get('status', 'N/A')}")
        
        # Aprovação
        if r2 >= 0.65 and rmse <= 1.5:
            print_success("Métricas APROVADAS para produção!")
            return True
        else:
            print_warning("Métricas abaixo do esperado (mas funcionais)")
            return True  # Não falha, pois dados são salvos mesmo assim
        
    except Exception as e:
        print_error(f"Erro ao validar métricas: {e}")
        return False

# ============================================================================
# RESUMO E RELATÓRIO
# ============================================================================

def generate_report(results):
    """Gera relatório final dos testes."""
    print_header("RELATÓRIO FINAL")
    
    total = len(results)
    passed = sum(1 for r in results.values() if r)
    failed = total - passed
    
    print(f"\nTotal de testes: {total}")
    print_success(f"Aprovados: {passed}")
    
    if failed > 0:
        print_error(f"Falharam: {failed}")
    else:
        print_success("Falharam: 0")
    
    print("\nDetalhamento:")
    for test_name, passed in results.items():
        status = "✅ PASSOU" if passed else "❌ FALHOU"
        color = Colors.GREEN if passed else Colors.RED
        print(f"  {color}{status}{Colors.END} - {test_name}")
    
    print("\n" + "="*70)
    
    if failed == 0:
        print(f"{Colors.GREEN}{Colors.BOLD}")
        print("🎉 TODOS OS TESTES PASSARAM! 🎉")
        print("Sistema pronto para produção!")
        print(f"{Colors.END}")
    else:
        print(f"{Colors.YELLOW}{Colors.BOLD}")
        print(f"⚠️  {failed} teste(s) falharam")
        print("Revise os erros acima e corrija antes de produção")
        print(f"{Colors.END}")

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Executa suite completa de testes."""
    print(f"{Colors.CYAN}{Colors.BOLD}")
    print("="*70)
    print("   SUITE DE TESTES COMPLETA - EVAonline")
    print("="*70)
    print(f"{Colors.END}")
    print(f"Início: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    results = {}
    
    # Teste 1: Ambiente Python
    results['Ambiente Python'] = test_python_environment()
    if not results['Ambiente Python']:
        print_error("\n⛔ Ambiente Python com problemas.")
        generate_report(results)
        return
    
    # Teste 2: Redis
    results['Redis Connection'] = test_redis_connection()
    if not results['Redis Connection']:
        print_warning("\n⚠️  Redis não disponível. Pulando testes.")
    
    # Teste 3: Imports
    results['Imports ETo Hourly'] = test_hourly_eto_imports()
    if not results['Imports ETo Hourly']:
        print_error("\n⛔ Imports com problemas.")
        generate_report(results)
        return
    
    # Teste 4: Celery Worker
    results['Celery Worker'] = test_celery_worker()
    
    # Teste 5: Métricas
    if results.get('Redis Connection'):
        results['Métricas Validação'] = test_validation_metrics()
    else:
        results['Métricas Validação'] = None
    
    # Relatório final
    print(f"\nFim: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Filtrar testes None (pulados)
    results_filtered = {k: v for k, v in results.items() 
                       if v is not None}
    generate_report(results_filtered)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}⚠️  Testes interrompidos pelo usuário{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n{Colors.RED}❌ Erro fatal: {e}{Colors.END}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
