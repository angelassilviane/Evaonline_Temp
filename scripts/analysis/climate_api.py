# # scripts/api/climate_api.py
# class ClimateAPI:
#     def __init__(self):
#         # Carrega apenas uma vez na inicialização
#         self.climate_tables = self.load_climate_tables()
    
#     def is_extreme(self, city: str, variable: str, value: float, date: str) -> Dict:
#         """API rápida para verificar extremos (usando tabelas pré-calculadas)"""
#         # Operação O(1) - apenas lookup nas tabelas
#         return self._check_extreme_fast(city, variable, value, date)