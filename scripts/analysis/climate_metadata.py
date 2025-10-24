# analysis/climate_metadata.py
import os
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats


class ScientificClimateMetadataRegistry:
    """
    Sistema de metadados climáticos baseado em referências científicas
    e padrões INMET/OMM:
    
    Referências Principais:
    - INMET: Normais Climatológicas do Brasil 1991-2020
    - WMO (2018): Guide to Climatological Practices (WMO-No. 1203)
    - Allen et al. (1998): FAO-56 Crop Evapotranspiration
    - McKee et al. (1993): Standardized Precipitation Index (SPI)
    - Sillmann et al. (2013): ETCCDI Climate Extremes Indices
    - Wilks (2011): Statistical Methods in the Atmospheric Sciences
    """
    
    # Períodos de referência padrão INMET/OMM (30 anos cada)
    REFERENCE_PERIODS = {
        '1961-1990': ('1961-01-01', '1990-12-31'),
        '1981-2010': ('1981-01-01', '2010-12-31'), 
        '1991-2020': ('1991-01-01', '2020-12-31')
    }
    
    def __init__(self, data_directory: str, reference_period: str = '1991-2020'):
        """
        Inicializa o registro de metadados climáticos.
        
        Args:
            data_directory: Diretório com dados climáticos
            reference_period: Período de referência ('1961-1990', '1981-2010', '1991-2020')
        """
        self.data_directory = data_directory
        
        # Valida período de referência
        if reference_period not in self.REFERENCE_PERIODS:
            raise ValueError(f"Período de referência deve ser um dos: {list(self.REFERENCE_PERIODS.keys())}")
        
        self.reference_period_key = reference_period
        self.reference_period = self.REFERENCE_PERIODS[reference_period]
        
        self.cities_config = self.create_cities_config()
        self.historical_data = self.load_all_city_data()
        
        # Inicializa estruturas vazias se não houver dados
        if not self.historical_data:
            print("⚠️  Nenhum dado foi carregado. Inicializando estruturas vazias.")
            self.climate_normals = {}
            self.all_period_normals = {}
            self.annual_normals = {}
            self.extreme_thresholds = {}
            self.spi_classification = {}
            self.hydrological_regimes = {}
        else:
            # Calcula normais para todos os períodos INMET
            self.all_period_normals = self.compute_inmet_normals()
            self.annual_normals = self.compute_annual_normals()
            
            # Usa o período de referência selecionado para análises
            self.climate_normals = self.all_period_normals.get(self.reference_period_key, {})
            
            # Métodos cientificamente validados
            self.extreme_thresholds = self.compute_etccdi_thresholds()
            self.spi_classification = self.compute_spi_classification()
            self.hydrological_regimes = self.classify_hydrological_years()
        
    def create_cities_config(self) -> Dict:
        """Cria configuração das cidades internamente"""
        return {
            'brasil': {
                'Alvorada_do_Gurgueia_PI': {'lat': -8.42, 'lon': -43.77, 'alt': 280},
                'Araguaina_TO': {'lat': -7.19, 'lon': -48.21, 'alt': 227},
                'Balsas_MA': {'lat': -7.53, 'lon': -46.04, 'alt': 283},
                'Barreiras_BA': {'lat': -12.15, 'lon': -45.00, 'alt': 454},
                'Bom_Jesus_PI': {'lat': -9.07, 'lon': -44.36, 'alt': 277},
                'Campos_Lindos_TO': {'lat': -7.99, 'lon': -46.87, 'alt': 313},
                'Carolina_MA': {'lat': -7.33, 'lon': -47.47, 'alt': 191},
                'Corrente_PI': {'lat': -10.44, 'lon': -45.16, 'alt': 438},
                'Formosa_do_Rio_Preto_BA': {'lat': -11.04, 'lon': -45.19, 'alt': 480},
                'Imperatriz_MA': {'lat': -5.53, 'lon': -47.48, 'alt': 95},
                'Luiz_Eduardo_Magalhaes_BA': {'lat': -12.09, 'lon': -45.79, 'alt': 720},
                'Pedro_Afonso_TO': {'lat': -8.97, 'lon': -48.17, 'alt': 201},
                'Piracicaba_SP': {'lat': -22.73, 'lon': -47.65, 'alt': 547},
                'Porto_Nacional_TO': {'lat': -10.71, 'lon': -48.42, 'alt': 212},
                'Sao_Desiderio_BA': {'lat': -12.36, 'lon': -44.97, 'alt': 516},
                'Tasso_Fragoso_MA': {'lat': -8.47, 'lon': -45.75, 'alt': 383},
                'Urucui_PI': {'lat': -7.23, 'lon': -44.56, 'alt': 421}
            },
            'global': {
                'Addis_Ababa_Ethiopia': {'lat': 9.03, 'lon': 38.74, 'alt': 2355},
                'Des_Moines_IA': {'lat': 41.59, 'lon': -93.62, 'alt': 291},
                'Fresno_CA': {'lat': 36.78, 'lon': -119.79, 'alt': 94},
                'Hanoi_Vietnam': {'lat': 21.03, 'lon': 105.85, 'alt': 16},
                'Krasnodar_Russia': {'lat': 45.04, 'lon': 38.98, 'alt': 28},
                'Ludhiana_Punjab': {'lat': 30.90, 'lon': 75.85, 'alt': 244},
                'Mendoza_Argentina': {'lat': -32.89, 'lon': -68.84, 'alt': 746},
                'Polokwane_Limpopo': {'lat': -23.90, 'lon': 29.45, 'alt': 1312},
                'Seville_Spain': {'lat': 37.39, 'lon': -5.98, 'alt': 7},
                'Wagga_Wagga_Australia': {'lat': -35.12, 'lon': 147.37, 'alt': 147}
            }
        }
    
    def load_city_eto_data(self, city_key: str, region: str) -> pd.DataFrame:
        """Carrega dados de ETo de uma cidade específica"""
        city_config = self.cities_config[region][city_key]
        
        # CORREÇÃO: Caminho correto para arquivo ETo
        if region == 'brasil':
            filepath = os.path.join(self.data_directory, 'csv', 'BRASIL', 'ETo', f"{city_key}.csv")
        else:
            filepath = os.path.join(self.data_directory, 'csv', 'MUNDO', 'ETo', f"{city_key}.csv")
        
        print(f"📁 Tentando carregar: {filepath}")
        
        try:
            # CORREÇÃO: Verifica se arquivo existe antes de ler
            if not os.path.exists(filepath):
                print(f"❌ Arquivo não encontrado: {filepath}")
                return pd.DataFrame()
            
            # CORREÇÃO: Lê o arquivo e verifica colunas disponíveis
            df = pd.read_csv(filepath)
            print(f"   Colunas encontradas: {list(df.columns)}")
            
            # CORREÇÃO: Verifica se a coluna de data existe
            date_column = None
            if 'Data' in df.columns:
                date_column = 'Data'
            elif 'date' in df.columns:
                date_column = 'date'
            else:
                print(f"❌ Coluna de data não encontrada. Colunas disponíveis: {list(df.columns)}")
                return pd.DataFrame()
            
            # CORREÇÃO: Converte para datetime
            df[date_column] = pd.to_datetime(df[date_column])
            df.set_index(date_column, inplace=True)
            
            # CORREÇÃO: Verifica se coluna ETo existe
            if 'ETo' not in df.columns:
                print(f"❌ Coluna ETo não encontrada. Colunas disponíveis: {list(df.columns)}")
                return pd.DataFrame()
            
            # Adicionar metadados da cidade
            df['city'] = city_key
            df['region'] = region
            df['lat'] = city_config['lat']
            df['lon'] = city_config['lon']
            df['alt'] = city_config['alt']
            
            print(f"✅ ETo {city_key} carregada - {len(df)} registros")
            return df
            
        except Exception as e:
            print(f"❌ Erro ao carregar ETo {city_key}: {e}")
            return pd.DataFrame()
    
    def load_city_precipitation_data(self, city_key: str, region: str) -> pd.DataFrame:
        """Carrega dados de precipitação de uma cidade específica"""
        city_config = self.cities_config[region][city_key]
        
        # CORREÇÃO: Caminho correto para arquivo precipitação
        if region == 'brasil':
            filepath = os.path.join(self.data_directory, 'csv', 'BRASIL', 'pr', f"{city_key}.csv")
        else:
            filepath = os.path.join(self.data_directory, 'csv', 'MUNDO', 'pr', f"{city_key}.csv")
        
        print(f"📁 Tentando carregar precipitação: {filepath}")
        
        try:
            # CORREÇÃO: Verifica se arquivo existe
            if not os.path.exists(filepath):
                print(f"⚠️ Arquivo precipitação não encontrado: {filepath}")
                return pd.DataFrame()
            
            # CORREÇÃO: Lê o arquivo e verifica colunas
            df = pd.read_csv(filepath)
            print(f"   Colunas encontradas: {list(df.columns)}")
            
            # CORREÇÃO: Verifica coluna de data
            date_column = None
            if 'Data' in df.columns:
                date_column = 'Data'
            elif 'date' in df.columns:
                date_column = 'date'
            else:
                print(f"❌ Coluna de data não encontrada no arquivo de precipitação")
                return pd.DataFrame()
            
            df[date_column] = pd.to_datetime(df[date_column])
            df.set_index(date_column, inplace=True)
            
            # CORREÇÃO: Renomeia coluna de precipitação
            precip_column = None
            if 'pr' in df.columns:
                precip_column = 'pr'
                df = df.rename(columns={'pr': 'precipitation'})
            elif 'precipitation' in df.columns:
                precip_column = 'precipitation'
            elif 'Precipitation' in df.columns:
                df = df.rename(columns={'Precipitation': 'precipitation'})
                precip_column = 'precipitation'
            else:
                print(f"❌ Coluna de precipitação não encontrada. Colunas: {list(df.columns)}")
                return pd.DataFrame()
            
            # Manter apenas coluna de precipitação
            df = df[['precipitation']]
            
            print(f"✅ Precipitação {city_key} carregada - {len(df)} registros")
            return df
            
        except Exception as e:
            print(f"❌ Erro ao carregar precipitação {city_key}: {e}")
            return pd.DataFrame()
    
    def load_city_combined_data(self, city_key: str, region: str) -> pd.DataFrame:
        """Combina dados de ETo e precipitação para uma cidade"""
        eto_data = self.load_city_eto_data(city_key, region)
        
        if eto_data.empty:
            print(f"❌ Dados de ETo vazios para {city_key}")
            return pd.DataFrame()
        
        # Se temos dados de precipitação, combina com ETo
        precip_data = self.load_city_precipitation_data(city_key, region)
        
        if not precip_data.empty:
            # CORREÇÃO: Faz merge baseado na data com sufixos
            combined_data = eto_data.merge(
                precip_data, 
                left_index=True, 
                right_index=True, 
                how='left',
                suffixes=('', '_precip')
            )
            print(f"🔄 Dados combinados para {city_key}: ETo + Precipitação")
        else:
            combined_data = eto_data
            combined_data['precipitation'] = np.nan
            print(f"ℹ️  Apenas ETo disponível para {city_key}")
        
        return combined_data
    
    def load_all_city_data(self) -> Dict[str, pd.DataFrame]:
        """Carrega dados de todas as cidades"""
        all_data = {}
        successful_cities = 0
        
        print(f"\n📂 Iniciando carregamento de dados de: {self.data_directory}")
        
        for region in ['brasil', 'global']:
            print(f"\n🌍 Processando região: {region.upper()}")
            
            for city_key in self.cities_config[region].keys():
                print(f"\n📍 Processando cidade: {city_key}")
                city_data = self.load_city_combined_data(city_key, region)
                
                if not city_data.empty:
                    all_data[city_key] = city_data
                    successful_cities += 1
                    print(f"✅ {city_key} - Carregado com sucesso")
                else:
                    print(f"❌ {city_key} - Falha no carregamento")
        
        print(f"\n🎯 Total de cidades carregadas com sucesso: {successful_cities}/{sum(len(self.cities_config[r]) for r in ['brasil', 'global'])}")
        
        # Estatísticas dos dados carregados
        if all_data:
            total_records = sum(len(data) for data in all_data.values())
            cities_with_precip = sum(1 for data in all_data.values() if 'precipitation' in data.columns and not data['precipitation'].isna().all())
            
            print(f"📊 Total de registros: {total_records:,}")
            print(f"🌧️  Cidades com dados de precipitação: {cities_with_precip}/{len(all_data)}")
        else:
            print("⚠️  Nenhum dado foi carregado com sucesso")
        
        return all_data

    def compute_inmet_normals(self) -> Dict[str, Dict]:
        """
        Calcula normais climatológicas para todos os períodos INMET/OMM
        seguindo a metodologia oficial.
        
        Agregação: Diários → Mensais → Anuais
        """
        print("\n📊 CALCULANDO NORMAIS CLIMATOLÓGICAS INMET/OMM")
        print("=" * 60)
        
        all_period_normals = {}
        
        for period_name, period_range in self.REFERENCE_PERIODS.items():
            print(f"\n🔬 Período: {period_name} ({period_range[0]} a {period_range[1]})")
            period_normals = {}
            
            for city_key, data in self.historical_data.items():
                print(f"  📍 Processando {city_key}...")
                
                try:
                    # Filtra dados do período
                    start_date, end_date = period_range
                    period_data = data[
                        (data.index >= start_date) & 
                        (data.index <= end_date)
                    ].copy()
                    
                    if len(period_data) == 0:
                        print(f"  ⚠️  Sem dados para {city_key} no período {period_name}")
                        continue
                    
                    # Calcula normais mensais e anuais
                    monthly_normals = self._compute_monthly_normals_inmet(period_data, period_name)
                    annual_normals = self._compute_annual_normals_inmet(period_data, period_name)
                    
                    if monthly_normals:
                        period_normals[city_key] = {
                            'monthly': monthly_normals,
                            'annual': annual_normals,
                            'metadata': {
                                'period': period_name,
                                'years_available': annual_normals.get('valid_years', 0),
                                'completeness': annual_normals.get('completeness_ratio', 0)
                            }
                        }
                        print(f"  ✅ {city_key}: {annual_normals.get('valid_years', 0)} anos válidos")
                    else:
                        print(f"  ⚠️  Dados insuficientes para {city_key}")
                        
                except Exception as e:
                    print(f"  ❌ Erro em {city_key}: {e}")
                    continue
            
            all_period_normals[period_name] = period_normals
            print(f"  🎯 {len(period_normals)} cidades processadas para {period_name}")
        
        return all_period_normals

    def _compute_monthly_normals_inmet(self, data: pd.DataFrame, period_name: str) -> Dict:
        """
        Calcula normais mensais: Diários → Mensais
        """
        monthly_stats = {}
        
        for month in range(1, 13):
            month_data = data[data.index.month == month]
            
            if len(month_data) == 0:
                continue
            
            # GRUPO I - ETo (VALORES MÉDIOS)
            # Agregação: Média diária → Média mensal
            eto_monthly = month_data.groupby([month_data.index.year, month_data.index.month])['ETo'].mean()
            eto_monthly_values = eto_monthly.groupby(level=1).mean()  # Média dos meses
            
            if len(eto_monthly) == 0:
                continue
                
            eto_stats = {
                # Normais mensais - GRUPO I (Médias)
                'normal': float(eto_monthly_values.get(month, np.nan)),
                
                # Estatísticas dos valores diários
                'daily_mean': month_data['ETo'].mean(),
                'daily_median': month_data['ETo'].median(),
                'daily_std': month_data['ETo'].std(),
                
                # Percentis de valores diários
                'p01': month_data['ETo'].quantile(0.01),
                'p05': month_data['ETo'].quantile(0.05),
                'p10': month_data['ETo'].quantile(0.10),
                'p25': month_data['ETo'].quantile(0.25),
                'p75': month_data['ETo'].quantile(0.75),
                'p90': month_data['ETo'].quantile(0.90),
                'p95': month_data['ETo'].quantile(0.95),
                'p99': month_data['ETo'].quantile(0.99),
                
                # Extremos absolutos
                'abs_min': month_data['ETo'].min(),
                'abs_max': month_data['ETo'].max(),
                
                # Metadados
                'n_days': len(month_data),
                'data_type': 'mean_daily'  # Grupo I - Valores médios
            }
            
            # GRUPO II - Precipitação (VALORES ACUMULADOS)
            if 'precipitation' in month_data.columns and not month_data['precipitation'].isna().all():
                precip_data = month_data['precipitation'].dropna()
                
                # Agregação: Soma diária → Total mensal → Normal mensal
                precip_monthly = month_data.groupby([month_data.index.year, month_data.index.month])['precipitation'].sum()
                precip_monthly_values = precip_monthly.groupby(level=1).mean()  # Média dos totais mensais
                
                # Define dia chuvoso como >= 1mm (conforme INMET)
                rainy_days = (precip_data >= 1.0)
                
                eto_stats.update({
                    # Normais mensais - GRUPO II (Totais)
                    'precip_normal': float(precip_monthly_values.get(month, np.nan)),
                    
                    # Estatísticas de totais diários
                    'precip_daily_mean': precip_data.mean(),
                    'precip_daily_median': precip_data.median(),
                    'precip_daily_std': precip_data.std(),
                    
                    # Percentis de totais diários
                    'precip_p95': precip_data.quantile(0.95),
                    'precip_p99': precip_data.quantile(0.99),
                    'precip_max': precip_data.max(),
                    
                    # Dias de chuva/seca
                    'rain_days': int(rainy_days.sum()),
                    'dry_days': len(precip_data) - int(rainy_days.sum()),
                    'rain_probability': rainy_days.mean(),
                    
                    # Intensidade de chuva
                    'precip_intensity': precip_data[rainy_days].mean() if rainy_days.any() else 0,
                    
                    # Metadados específicos
                    'precip_data_type': 'daily_totals'  # Grupo II - Valores acumulados
                })
            
            monthly_stats[month] = eto_stats
        
        return monthly_stats

    def _compute_annual_normals_inmet(self, data: pd.DataFrame, period_name: str) -> Dict:
        """
        Calcula normais anuais: Mensais → Anuais
        Fórmula INMET: n(X) = Σ_j X_ij / m_i, onde m_i = anos válidos
        """
        annual_stats = {}
        
        # Agregação anual - GRUPO I (ETo)
        eto_annual = data.groupby(data.index.year)['ETo'].mean()
        valid_years_eto = eto_annual.count()
        
        # Agregação anual - GRUPO II (Precipitação)
        if 'precipitation' in data.columns:
            precip_annual = data.groupby(data.index.year)['precipitation'].sum()
            valid_years_precip = precip_annual.count()
        else:
            precip_annual = pd.Series(dtype=float)
            valid_years_precip = 0
        
        # Usa o menor número de anos válidos entre as variáveis
        valid_years = min(valid_years_eto, valid_years_precip) if precip_annual.any() else valid_years_eto
        
        if valid_years >= 10:  # Mínimo 10 anos conforme OMM
            annual_stats.update({
                # Normais anuais (arredondamento INMET)
                'eto_normal': round(eto_annual.mean(), 1) if not eto_annual.empty else None,  # 1 casa decimal
                'precip_normal': round(precip_annual.mean(), 0) if precip_annual.any() else None,  # 0 casas decimais
                
                # Estatísticas anuais
                'eto_annual_mean': eto_annual.mean() if not eto_annual.empty else None,
                'eto_annual_std': eto_annual.std() if not eto_annual.empty else None,
                'precip_annual_mean': precip_annual.mean() if precip_annual.any() else None,
                'precip_annual_std': precip_annual.std() if precip_annual.any() else None,
                
                # Metadados
                'valid_years': int(valid_years),
                'completeness_ratio': valid_years / 30,  # 30 anos esperados
                'period': period_name
            })
        
        return annual_stats

    def compute_annual_normals(self) -> Dict[str, Dict]:
        """
        Calcula normais anuais para todos os períodos
        """
        print("\n📈 CALCULANDO NORMAIS ANUAIS")
        print("=" * 50)
        
        annual_normals = {}
        
        for period_name in self.REFERENCE_PERIODS.keys():
            period_data = self.all_period_normals.get(period_name, {})
            annual_data = {}
            
            for city_key, city_data in period_data.items():
                annual_stats = city_data.get('annual', {})
                if annual_stats:
                    annual_data[city_key] = annual_stats
            
            annual_normals[period_name] = annual_data
            valid_cities = len(annual_data)
            print(f"📊 {period_name}: {valid_cities} cidades com normais anuais válidas")
        
        return annual_normals

    # CORREÇÃO: Método renomeado para compatibilidade
    def calculate_extreme_thresholds(self) -> Dict:
        """Alias para compute_etccdi_thresholds para compatibilidade"""
        return self.compute_etccdi_thresholds()
    
    def compute_etccdi_thresholds(self) -> Dict:
        """
        Calcula limiares de extremos conforme ETCCDI
        """
        thresholds = {}
        
        for city_key, data in self.historical_data.items():
            print(f"📊 Calculando extremos ETCCDI para {city_key}...")
            
            try:
                # Usa período de referência para consistência
                ref_data = data[
                    (data.index >= self.reference_period[0]) & 
                    (data.index <= self.reference_period[1])
                ]
                
                if len(ref_data) == 0:
                    continue
                
                city_thresholds = {
                    'ETo': {
                        # Índices de extremos de temperatura (adaptados para ETo)
                        'TXx': ref_data['ETo'].max(),  # Máximo da máxima mensal
                        'TNn': ref_data['ETo'].min(),  # Mínimo da mínima mensal
                        
                        # Percentis para dias extremos (ETCCDI)
                        'p01': ref_data['ETo'].quantile(0.01),  # Dias extremamente frios
                        'p99': ref_data['ETo'].quantile(0.99),  # Dias extremamente quentes
                        
                        # Limiares absolutos
                        'absolute_max': ref_data['ETo'].max(),
                        'absolute_min': ref_data['ETo'].min(),
                        
                        # Estatísticas de base
                        'mean': ref_data['ETo'].mean(),
                        'std': ref_data['ETo'].std()
                    }
                }
                
                # Índices de precipitação se disponível
                if 'precipitation' in ref_data.columns and not ref_data['precipitation'].isna().all():
                    precip_data = ref_data['precipitation'].dropna()
                    
                    city_thresholds['precipitation'] = {
                        # Índices de extremos de precipitação (ETCCDI)
                        'RX1day': precip_data.max(),  # Máximo de 1 dia
                        'R95p': precip_data.quantile(0.95),  # Percentil 95
                        'R99p': precip_data.quantile(0.99),  # Percentil 99
                        
                        # Índices de duração
                        'CDD': self._calculate_cdd(precip_data),  # Máximo de dias secos consecutivos
                        'CWD': self._calculate_cwd(precip_data),  # Máximo de dias úmidos consecutivos
                        
                        # Estatísticas básicas
                        'mean': precip_data.mean(),
                        'std': precip_data.std(),
                        'rain_probability': (precip_data > 0.1).mean()
                    }
                
                thresholds[city_key] = city_thresholds
                
            except Exception as e:
                print(f"❌ Erro ao calcular extremos para {city_key}: {e}")
                continue
        
        return thresholds
    
    def _calculate_cdd(self, precip_data: pd.Series) -> int:
        """Calcula CDD (Consecutive Dry Days) conforme ETCCDI"""
        try:
            dry_days = (precip_data < 1.0)  # < 1mm = dia seco (ETCCDI)
            dry_spells = dry_days.astype(int).groupby((~dry_days).cumsum()).sum()
            return dry_spells.max() if len(dry_spells) > 0 else 0
        except:
            return 0
    
    def _calculate_cwd(self, precip_data: pd.Series) -> int:
        """Calcula CWD (Consecutive Wet Days) conforme ETCCDI"""
        try:
            wet_days = (precip_data >= 1.0)  # ≥ 1mm = dia úmido (ETCCDI)
            wet_spells = wet_days.astype(int).groupby((~wet_days).cumsum()).sum()
            return wet_spells.max() if len(wet_spells) > 0 else 0
        except:
            return 0
    
    def compute_spi_classification(self) -> Dict:
        """
        Calcula classificação SPI (Standardized Precipitation Index) 
        """
        spi_data = {}
        
        for city_key, data in self.historical_data.items():
            if 'precipitation' not in data.columns:
                continue
                
            try:
                precip_data = data['precipitation'].dropna()
                
                if len(precip_data) < 365:  # Mínimo 1 ano de dados
                    continue
                    
                # Calcula SPI para escala de 12 meses (anual)
                spi_12 = self._calculate_spi(precip_data, scale=12)
                
                if len(spi_12) == 0:
                    continue
                
                # CORREÇÃO: Agrupa por ano corretamente
                # Cria DataFrame temporário para agrupamento
                spi_df = pd.DataFrame({'spi': spi_12, 'year': spi_12.index.year})
                
                # Calcula média anual do SPI
                yearly_spi = spi_df.groupby('year')['spi'].mean()
                
                classification = {}
                for year, spi in yearly_spi.items():
                    if np.isnan(spi):
                        continue
                        
                    if spi >= 2.0:
                        classification[year] = 'extremely_wet'
                    elif spi >= 1.5:
                        classification[year] = 'very_wet'
                    elif spi >= 1.0:
                        classification[year] = 'moderately_wet'
                    elif spi >= -0.99:
                        classification[year] = 'near_normal'
                    elif spi >= -1.49:
                        classification[year] = 'moderately_dry'
                    elif spi >= -1.99:
                        classification[year] = 'severely_dry'
                    else:
                        classification[year] = 'extremely_dry'
                
                spi_data[city_key] = classification
                
            except Exception as e:
                print(f"❌ Erro ao calcular SPI para {city_key}: {e}")
                continue
        
        return spi_data

    def _calculate_spi(self, precip_data: pd.Series, scale: int = 12) -> pd.Series:
        """Calcula SPI conforme McKee et al. (1993)"""
        try:
            # Agrega precipitação no scale mensal
            precip_roll = precip_data.rolling(window=scale, min_periods=scale).sum()
            
            # Remove valores com menos de scale meses
            precip_roll = precip_roll[precip_roll.notna()]
            
            if len(precip_roll) == 0:
                return pd.Series([], dtype=float)
            
            # Ajusta distribuição gamma (McKee et al. 1993)
            # Usamos método MLE (Maximum Likelihood Estimation)
            try:
                params = stats.gamma.fit(precip_roll, method='MLE')
            except:
                # Fallback para método MM (Method of Moments)
                params = stats.gamma.fit(precip_roll, method='MM')
            
            # Calcula probabilidade acumulada
            cdf = stats.gamma.cdf(precip_roll, *params)
            
            # Evita valores 0 ou 1 que causam problemas com ppf
            cdf = np.clip(cdf, 0.0001, 0.9999)
            
            # Transforma para distribuição normal padrão
            spi_values = stats.norm.ppf(cdf)
            
            # CORREÇÃO: Retorna como Series do pandas mantendo o índice original
            spi_series = pd.Series(spi_values, index=precip_roll.index, name='SPI')
            
            return spi_series
            
        except Exception as e:
            print(f"❌ Erro no cálculo do SPI: {e}")
            return pd.Series([], dtype=float)
    
    def classify_hydrological_years(self) -> Dict:
        """
        Classifica anos hidrológicos (secos/normais/úmidos)
        """
        regimes = {}
        
        for city_key, data in self.historical_data.items():
            if 'precipitation' not in data.columns:
                continue
                
            try:
                # Agrupa por ano hidrológico (outubro a setembro)
                hydrological_years = self._calculate_hydrological_years(data)
                annual_precip = hydrological_years.groupby('hydrological_year')['precipitation'].sum()
                
                # Classificação baseada em percentis (Wilks, 2011)
                dry_threshold = annual_precip.quantile(0.33)  # Percentil 33
                wet_threshold = annual_precip.quantile(0.67)  # Percentil 67
                
                year_regimes = {}
                for year, precip in annual_precip.items():
                    if precip <= dry_threshold:
                        year_regimes[year] = 'dry'
                    elif precip >= wet_threshold:
                        year_regimes[year] = 'wet'
                    else:
                        year_regimes[year] = 'normal'
                
                regimes[city_key] = year_regimes
                
            except Exception as e:
                print(f"❌ Erro ao classificar anos hidrológicos para {city_key}: {e}")
                continue
        
        return regimes
    
    def _calculate_hydrological_years(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calcula anos hidrológicos (outubro a setembro)"""
        data_copy = data.copy()
        data_copy['hydrological_year'] = data_copy.index.year
        data_copy.loc[data_copy.index.month >= 10, 'hydrological_year'] += 1
        return data_copy
    
    def is_climate_extreme(self, city_key: str, variable: str, value: float, date: str) -> Dict:
        """
        Verifica se um valor é extremo climático ou outlier com base científico
        """
        if city_key not in self.extreme_thresholds:
            return {'is_extreme': False, 'confidence': 0.0, 'reason': 'unknown_city'}
        
        thresholds = self.extreme_thresholds[city_key].get(variable)
        if not thresholds:
            return {'is_extreme': False, 'confidence': 0.0, 'reason': f'unknown_variable_{variable}'}
        
        try:
            month = pd.to_datetime(date).month
            
            # CORREÇÃO: Acessa as normais corretamente da nova estrutura INMET
            city_normals = self.climate_normals.get(city_key, {})
            if not city_normals:
                return {'is_extreme': False, 'confidence': 0.0, 'reason': 'no_climate_normals'}
            
            monthly_normals = city_normals.get('monthly', {})
            if month not in monthly_normals:
                return {'is_extreme': False, 'confidence': 0.0, 'reason': f'no_normals_for_month_{month}'}
            
            seasonal_normals = monthly_normals[month]
            
            # Para precipitação, tratamento especial para valores zero
            if variable == 'precipitation' and value == 0:
                rain_probability = seasonal_normals.get('rain_probability', 0.5)
                return {
                    'is_extreme': False,
                    'confidence': 0.9,
                    'reason': 'no_precipitation_normal',
                    'rain_probability': rain_probability,
                    'methodology': 'ETCCDI dry day definition'
                }
            
            # 1. Verificação de Outlier Estatístico (Wilks, 2011)
            # CORREÇÃO: Usa daily_std em vez de std
            daily_std = seasonal_normals.get('daily_std') if variable == 'ETo' else seasonal_normals.get('precip_daily_std')
            daily_mean = seasonal_normals.get('daily_mean') if variable == 'ETo' else seasonal_normals.get('precip_daily_mean')
            
            if daily_std is None or daily_mean is None or daily_std == 0:
                return {'is_extreme': False, 'confidence': 0.0, 'reason': 'insufficient_statistics'}
            
            z_score = abs(value - daily_mean) / daily_std
            if z_score > 3.5:  # 3.5 sigma - outlier estatístico
                return {
                    'is_extreme': False, 
                    'confidence': 0.95, 
                    'reason': 'statistical_outlier',
                    'z_score': z_score,
                    'methodology': 'Wilks (2011) statistical outlier detection'
                }
            
            # 2. Verificação de Extremo Climático (ETCCDI)
            if value > thresholds.get('p99', np.inf):
                similar_events = self._count_similar_events(city_key, variable, value, month, 'high')
                return {
                    'is_extreme': True,
                    'confidence': min(0.9, 0.5 + similar_events * 0.1),
                    'reason': f'extreme_high_{variable}',
                    'percentile': 99,
                    'historical_context': f"Valores > {value:.1f} ocorreram {similar_events} vezes em {self._get_month_name(month)}",
                    'current_vs_normal': f"{value/daily_mean:.1f}x acima da média mensal",
                    'methodology': 'ETCCDI p99 threshold (Sillmann et al. 2013)'
                }
            
            if value < thresholds.get('p01', -np.inf):
                similar_events = self._count_similar_events(city_key, variable, value, month, 'low')
                return {
                    'is_extreme': True,
                    'confidence': min(0.9, 0.5 + similar_events * 0.1),
                    'reason': f'extreme_low_{variable}',
                    'percentile': 1,
                    'historical_context': f"Valores < {value:.1f} ocorreram {similar_events} vezes em {self._get_month_name(month)}",
                    'current_vs_normal': f"{value/daily_mean:.1f}x abaixo da média mensal",
                    'methodology': 'ETCCDI p01 threshold (Sillmann et al. 2013)'
                }
            
            # 3. Dentro da faixa normal
            return {
                'is_extreme': False,
                'confidence': 0.95,
                'reason': 'within_normal_range',
                'percentile': self._calculate_percentile(city_key, variable, value, month),
                'z_score': z_score,
                'methodology': 'WMO-1203 climate normal range'
            }
            
        except Exception as e:
            return {'is_extreme': False, 'confidence': 0.0, 'reason': f'error: {str(e)}'}


    
    def _count_similar_events(self, city_key: str, variable: str, value: float, month: int, direction: str) -> int:
        """Conta eventos similares no histórico"""
        try:
            data = self.historical_data[city_key]
            month_data = data[data.index.month == month]
            
            if direction == 'high':
                similar = month_data[month_data[variable] >= value * 0.95]
            else:  # low
                similar = month_data[month_data[variable] <= value * 1.05]
            
            return len(similar)
        except:
            return 0
    
    def _calculate_percentile(self, city_key: str, variable: str, value: float, month: int) -> float:
        """Calcula o percentil do valor no histórico mensal"""
        try:
            data = self.historical_data[city_key]
            month_data = data[data.index.month == month]
            
            if variable == 'ETo':
                series_data = month_data['ETo']
            elif variable == 'precipitation' and 'precipitation' in month_data.columns:
                series_data = month_data['precipitation'].dropna()
            else:
                return 50.0
                
            if len(series_data) == 0:
                return 50.0
                
            return stats.percentileofscore(series_data, value)
        except:
            return 50.0
    
    def _get_month_name(self, month: int) -> str:
        """Retorna nome do mês em português"""
        months_pt = [
            'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
            'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
        ]
        return months_pt[month - 1]
    
    def generate_scientific_report(self, city_key: str) -> Dict:
        """
        Gera relatório científico completo de uma cidade
        incluindo todos os períodos de normais INMET.
        """
        try:
            # Coleta normais anuais para todos os períodos
            annual_comparison = {}
            for period_name in self.REFERENCE_PERIODS.keys():
                period_annual = self.annual_normals.get(period_name, {}).get(city_key, {})
                if period_annual:
                    annual_comparison[period_name] = {
                        'eto_normal_mm_day': period_annual.get('eto_normal'),
                        'precip_normal_mm_year': period_annual.get('precip_normal'),
                        'valid_years': period_annual.get('valid_years'),
                        'completeness': period_annual.get('completeness_ratio')
                    }
            
            report = {
                'city': city_key,
                'reference_period': self.reference_period,
                'reference_period_key': self.reference_period_key,
                'total_records': len(self.historical_data[city_key]),
                'data_period': f"{self.historical_data[city_key].index.min().year}-{self.historical_data[city_key].index.max().year}",
                
                # Normais climatológicas para todos os períodos INMET
                'climate_normals_all_periods': {
                    period: norms.get(city_key, {}) 
                    for period, norms in self.all_period_normals.items()
                },
                
                # Comparação de normais anuais entre períodos
                'annual_normals_comparison': annual_comparison,
                
                # Normais do período de referência selecionado (para compatibilidade)
                'climate_normals': self.climate_normals.get(city_key, {}),
                
                # Extremos climáticos (ETCCDI)
                'extreme_thresholds': self.extreme_thresholds.get(city_key, {}),
                
                # Classificação de secas (SPI - McKee et al. 1993)
                'spi_classification': self.spi_classification.get(city_key, {}),
                
                # Regimes hidrológicos (Palmer 1965 adaptado)
                'hydrological_regimes': self.hydrological_regimes.get(city_key, {}),
                
                # Metodologias aplicadas
                'methodologies': {
                    'normals': 'INMET/OMM WMO-1203 (2018) - Normais Climatológicas do Brasil',
                    'aggregation': 'Diários → Mensais (ETo: média, Precip: soma) → Anuais (média)',
                    'extremes': 'ETCCDI - Sillmann et al. (2013)',
                    'drought': 'SPI - McKee et al. (1993)',
                    'statistics': 'Wilks (2011) - Statistical Methods in Atmospheric Sciences',
                    'eto_reference': 'Allen et al. (1998) - FAO-56',
                    'reference_periods': 'Padrão INMET: 1961-1990, 1981-2010, 1991-2020',
                    'min_valid_years': '10 anos (mínimo OMM)',
                    'rounding': 'ETo: 1 casa decimal, Precip: 0 casas decimais'
                },
                
                # Estatísticas de qualidade
                'quality_metrics': self._calculate_quality_metrics(city_key)
            }
            
            return report
        except Exception as e:
            return {'error': f'Erro ao gerar relatório: {str(e)}'}
    
    def _calculate_quality_metrics(self, city_key: str) -> Dict:
        """Calcula métricas de qualidade dos dados"""
        data = self.historical_data[city_key]
        
        return {
            'completeness': len(data) / ((2024-1961+1) * 365),  # % de completude
            'missing_days': data['ETo'].isna().sum(),
            'period_covered': f"{data.index.min().date()} to {data.index.max().date()}",
            'variables_available': self.get_city_variables(city_key)
        }
    
    def get_available_cities(self) -> List[str]:
        """Retorna lista de cidades disponíveis"""
        return list(self.historical_data.keys())
    
    def get_city_variables(self, city_key: str) -> List[str]:
        """Retorna variáveis disponíveis para uma cidade"""
        variables = ['ETo']  # ETo sempre disponível
        if 'precipitation' in self.historical_data[city_key].columns:
            variables.append('precipitation')
        return variables