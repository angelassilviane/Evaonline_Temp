"""
Tasks Celery para pre-carregamento de dados climáticos populares.

Estratégia de pre-fetch:
- Cidades mundiais populares: 50 cidades, execução diária 03:00 BRT
- Dados dos últimos 30 dias para cada localização

Benefits:
- Cache aquecido para requisições futuras
- Reduz latência para usuários
- Otimiza uso de APIs externas
- Distribui carga ao longo do tempo
"""

import asyncio
from datetime import datetime, timedelta

from celery import shared_task
from loguru import logger

# Cidades mundiais mais populares (top 50)
POPULAR_WORLD_CITIES = [
    {"name": "Paris", "lat": 48.8566, "lon": 2.3522, "country": "França"},
    {"name": "London", "lat": 51.5074, "lon": -0.1278, "country": "Reino Unido"},
    {"name": "New York", "lat": 40.7128, "lon": -74.0060, "country": "EUA"},
    {"name": "Tokyo", "lat": 35.6762, "lon": 139.6503, "country": "Japão"},
    {"name": "São Paulo", "lat": -23.5505, "lon": -46.6333, "country": "Brasil"},
    {"name": "Los Angeles", "lat": 34.0522, "lon": -118.2437, "country": "EUA"},
    {"name": "Shanghai", "lat": 31.2304, "lon": 121.4737, "country": "China"},
    {"name": "Mumbai", "lat": 19.0760, "lon": 72.8777, "country": "Índia"},
    {"name": "Beijing", "lat": 39.9042, "lon": 116.4074, "country": "China"},
    {"name": "Mexico City", "lat": 19.4326, "lon": -99.1332, "country": "México"},
    {"name": "Moscow", "lat": 55.7558, "lon": 37.6173, "country": "Rússia"},
    {"name": "Dubai", "lat": 25.2048, "lon": 55.2708, "country": "EAU"},
    {"name": "Singapore", "lat": 1.3521, "lon": 103.8198, "country": "Cingapura"},
    {"name": "Sydney", "lat": -33.8688, "lon": 151.2093, "country": "Austrália"},
    {"name": "Berlin", "lat": 52.5200, "lon": 13.4050, "country": "Alemanha"},
    {"name": "Madrid", "lat": 40.4168, "lon": -3.7038, "country": "Espanha"},
    {"name": "Rome", "lat": 41.9028, "lon": 12.4964, "country": "Itália"},
    {"name": "Toronto", "lat": 43.6532, "lon": -79.3832, "country": "Canadá"},
    {"name": "Istanbul", "lat": 41.0082, "lon": 28.9784, "country": "Turquia"},
    {"name": "Bangkok", "lat": 13.7563, "lon": 100.5018, "country": "Tailândia"},
    {"name": "Buenos Aires", "lat": -34.6037, "lon": -58.3816,
     "country": "Argentina"},
    {"name": "Rio de Janeiro", "lat": -22.9068, "lon": -43.1729,
     "country": "Brasil"},
    {"name": "Seoul", "lat": 37.5665, "lon": 126.9780, "country": "Coreia"},
    {"name": "Amsterdam", "lat": 52.3676, "lon": 4.9041, "country": "Holanda"},
    {"name": "Vienna", "lat": 48.2082, "lon": 16.3738, "country": "Áustria"},
    {"name": "Barcelona", "lat": 41.3851, "lon": 2.1734, "country": "Espanha"},
    {"name": "Lisbon", "lat": 38.7223, "lon": -9.1393, "country": "Portugal"},
    {"name": "Cairo", "lat": 30.0444, "lon": 31.2357, "country": "Egito"},
    {"name": "Cape Town", "lat": -33.9249, "lon": 18.4241,
     "country": "África do Sul"},
    {"name": "Melbourne", "lat": -37.8136, "lon": 144.9631,
     "country": "Austrália"},
    {"name": "Hong Kong", "lat": 22.3193, "lon": 114.1694, "country": "China"},
    {"name": "San Francisco", "lat": 37.7749, "lon": -122.4194,
     "country": "EUA"},
    {"name": "Chicago", "lat": 41.8781, "lon": -87.6298, "country": "EUA"},
    {"name": "Miami", "lat": 25.7617, "lon": -80.1918, "country": "EUA"},
    {"name": "Brasília", "lat": -15.7939, "lon": -47.8828, "country": "Brasil"},
    {"name": "Bogotá", "lat": 4.7110, "lon": -74.0721, "country": "Colômbia"},
    {"name": "Lima", "lat": -12.0464, "lon": -77.0428, "country": "Peru"},
    {"name": "Santiago", "lat": -33.4489, "lon": -70.6693, "country": "Chile"},
    {"name": "Johannesburg", "lat": -26.2041, "lon": 28.0473,
     "country": "África do Sul"},
    {"name": "Lagos", "lat": 6.5244, "lon": 3.3792, "country": "Nigéria"},
    {"name": "Nairobi", "lat": -1.2864, "lon": 36.8172, "country": "Quênia"},
    {"name": "Tel Aviv", "lat": 32.0853, "lon": 34.7818, "country": "Israel"},
    {"name": "Athens", "lat": 37.9838, "lon": 23.7275, "country": "Grécia"},
    {"name": "Stockholm", "lat": 59.3293, "lon": 18.0686, "country": "Suécia"},
    {"name": "Copenhagen", "lat": 55.6761, "lon": 12.5683,
     "country": "Dinamarca"},
    {"name": "Oslo", "lat": 59.9139, "lon": 10.7522, "country": "Noruega"},
    {"name": "Helsinki", "lat": 60.1695, "lon": 24.9354, "country": "Finlândia"},
    {"name": "Warsaw", "lat": 52.2297, "lon": 21.0122, "country": "Polônia"},
    {"name": "Prague", "lat": 50.0755, "lon": 14.4378, "country": "Tchéquia"},
    {"name": "Budapest", "lat": 47.4979, "lon": 19.0402, "country": "Hungria"},
]


