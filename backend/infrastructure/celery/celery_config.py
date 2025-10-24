"""
Configuração do Celery para tarefas assíncronas do EVAonline.
Centraliza todas as configurações do Celery para a aplicação.
"""
import json
import logging
import time
from datetime import datetime

from celery import Celery
from celery.schedules import crontab
from kombu import Queue
from redis import Redis

from config.settings import get_settings

logger = logging.getLogger(__name__)

# Carregar configurações
settings = get_settings()

# Inicializar Celery
celery_app = Celery(
    "evaonline",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Métricas Prometheus
# As métricas são importadas do main.py para evitar duplicação

# Classe base para tarefas com monitoramento e progresso
class MonitoredProgressTask(celery_app.Task):
    def publish_progress(self, task_id, progress, status="PROGRESS"):
        """Publica progresso no canal Redis para WebSocket."""
        try:
            redis_client = Redis.from_url(
                settings.CELERY_BROKER_URL,
                decode_responses=True
            )
            redis_client.publish(
                f"task_status:{task_id}",
                json.dumps({
                    "status": status,
                    "info": progress,
                    "timestamp": datetime.now().isoformat()
                })
            )
            redis_client.close()
        except Exception as e:
            # Não bloqueia a task se falhar publicação de progresso
            import logging
            logging.warning(f"Falha ao publicar progresso: {e}")

    def __call__(self, *args, **kwargs):
        """Rastreia duração e status da tarefa para Prometheus."""
        start_time = time.time()
        try:
            result = super().__call__(*args, **kwargs)
            
            # Registrar sucesso em Prometheus (se disponível)
            try:
                from backend.api.middleware.prometheus_metrics import CELERY_TASKS_TOTAL
                CELERY_TASKS_TOTAL.labels(task_name=self.name, status="SUCCESS").inc()
            except (ImportError, AttributeError):
                pass  # Prometheus não disponível
            
            return result
            
        except Exception as e:
            # Registrar erro em Prometheus (se disponível)
            try:
                from backend.api.middleware.prometheus_metrics import CELERY_TASKS_TOTAL
                CELERY_TASKS_TOTAL.labels(task_name=self.name, status="FAILURE").inc()
            except (ImportError, AttributeError):
                pass
            
            raise
            
        finally:
            # Registrar duração em Prometheus (se disponível)
            try:
                from backend.api.middleware.prometheus_metrics import CELERY_TASK_DURATION
                CELERY_TASK_DURATION.labels(task_name=self.name).observe(time.time() - start_time)
            except (ImportError, AttributeError):
                pass

# Definir classe base para todas as tarefas
celery_app.Task = MonitoredProgressTask

# Configurações principais
celery_app.conf.update(
    # Serialização
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    
    # Timezone
    timezone="America/Sao_Paulo",
    enable_utc=True,
    
    # Rotas e filas
    task_default_queue="general",
    task_routes={
        "backend.core.eto_calculation.*": {"queue": "eto_processing"},
        "backend.core.data_processing.data_download.*": {"queue": "data_download"},
        "backend.infrastructure.cache.*": {"queue": "data_processing"},
    },
    task_queues=(
        Queue("general"),
        Queue("eto_processing"),
        Queue("data_download"),
        Queue("data_processing"),
    ),
)

# Configuração de tarefas periódicas
celery_app.conf.beat_schedule = {
    # Limpeza de cache antigo (02:00 BRT)
    "cleanup-old-climate-cache": {
        "task": "backend.infrastructure.cache.climate_tasks.cleanup_old_cache",
        "schedule": crontab(hour=2, minute=0),
        "options": {"queue": "data_processing"}
    },
    # Pre-fetch cidades mundiais populares (03:00 BRT)
    "prefetch-nasa-popular-cities": {
        "task": "backend.infrastructure.cache.climate_tasks.prefetch_nasa_popular_cities",
        "schedule": crontab(hour=3, minute=0),
        "options": {"queue": "data_processing"}
    },
    # Estatísticas de cache (a cada hora)
    "generate-cache-stats": {
        "task": "backend.infrastructure.cache.climate_tasks.generate_cache_stats",
        "schedule": crontab(minute=0),  # Todo início de hora
        "options": {"queue": "data_processing"}
    },
    # Tasks legadas
    "cleanup-expired-data": {
        "task": "backend.infrastructure.cache.celery_tasks.cleanup_expired_data",
        "schedule": crontab(hour=0, minute=0),  # 00:00 diariamente
        "options": {"queue": "data_processing"}
    },
    "update-popular-ranking": {
        "task": "backend.infrastructure.cache.celery_tasks.update_popular_ranking",
        "schedule": crontab(minute="*/10"),  # A cada 10 minutos
        "options": {"queue": "data_processing"}
    },
}

# Descoberta automática de tarefas
celery_app.autodiscover_tasks([
    "backend.infrastructure.cache.celery_tasks",
    "backend.infrastructure.cache.climate_tasks",
    "backend.core.eto_calculation",
    "backend.core.data_processing.data_download",
])
