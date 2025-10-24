# scripts/analysis/test_scientific_metadata.py
import json
import os
import sys
from datetime import datetime

import numpy as np
import pandas as pd

# Adiciona o diretório pai ao path para importar climate_metadata
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from climate_metadata import ScientificClimateMetadataRegistry


def save_city_reports(metadata, output_dir='./reports'):
    """Salva relatórios completos para todas as cidades"""
    
    # Cria diretório de saída se não existir
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, 'cities'), exist_ok=True)
    os.makedirs(os.path.join(output_dir, 'summary'), exist_ok=True)
    
    print(f"\n💾 Salvando relatórios em: {os.path.abspath(output_dir)}")
    
    all_cities_summary = []
    extreme_events_summary = []
    annual_normals_summary = []
    
    for i, city_key in enumerate(metadata.get_available_cities(), 1):
        print(f"\n📊 Processando cidade {i}/{len(metadata.historical_data)}: {city_key}")
        
        # Gera relatório científico completo
        city_report = metadata.generate_scientific_report(city_key)
        
        # Salva relatório individual da cidade
        city_filename = f"report_{city_key.replace(' ', '_')}.json"
        city_filepath = os.path.join(output_dir, 'cities', city_filename)
        
        with open(city_filepath, 'w', encoding='utf-8') as f:
            json.dump(city_report, f, indent=2, ensure_ascii=False, default=str)
        
        # Adiciona ao resumo geral
        city_summary = {
            'city': city_key,
            'region': metadata.historical_data[city_key]['region'].iloc[0],
            'lat': metadata.historical_data[city_key]['lat'].iloc[0],
            'lon': metadata.historical_data[city_key]['lon'].iloc[0],
            'alt': metadata.historical_data[city_key]['alt'].iloc[0],
            'total_records': city_report['total_records'],
            'data_period': city_report['data_period'],
            'variables': city_report['quality_metrics']['variables_available'],
            'completeness': city_report['quality_metrics']['completeness']
        }
        
        # Adiciona estatísticas de ETo se disponível
        if 'ETo' in metadata.extreme_thresholds.get(city_key, {}):
            eto_stats = metadata.extreme_thresholds[city_key]['ETo']
            city_summary.update({
                'eto_mean': eto_stats.get('mean'),
                'eto_std': eto_stats.get('std'),
                'eto_max': eto_stats.get('TXx'),
                'eto_min': eto_stats.get('TNn'),
                'eto_p99': eto_stats.get('p99'),
                'eto_p01': eto_stats.get('p01')
            })
        
        all_cities_summary.append(city_summary)
        
        # Coleta eventos extremos para análise
        extreme_analysis = analyze_city_extremes(metadata, city_key)
        extreme_events_summary.append(extreme_analysis)
        
        # Coleta normais anuais para comparação entre períodos
        annual_comparison = city_report.get('annual_normals_comparison', {})
        for period, norms in annual_comparison.items():
            annual_normals_summary.append({
                'city': city_key,
                'period': period,
                'eto_normal_mm_day': norms.get('eto_normal_mm_day'),
                'precip_normal_mm_year': norms.get('precip_normal_mm_year'),
                'valid_years': norms.get('valid_years'),
                'completeness': norms.get('completeness')
            })
        
        print(f"✅ Relatório salvo: {city_filename}")
    
    # Salva resumo geral em CSV
    summary_df = pd.DataFrame(all_cities_summary)
    summary_csv_path = os.path.join(output_dir, 'summary', 'cities_summary.csv')
    summary_df.to_csv(summary_csv_path, index=False, encoding='utf-8')
    
    # Salva análise de extremos
    extremes_df = pd.DataFrame(extreme_events_summary)
    extremes_csv_path = os.path.join(output_dir, 'summary', 'extremes_analysis.csv')
    extremes_df.to_csv(extremes_csv_path, index=False, encoding='utf-8')
    
    # Salva comparação de normais anuais
    annual_normals_df = pd.DataFrame(annual_normals_summary)
    annual_normals_csv_path = os.path.join(output_dir, 'summary', 'annual_normals_comparison.csv')
    annual_normals_df.to_csv(annual_normals_csv_path, index=False, encoding='utf-8')
    
    # Salva metadados do processo
    metadata_report = {
        'generation_date': datetime.now().isoformat(),
        'total_cities': len(metadata.historical_data),
        'reference_period': metadata.reference_period,
        'reference_period_key': metadata.reference_period_key,
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
        'summary_statistics': {
            'total_records': sum(city['total_records'] for city in all_cities_summary),
            'cities_with_precipitation': sum(1 for city in all_cities_summary if 'precipitation' in city['variables']),
            'average_completeness': np.mean([city['completeness'] for city in all_cities_summary]),
            'period_covered': f"{min(city['data_period'] for city in all_cities_summary)} to {max(city['data_period'] for city in all_cities_summary)}"
        }
    }
    
    metadata_filepath = os.path.join(output_dir, 'summary', 'generation_metadata.json')
    with open(metadata_filepath, 'w', encoding='utf-8') as f:
        json.dump(metadata_report, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n🎉 Processo concluído!")
    print(f"📁 Relatórios individuais: {output_dir}/cities/")
    print(f"📊 Resumos gerais: {output_dir}/summary/")
    print(f"📈 Comparação de normais anuais: {output_dir}/summary/annual_normals_comparison.csv")
    print(f"🏙️  Total de cidades processadas: {len(metadata.historical_data)}")
    
    return all_cities_summary


def analyze_city_extremes(metadata, city_key):
    """Analisa eventos extremos para uma cidade específica"""
    
    data = metadata.historical_data[city_key]
    thresholds = metadata.extreme_thresholds.get(city_key, {})
    
    analysis = {
        'city': city_key,
        'total_days': len(data)
    }
    
    # Análise de extremos de ETo
    if 'ETo' in thresholds:
        eto_data = data['ETo']
        eto_thresholds = thresholds['ETo']
        
        high_extremes = eto_data[eto_data > eto_thresholds.get('p99', np.inf)]
        low_extremes = eto_data[eto_data < eto_thresholds.get('p01', -np.inf)]
        
        analysis.update({
            'eto_high_extremes_count': len(high_extremes),
            'eto_low_extremes_count': len(low_extremes),
            'eto_total_extremes': len(high_extremes) + len(low_extremes),
            'eto_extreme_frequency': (len(high_extremes) + len(low_extremes)) / len(data) * 100,
            'eto_max_value': eto_data.max(),
            'eto_min_value': eto_data.min(),
            'eto_high_extremes_years': count_years_with_extremes(high_extremes),
            'eto_low_extremes_years': count_years_with_extremes(low_extremes)
        })
    
    # Análise de extremos de precipitação
    if 'precipitation' in thresholds and 'precipitation' in data.columns:
        precip_data = data['precipitation'].dropna()
        precip_thresholds = thresholds['precipitation']
        
        precip_extremes = precip_data[precip_data > precip_thresholds.get('R95p', np.inf)]
        
        analysis.update({
            'precip_extremes_count': len(precip_extremes),
            'precip_extreme_frequency': len(precip_extremes) / len(precip_data) * 100,
            'precip_max_value': precip_data.max(),
            'precip_dry_spell_max': precip_thresholds.get('CDD', 0),
            'precip_wet_spell_max': precip_thresholds.get('CWD', 0)
        })
    
    return analysis

def count_years_with_extremes(extreme_series):
    """Conta quantos anos tiveram pelo menos um evento extremo"""
    if len(extreme_series) == 0:
        return 0
    return extreme_series.index.year.nunique()

def test_extreme_detection_scenarios(metadata):
    """Testa cenários específicos de detecção de extremos"""
    
    print("\n🧪 TESTANDO CENÁRIOS DE DETECÇÃO DE EXTREMOS")
    print("=" * 60)
    
    test_scenarios = [
        # (cidade, variável, valor, data, descrição)
        ('Alvorada_do_Gurgueia_PI', 'ETo', 4.5, '2020-06-15', 'Valor normal de ETo'),
        ('Alvorada_do_Gurgueia_PI', 'ETo', 8.5, '2020-01-15', 'ETo extremamente alta'),
        ('Alvorada_do_Gurgueia_PI', 'ETo', 1.2, '2020-07-20', 'ETo extremamente baixa'),
        ('Piracicaba_SP', 'ETo', 2.5, '2020-08-01', 'ETo moderada em Piracicaba'),
        ('Seville_Spain', 'ETo', 12.0, '2020-08-15', 'ETo alta em Seville'),
        ('Seville_Spain', 'ETo', 20.0, '2020-08-15', 'Possível outlier em Seville'),
    ]
    
    results = []
    
    for city, variable, value, date, description in test_scenarios:
        if city in metadata.historical_data:
            result = metadata.is_climate_extreme(city, variable, value, date)
            
            scenario_result = {
                'scenario': description,
                'city': city,
                'variable': variable,
                'value': value,
                'date': date,
                'is_extreme': result['is_extreme'],
                'confidence': result['confidence'],
                'reason': result['reason'],
                'methodology': result.get('methodology', 'N/A')
            }
            
            results.append(scenario_result)
            
            # Exibe resultado formatado
            status = "🔴 EXTREMO" if result['is_extreme'] else "🟢 NORMAL"
            print(f"\n{status} - {description}")
            print(f"   📍 {city} | {variable}: {value} | {date}")
            print(f"   📋 Razão: {result['reason']}")
            print(f"   🎯 Confiança: {result['confidence']:.2f}")
            if 'historical_context' in result:
                print(f"   📊 Contexto: {result['historical_context']}")
            print(f"   🔬 Metodologia: {result.get('methodology', 'N/A')}")
        else:
            print(f"\n❌ Cidade não encontrada: {city}")
    
    return results

def generate_comprehensive_analysis(metadata, output_dir='../reports'):
    """Gera análise compreensiva do dataset completo"""
    
    print("\n📈 GERANDO ANÁLISE COMPREENSIVA")
    print("=" * 50)
    
    analysis = {
        'dataset_overview': {
            'total_cities': len(metadata.historical_data),
            'cities_brasil': len([c for c in metadata.historical_data.keys() if metadata.historical_data[c]['region'].iloc[0] == 'brasil']),
            'cities_global': len([c for c in metadata.historical_data.keys() if metadata.historical_data[c]['region'].iloc[0] == 'global']),
            'total_records': sum(len(data) for data in metadata.historical_data.values()),
            'date_range_start': min(data.index.min() for data in metadata.historical_data.values()),
            'date_range_end': max(data.index.max() for data in metadata.historical_data.values())
        },
        'variable_analysis': {
            'cities_with_eto': len(metadata.historical_data),
            'cities_with_precipitation': sum(1 for data in metadata.historical_data.values() if 'precipitation' in data.columns and not data['precipitation'].isna().all())
        },
        'extreme_events_global': analyze_global_extremes(metadata),
        'annual_normals_summary': analyze_annual_normals_trends(metadata)
    }
    
    # Salva análise compreensiva
    analysis_filepath = os.path.join(output_dir, 'summary', 'comprehensive_analysis.json')
    with open(analysis_filepath, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"✅ Análise compreensiva salva: {analysis_filepath}")
    
    return analysis

def analyze_annual_normals_trends(metadata):
    """Analisa tendências nas normais anuais entre períodos"""
    
    trends_analysis = {}
    
    if hasattr(metadata, 'annual_normals'):
        for period_name, cities_data in metadata.annual_normals.items():
            period_trends = {
                'total_cities': len(cities_data),
                'eto_values': [],
                'precip_values': []
            }
            
            for city_key, annual_data in cities_data.items():
                eto_norm = annual_data.get('eto_normal')
                precip_norm = annual_data.get('precip_normal')
                
                if eto_norm is not None:
                    period_trends['eto_values'].append(eto_norm)
                if precip_norm is not None:
                    period_trends['precip_values'].append(precip_norm)
            
            # Calcula estatísticas do período
            if period_trends['eto_values']:
                period_trends['eto_mean'] = np.mean(period_trends['eto_values'])
                period_trends['eto_std'] = np.std(period_trends['eto_values'])
            if period_trends['precip_values']:
                period_trends['precip_mean'] = np.mean(period_trends['precip_values'])
                period_trends['precip_std'] = np.std(period_trends['precip_values'])
            
            trends_analysis[period_name] = period_trends
    
    return trends_analysis

def analyze_global_extremes(metadata):
    """Analisa extremos em todo o dataset"""
    
    global_extremes = {
        'highest_eto': {'value': -np.inf, 'city': '', 'date': ''},
        'lowest_eto': {'value': np.inf, 'city': '', 'date': ''},
        'highest_precipitation': {'value': -np.inf, 'city': '', 'date': ''},
        'cities_most_extremes': []
    }
    
    for city_key, data in metadata.historical_data.items():
        # Encontra extremos globais de ETo
        max_eto_idx = data['ETo'].idxmax()
        min_eto_idx = data['ETo'].idxmin()
        
        if data['ETo'].max() > global_extremes['highest_eto']['value']:
            global_extremes['highest_eto'] = {
                'value': data['ETo'].max(),
                'city': city_key,
                'date': max_eto_idx.strftime('%Y-%m-%d')
            }
        
        if data['ETo'].min() < global_extremes['lowest_eto']['value']:
            global_extremes['lowest_eto'] = {
                'value': data['ETo'].min(),
                'city': city_key,
                'date': min_eto_idx.strftime('%Y-%m-%d')
            }
        
        # Encontra extremos de precipitação
        if 'precipitation' in data.columns:
            precip_data = data['precipitation'].dropna()
            if len(precip_data) > 0:
                max_precip_idx = precip_data.idxmax()
                if precip_data.max() > global_extremes['highest_precipitation']['value']:
                    global_extremes['highest_precipitation'] = {
                        'value': precip_data.max(),
                        'city': city_key,
                        'date': max_precip_idx.strftime('%Y-%m-%d')
                    }
    
    return global_extremes


def load_data_from_new_structure(data_dir):
    """Carrega dados da nova estrutura de pastas"""
    
    print(f"\n📁 Carregando dados da estrutura: {data_dir}")
    
    # Mapeamento das pastas
    data_structure = {
        'brasil': {
            'ETo': os.path.join(data_dir, 'csv', 'BRASIL', 'ETo'),
            'precipitation': os.path.join(data_dir, 'csv', 'BRASIL', 'pr')
        },
        'global': {
            'ETo': os.path.join(data_dir, 'csv', 'MUNDO', 'ETo'),
            'precipitation': os.path.join(data_dir, 'csv', 'MUNDO', 'pr')
        }
    }
    
    all_data = {}
    
    for region, folders in data_structure.items():
        print(f"\n🌍 Processando região: {region.upper()}")
        
        # Carrega arquivos ETo
        eto_folder = folders['ETo']
        if os.path.exists(eto_folder):
            print(f"   📂 Lendo ETo de: {eto_folder}")
            for file in os.listdir(eto_folder):
                if file.endswith('.csv'):
                    city_name = file.replace('.csv', '')
                    file_path = os.path.join(eto_folder, file)
                    
                    try:
                        # Lê o arquivo CSV
                        df = pd.read_csv(file_path)
                        
                        # Verifica se a coluna 'Data' existe (com D maiúsculo)
                        if 'Data' in df.columns:
                            df['date'] = pd.to_datetime(df['Data'])
                            df.set_index('date', inplace=True)
                            # Remove a coluna original 'Data' se existir
                            if 'Data' in df.columns:
                                df = df.drop('Data', axis=1)
                        elif 'date' in df.columns:
                            df['date'] = pd.to_datetime(df['date'])
                            df.set_index('date', inplace=True)
                        else:
                            print(f"   ⚠️  Coluna de data não encontrada em {file}")
                            continue
                        
                        # Renomeia coluna ETo se necessário
                        if 'ETo' not in df.columns and 'eto' in df.columns:
                            df = df.rename(columns={'eto': 'ETo'})
                        
                        df['region'] = region
                        
                        # Adiciona coordenadas padrão (serão atualizadas posteriormente)
                        df['lat'] = 0.0
                        df['lon'] = 0.0
                        df['alt'] = 0.0
                        
                        # Adiciona precipitação se disponível
                        precip_folder = folders['precipitation']
                        precip_file = os.path.join(precip_folder, file)
                        if os.path.exists(precip_file):
                            try:
                                precip_df = pd.read_csv(precip_file)
                                
                                # Verifica coluna de data no arquivo de precipitação
                                if 'Data' in precip_df.columns:
                                    precip_df['date'] = pd.to_datetime(precip_df['Data'])
                                    precip_df.set_index('date', inplace=True)
                                    if 'Data' in precip_df.columns:
                                        precip_df = precip_df.drop('Data', axis=1)
                                elif 'date' in precip_df.columns:
                                    precip_df['date'] = pd.to_datetime(precip_df['date'])
                                    precip_df.set_index('date', inplace=True)
                                
                                # Combina ETo e precipitação
                                if 'precipitation' in precip_df.columns:
                                    df['precipitation'] = precip_df['precipitation']
                                elif 'pr' in precip_df.columns:
                                    df['precipitation'] = precip_df['pr']
                                elif 'Precipitation' in precip_df.columns:
                                    df['precipitation'] = precip_df['Precipitation']
                                    
                                print(f"   ✅ {city_name}: {len(df)} registros (ETo + precipitação)")
                            except Exception as e:
                                print(f"   ⚠️  Erro ao carregar precipitação para {city_name}: {e}")
                                print(f"   ✅ {city_name}: {len(df)} registros (apenas ETo)")
                        else:
                            print(f"   ✅ {city_name}: {len(df)} registros (apenas ETo)")
                        
                        all_data[city_name] = df
                        
                    except Exception as e:
                        print(f"   ❌ Erro ao processar {file}: {e}")
        else:
            print(f"   ⚠️  Pasta não encontrada: {eto_folder}")
    
    return all_data


class AdaptedScientificClimateMetadataRegistry(
    ScientificClimateMetadataRegistry
):
    """Classe adaptada para trabalhar com a nova estrutura de dados"""
    
    def __init__(self, data_directory, reference_period='1991-2020'):
        # Chama o construtor da classe pai
        super().__init__(data_directory, reference_period)
        
        # Substitui o carregamento automático pelo nosso método
        self.historical_data = load_data_from_new_structure(data_directory)
        self.extreme_thresholds = self.calculate_extreme_thresholds()
        
    def get_available_cities(self):
        """Retorna lista de cidades disponíveis"""
        return list(self.historical_data.keys())
    

def main():
    """Função principal"""
    
    print("🔬 SISTEMA DE METADADOS CLIMÁTICOS CIENTÍFICOS - INMET/OMM")
    print("=" * 60)
    print("Metodologia INMET:")
    print("• Agregação: Diários → Mensais → Anuais")
    print("• ETo (Grupo I): Média diária → Média mensal → Média anual") 
    print("• Precipitação (Grupo II): Soma diária → Total mensal → Média anual")
    print("• Períodos: 1961-1990, 1981-2010, 1991-2020 (30 anos cada)")
    print("• Mínimo: 10 anos válidos por período")
    print("=" * 60)
    
    # Inicializa o sistema com período INMET
    print("\n🚀 Inicializando Scientific Climate Metadata Registry...")
    
    # Usa a classe adaptada com período INMET
    data_dir = './data'
    metadata = AdaptedScientificClimateMetadataRegistry(
        data_directory=data_dir,
        reference_period='1991-2020'  # Padrão INMET mais recente
    )
    
    print(f"\n✅ Sistema inicializado com {len(metadata.historical_data)} cidades")
    print(f"📅 Período de referência: {metadata.reference_period_key}")
    
    # Relatório de normais anuais
    print("\n📈 NORMAIS ANUAIS - COMPARAÇÃO ENTRE PERÍODOS")
    print("=" * 50)
    
    if hasattr(metadata, 'annual_normals') and metadata.annual_normals:
        for period_name, cities_data in metadata.annual_normals.items():
            valid_cities = len(cities_data)
            if valid_cities > 0:
                # Calcula médias para o período
                eto_values = [data.get('eto_normal') for data in cities_data.values() if data.get('eto_normal') is not None]
                precip_values = [data.get('precip_normal') for data in cities_data.values() if data.get('precip_normal') is not None]
                
                eto_mean = np.mean(eto_values) if eto_values else None
                precip_mean = np.mean(precip_values) if precip_values else None
                
                print(f"\n📊 {period_name}: {valid_cities} cidades válidas")
                if eto_mean:
                    print(f"   • ETo normal: {eto_mean:.1f} mm/dia")
                if precip_mean:
                    print(f"   • Precipitação normal: {precip_mean:.0f} mm/ano")
                
                # Mostra exemplos
                sample_cities = list(cities_data.items())[:2]
                for city_key, annual_data in sample_cities:
                    eto_norm = annual_data.get('eto_normal', 'N/A')
                    precip_norm = annual_data.get('precip_normal', 'N/A')
                    years = annual_data.get('valid_years', 0)
                    print(f"   • {city_key}: ETo={eto_norm} mm/dia, Precip={precip_norm} mm/ano ({years} anos)")
    else:
        print("❌ Nenhum dado de normais anuais disponível")
    
    if len(metadata.historical_data) == 0:
        print("❌ Nenhum dado foi carregado. Verifique a estrutura de pastas.")
        return
    
    # 1. Testa cenários de detecção de extremos
    test_results = test_extreme_detection_scenarios(metadata)
    
    # 2. Salva relatórios completos de todas as cidades
    cities_summary = save_city_reports(metadata)
    
    # 3. Gera análise compreensiva
    comprehensive_analysis = generate_comprehensive_analysis(metadata)
    
    # 4. Relatório final
    print("\n" + "=" * 60)
    print("🎉 RELATÓRIO FINAL - PROCESSO CONCLUÍDO")
    print("=" * 60)
    
    print(f"\n📊 ESTATÍSTICAS GERAIS:")
    print(f"   • Cidades processadas: {len(metadata.historical_data)}")
    print(f"   • Período de referência: {metadata.reference_period_key}")
    print(f"   • Total de registros: {comprehensive_analysis['dataset_overview']['total_records']:,}")
    print(f"   • Cidades com precipitação: {comprehensive_analysis['variable_analysis']['cities_with_precipitation']}")
    
    print(f"\n🌍 EXTREMOS GLOBAIS ENCONTRADOS:")
    print(f"   • Maior ETo: {comprehensive_analysis['extreme_events_global']['highest_eto']['value']:.2f} mm/dia")
    print(f"     Local: {comprehensive_analysis['extreme_events_global']['highest_eto']['city']}")
    print(f"     Data: {comprehensive_analysis['extreme_events_global']['highest_eto']['date']}")
    
    print(f"   • Menor ETo: {comprehensive_analysis['extreme_events_global']['lowest_eto']['value']:.2f} mm/dia")
    print(f"     Local: {comprehensive_analysis['extreme_events_global']['lowest_eto']['city']}")
    print(f"     Data: {comprehensive_analysis['extreme_events_global']['lowest_eto']['date']}")
    
    if comprehensive_analysis['extreme_events_global']['highest_precipitation']['value'] > -np.inf:
        print(f"   • Maior precipitação: {comprehensive_analysis['extreme_events_global']['highest_precipitation']['value']:.2f} mm")
        print(f"     Local: {comprehensive_analysis['extreme_events_global']['highest_precipitation']['city']}")
        print(f"     Data: {comprehensive_analysis['extreme_events_global']['highest_precipitation']['date']}")
    
    print(f"\n📈 TENDÊNCIAS DAS NORMAIS:")
    annual_trends = comprehensive_analysis.get('annual_normals_summary', {})
    for period_name, trends in annual_trends.items():
        if 'eto_mean' in trends:
            print(f"   • {period_name}: ETo {trends['eto_mean']:.1f} ± {trends['eto_std']:.1f} mm/dia")
        if 'precip_mean' in trends:
            print(f"     Precip {trends['precip_mean']:.0f} ± {trends['precip_std']:.0f} mm/ano")
    
    print(f"\n💾 ARQUIVOS GERADOS:")
    print(f"   • Relatórios individuais: ./reports/cities/")
    print(f"   • Resumos gerais: ./reports/summary/")
    print(f"   • Comparação de normais: ./reports/summary/annual_normals_comparison.csv")
    print(f"   • Análise compreensiva: ./reports/summary/comprehensive_analysis.json")
    
    print(f"\n🔬 METODOLOGIAS APLICADAS:")
    if metadata.historical_data:
        first_city = list(metadata.historical_data.keys())[0]
        report = metadata.generate_scientific_report(first_city)
        methodologies = report.get('methodologies', {})
        for method, ref in methodologies.items():
            if method in ['normals', 'aggregation', 'reference_periods', 'min_valid_years', 'rounding']:
                print(f"   • {method}: {ref}")

if __name__ == "__main__":
    main()