@shared_task(
    bind=True,
    max_retries=3,
    name="backend.infrastructure.cache.climate_tasks.prefetch_nasa_popular_cities"
)
def prefetch_nasa_popular_cities(self):
    """
    Pre-carrega dados NASA POWER para 50 cidades mais populares.

    Execução: Diariamente às 03:00 BRT via Celery Beat
    Período: Últimos 30 dias
    Fontes: NASA POWER (domínio público)

    Returns:
        dict: Status e estatísticas do pre-fetch
    """
    try:
        logger.info("🚀 Iniciando pre-fetch NASA POWER (50 cidades)")

        # Importa dentro da task para evitar circular imports
        from backend.api.services.nasa_power_client import NASAPowerClient
        from backend.infrastructure.cache.climate_cache import create_climate_cache

        # Período: últimos 30 dias
        end = datetime.now()
        start = end - timedelta(days=30)

        # Cria cache e cliente
        cache = create_climate_cache("nasa")
        client = NASAPowerClient(cache=cache)

        success_count = 0
        failed_cities = []

        # Pre-fetch cada cidade
        for idx, city in enumerate(POPULAR_WORLD_CITIES, 1):
            try:
                # Usa asyncio para chamar método async
                loop = asyncio.get_event_loop()
                data = loop.run_until_complete(
                    client.get_daily_data(
                        lat=city["lat"],
                        lon=city["lon"],
                        start_date=start,
                        end_date=end
                    )
                )

                if data:
                    success_count += 1
                    logger.info(
                        f"✅ [{idx}/{len(POPULAR_WORLD_CITIES)}] "
                        f"{city['name']}, {city['country']}"
                    )
                else:
                    failed_cities.append(city["name"])
                    logger.warning(f"⚠️ Sem dados para {city['name']}")

            except Exception as e:
                failed_cities.append(city["name"])
                logger.error(
                    f"❌ Erro em {city['name']}: {str(e)[:100]}"
                )

        # Estatísticas finais
        total = len(POPULAR_WORLD_CITIES)
        success_rate = (success_count / total) * 100

        result = {
            "status": "success" if success_count > 0 else "failed",
            "total_cities": total,
            "success": success_count,
            "failed": len(failed_cities),
            "success_rate": f"{success_rate:.1f}%",
            "failed_cities": failed_cities[:10],  # Primeiras 10
            "period": f"{start.date()} to {end.date()}"
        }

        logger.info(
            f"🎯 Pre-fetch NASA POWER completo: "
            f"{success_count}/{total} cidades ({success_rate:.1f}%)"
        )

        # Fecha conexões
        loop.run_until_complete(cache.close())
        loop.run_until_complete(client.close())

        return result

    except Exception as e:
        logger.error(f"💥 Erro crítico no pre-fetch NASA: {e}")
        # Retry com exponential backoff
        raise self.retry(exc=e, countdown=300)  # 5 minutos


