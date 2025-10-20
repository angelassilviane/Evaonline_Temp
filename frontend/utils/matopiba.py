"""
Utilitários para dados do MATOPIBA (337 cidades da região) otimizados.
"""
import json
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
from loguru import logger


class MatopibaDataManager:
    """Gerencia dados MATOPIBA com cache e otimizações."""
    
    def __init__(self):
        self._data_loaded = False
        self._geojson_cache = None
    
    @lru_cache(maxsize=1)
    def load_matopiba_cities(self) -> Dict:
        """
        Carrega as 337 cidades MATOPIBA com cache agressivo.
        
        Returns:
            dict: GeoJSON FeatureCollection
            
        Example:
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [-49.1624, -9.6218]
                        },
                        "properties": {
                            "name": "Abreulândia",
                            "uf": "TO",
                            "elevation": 238.86
                        }
                    }
                ]
            }
        """
        csv_path = (
            Path(__file__).parent.parent.parent / 
            'data' / 'csv' / 'CITIES_MATOPIBA_337.csv'
        )
        
        # Verificar cache primeiro
        if self._geojson_cache:
            return self._geojson_cache
        
        try:
            # Carregar CSV com otimizações
            df = pd.read_csv(
                csv_path,
                dtype={
                    'CITY': 'string',
                    'UF': 'string',
                    'LATITUDE': 'float64',
                    'LONGITUDE': 'float64',
                    'HEIGHT': 'float64'
                },
                usecols=['CITY', 'UF', 'LATITUDE', 'LONGITUDE', 'HEIGHT']
            )
            
            logger.info(f"✅ Carregadas {len(df)} cidades MATOPIBA")
            
            # Converter para GeoJSON de forma otimizada
            features = self._convert_to_geojson_features(df)
            geojson = {
                "type": "FeatureCollection",
                "features": features
            }
            
            # Atualizar cache
            self._geojson_cache = geojson
            self._data_loaded = True
            
            logger.info(f"✅ GeoJSON MATOPIBA criado com {len(features)} features")
            return geojson
            
        except FileNotFoundError:
            logger.error(f"❌ Arquivo não encontrado: {csv_path}")
            return self._get_empty_geojson()
        except Exception as e:
            logger.error(f"❌ Erro ao carregar MATOPIBA: {e}")
            return self._get_empty_geojson()
    
    def _convert_to_geojson_features(self, df: pd.DataFrame) -> List[Dict]:
        """Converte DataFrame para features GeoJSON de forma otimizada."""
        features = []
        
        for _, row in df.iterrows():
            try:
                feature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [
                            float(row['LONGITUDE']), 
                            float(row['LATITUDE'])
                        ]
                    },
                    "properties": {
                        "name": str(row['CITY']),
                        "uf": str(row['UF']),
                        "elevation": float(row['HEIGHT']),
                        "popup_text": (
                            f"<b>{row['CITY']}, {row['UF']}</b><br/>"
                            f"Latitude: {row['LATITUDE']:.4f}°<br/>"
                            f"Longitude: {row['LONGITUDE']:.4f}°<br/>"
                            f"Elevação: {row['HEIGHT']:.1f}m"
                        )
                    }
                }
                features.append(feature)
            except (ValueError, KeyError) as e:
                logger.warning(f"Erro ao processar linha {_}: {e}")
                continue
        
        return features
    
    def _get_empty_geojson(self) -> Dict:
        """Retorna GeoJSON vazio padrão."""
        return {"type": "FeatureCollection", "features": []}
    
    def get_city_by_name(self, city_name: str) -> Optional[Dict]:
        """Busca cidade por nome (case insensitive)."""
        geojson = self.load_matopiba_cities()
        
        for feature in geojson.get('features', []):
            if (feature['properties']['name'].lower() == 
                city_name.lower()):
                return feature
        return None
    
    def get_cities_by_uf(self, uf: str) -> List[Dict]:
        """Filtra cidades por UF."""
        geojson = self.load_matopiba_cities()
        
        return [
            feature for feature in geojson.get('features', [])
            if feature['properties']['uf'].upper() == uf.upper()
        ]


# Instância global para reutilização
matopiba_manager = MatopibaDataManager()


def load_matopiba_cities() -> Dict:
    """
    Função de compatibilidade para uso existente.
    
    Returns:
        dict: GeoJSON FeatureCollection
    """
    return matopiba_manager.load_matopiba_cities()


@lru_cache(maxsize=1)
def get_matopiba_geojson_with_clustering() -> Dict:
    """
    Retorna GeoJSON MATOPIBA com cache para clustering.
    
    Returns:
        dict: GeoJSON pronto para dl.GeoJSON()
    """
    return matopiba_manager.load_matopiba_cities()
