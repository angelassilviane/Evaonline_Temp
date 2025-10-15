"""
Adapter síncrono para NASAPowerClient.

Este adapter permite usar o cliente assíncrono NASA POWER em código síncrono,
facilitando a migração gradual da arquitetura.

Usage:
    >>> adapter = NASAPowerSyncAdapter()
    >>> data = adapter.get_daily_data_sync(
    ...     lat=-15.7939,
    ...     lon=-47.8828,
    ...     start_date=datetime(2024, 10, 1),
    ...     end_date=datetime(2024, 10, 7)
    ... )
"""

import asyncio
from datetime import datetime
from typing import List, Optional

from loguru import logger

from .nasa_power_client import NASAPowerClient, NASAPowerConfig, NASAPowerData


class NASAPowerSyncAdapter:
    """
    Adapter síncrono para NASAPowerClient assíncrono.
    
    Converte chamadas síncronas em assíncronas usando asyncio.run(),
    mantendo compatibilidade com código legacy.
    
    Features:
    - Interface síncrona simples
    - Gerenciamento automático de event loop
    - Cache Redis integrado
    - Logging detalhado
    """
    
    def __init__(
        self,
        config: Optional[NASAPowerConfig] = None,
        cache: Optional[any] = None
    ):
        """
        Inicializa adapter.
        
        Args:
            config: Configuração NASA POWER (opcional)
            cache: Cache service (opcional)
        """
        self.config = config or NASAPowerConfig()
        self.cache = cache
        logger.info("NASAPowerSyncAdapter initialized")
    
    def get_daily_data_sync(
        self,
        lat: float,
        lon: float,
        start_date: datetime,
        end_date: datetime,
        community: str = "ag"
    ) -> List[NASAPowerData]:
        """
        Busca dados diários de forma síncrona.
        
        Internamente usa async/await mas expõe interface síncrona.
        
        Args:
            lat: Latitude (-90 a 90)
            lon: Longitude (-180 a 180)
            start_date: Data inicial
            end_date: Data final
            community: Comunidade NASA POWER (ag=agriculture)
            
        Returns:
            List[NASAPowerData]: Dados diários
            
        Raises:
            ValueError: Se parâmetros inválidos
            Exception: Se requisição falhar
        """
        logger.debug(
            f"Sync request: lat={lat}, lon={lon}, "
            f"dates={start_date.date()} to {end_date.date()}"
        )
        
        # Executa função assíncrona de forma síncrona
        return asyncio.run(
            self._async_get_daily_data(
                lat=lat,
                lon=lon,
                start_date=start_date,
                end_date=end_date,
                community=community
            )
        )
    
    async def _async_get_daily_data(
        self,
        lat: float,
        lon: float,
        start_date: datetime,
        end_date: datetime,
        community: str
    ) -> List[NASAPowerData]:
        """
        Método assíncrono interno.
        
        Cria cliente, faz requisição, fecha conexão.
        """
        client = NASAPowerClient(config=self.config, cache=self.cache)
        
        try:
            data = await client.get_daily_data(
                lat=lat,
                lon=lon,
                start_date=start_date,
                end_date=end_date,
                community=community
            )
            
            logger.info(
                f"✅ NASA POWER sync: {len(data)} registros obtidos"
            )
            return data
            
        finally:
            await client.close()
    
    def health_check_sync(self) -> bool:
        """
        Health check síncrono.
        
        Returns:
            bool: True se API está acessível
        """
        return asyncio.run(self._async_health_check())
    
    async def _async_health_check(self) -> bool:
        """Health check assíncrono interno."""
        client = NASAPowerClient(config=self.config, cache=self.cache)
        
        try:
            return await client.health_check()
        finally:
            await client.close()


# Exemplo de uso
def example_sync_usage():
    """Demonstra uso síncrono do adapter."""
    adapter = NASAPowerSyncAdapter()
    
    # Buscar dados para Brasília (código síncrono!)
    data = adapter.get_daily_data_sync(
        lat=-15.7939,
        lon=-47.8828,
        start_date=datetime(2024, 10, 1),
        end_date=datetime(2024, 10, 7)
    )
    
    print(f"✅ NASA POWER: {len(data)} registros")
    for record in data[:3]:  # Primeiros 3
        print(
            f"  {record.date}: "
            f"T={record.temp_mean}°C, "
            f"RH={record.humidity}%, "
            f"Solar={record.solar_radiation} MJ/m²/day"
        )


if __name__ == "__main__":
    example_sync_usage()
