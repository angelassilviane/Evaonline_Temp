import time

import redis
from celery import shared_task
from loguru import logger

from config.settings import get_settings

# Fallback para métricas locais se houver problema de importação
try:
    # Importar métricas globais do middleware Prometheus
    from backend.api.middleware.prometheus_metrics import CELERY_TASK_DURATION, CELERY_TASKS_TOTAL
except ImportError:
    # Métricas dummy se prometheus não estiver disponível
    class DummyMetric:
        def labels(self, **kwargs):
            return self

        def inc(self):
            pass

        def observe(self, value):
            pass

    CELERY_TASKS_TOTAL = DummyMetric()
    CELERY_TASK_DURATION = DummyMetric()

# Carregar configurações
settings = get_settings()
REDIS_URL = settings.REDIS_URL


@shared_task(name="backend.infrastructure.cache.celery_tasks."
             "cleanup_expired_data")
def cleanup_expired_data():
    """Limpeza de dados expirados no Redis"""
    start_time = time.time()
    try:
        # Usar Redis síncrono
        r = redis.from_url(REDIS_URL, decode_responses=True)
        expired_keys = r.keys("forecast:expired:*")
        if expired_keys:
            r.delete(*expired_keys)
            logger.info(f"Removidas {len(expired_keys)} chaves expiradas")
        
        logger.info("Limpeza de dados expirados concluída com sucesso")
        CELERY_TASKS_TOTAL.labels(
            task_name="cleanup_expired_data", status="SUCCESS"
        ).inc()
        return {"status": "success", "cleaned_keys": len(expired_keys)}
        
    except Exception as e:
        logger.error(f"Erro na limpeza de dados: {str(e)}")
        CELERY_TASKS_TOTAL.labels(
            task_name="cleanup_expired_data", status="FAILURE"
        ).inc()
        raise
    finally:
        CELERY_TASK_DURATION.labels(
            task_name="cleanup_expired_data"
        ).observe(time.time() - start_time)


@shared_task(name="backend.infrastructure.cache.celery_tasks."
             "update_popular_ranking")
def update_popular_ranking():
    """Atualizar ranking de cidades mais acessadas"""
    start_time = time.time()
    try:
        # Usar Redis síncrono
        r = redis.from_url(REDIS_URL, decode_responses=True)
        keys = r.keys("acessos:*")
        
        for key in keys:
            acessos = int(r.get(key) or 0)
            r.zadd("ranking_acessos", {key: acessos})
        
        top_keys = r.zrange("ranking_acessos", 0, 9, desc=True)
        logger.info(f"Chaves mais acessadas: {top_keys}")
        
        CELERY_TASKS_TOTAL.labels(
            task_name="update_popular_ranking", status="SUCCESS"
        ).inc()
        return {"status": "success", "top_keys": top_keys}
        
    except Exception as e:
        logger.error(f"Erro ao atualizar ranking: {str(e)}")
        CELERY_TASKS_TOTAL.labels(
            task_name="update_popular_ranking", status="FAILURE"
        ).inc()
        raise
    finally:
        CELERY_TASK_DURATION.labels(
            task_name="update_popular_ranking"
        ).observe(time.time() - start_time)


