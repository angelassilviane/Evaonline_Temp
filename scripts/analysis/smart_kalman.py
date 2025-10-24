# scripts/models/smart_kalman.py
class SmartKalmanFilter:
    def __init__(self, climate_tables_path='../data/climate_tables.pkl'):
        # Carrega tabelas pré-calculadas (rápido!)
        with open(climate_tables_path, 'rb') as f:
            self.climate_data = pickle.load(f)
    
    def fuse_with_climate_intelligence(self, city_key, source_data):
        """Fusão Kalman com inteligência climática"""
        for source_name, measurement in source_data.items():
            extreme_check = self.check_if_extreme(
                city_key, 'ETo', measurement['ETo'], measurement['date']
            )
            
            # Ajusta peso baseado no resultado
            if extreme_check['is_extreme']:
                weight = 0.7  # Reduz peso, mas mantém
            elif extreme_check['reason'] == 'outlier':
                weight = 0.1  # Quase descarta
            else:
                weight = 1.0  # Peso normal
                
            # Aplica Kalman com peso adaptativo...