@shared_task(name="backend.infrastructure.cache.climate_tasks.cleanup_old_cache")
def cleanup_old_cache():
    """
    Remove entradas de cache expiradas antigas.

    Execução: Diariamente às 02:00 BRT via Celery Beat
    Remove: Chaves com padrão 'climate:*' expiradas há mais de 7 dias

    Returns:
        dict: Estatísticas de limpeza
    """
    try:
        import redis

        from config.settings import get_settings

        settings = get_settings()

        logger.info("🧹 Iniciando limpeza de cache climático antigo")

        r = redis.from_url(settings.REDIS_URL, decode_responses=True)

        # Busca todas as chaves 'climate:*'
        keys = r.keys("climate:*")
        removed_count = 0

        for key in keys:
            ttl = r.ttl(key)
            # Se TTL <= 0 (expirado)
            if ttl <= 0:
                r.delete(key)
                removed_count += 1

        logger.info(f"✅ Removidas {removed_count} chaves de cache expiradas")
        return {"status": "success", "removed_keys": removed_count}

    except Exception as e:
        logger.error(f"❌ Erro na limpeza de cache: {str(e)}")
        return {"status": "error", "message": str(e)}

        removed_count = 0
        kept_count = 0

        for key in keys:
            ttl = loop.run_until_complete(redis.ttl(key))

            # Remove se TTL expirado (< 0) ou muito baixo (< 1 hora)
            if ttl < 0 or ttl < 3600:
                loop.run_until_complete(redis.delete(key))
                removed_count += 1
            else:
                kept_count += 1

        logger.info(
            f"✅ Limpeza completa: {removed_count} removidas, "
            f"{kept_count} mantidas"
        )

        loop.run_until_complete(redis.close())

        return {
            "status": "success",
            "removed": removed_count,
            "kept": kept_count,
            "total_scanned": len(keys)
        }

    except Exception as e:
        logger.error(f"❌ Erro na limpeza de cache: {e}")
        return {"status": "error", "message": str(e)}


@shared_task(name="backend.infrastructure.cache.climate_tasks.generate_cache_stats")
def generate_cache_stats():
    """
    Gera estatísticas de uso do cache.

    Execução: A cada hora via Celery Beat
    Métricas: Hit rate, dados populares, tamanho do cache

    Returns:
        dict: Estatísticas de cache
    """
    try:
        import redis

        from config.settings import get_settings

        settings = get_settings()
        r = redis.from_url(settings.REDIS_URL, decode_responses=True)

        # Conta chaves por fonte
        sources = ["nasa", "met", "nws", "openmeteo"]
        stats = {}

        for source in sources:
            keys = r.keys(f"climate:{source}:*")
            stats[source] = {
                "total_keys": len(keys),
                "memory_mb": 0  # TODO: calcular tamanho real
            }

        # Total geral
        total_keys = r.dbsize()

        result = {
            "timestamp": datetime.now().isoformat(),
            "sources": stats,
            "total_keys_db": total_keys
        }

        logger.info(f"📊 Cache stats: {result}")

        return result

    except Exception as e:
        logger.error(f"❌ Erro ao gerar stats: {e}")
        return {"status": "error", "message": str(e)}
