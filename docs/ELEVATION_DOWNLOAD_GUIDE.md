# Guia Rápido: Adicionar Elevações ao worldcities.csv

## 📋 Status

- **Total de cidades**: 48,060
- **Limite diário Open-Meteo**: 10,000 requisições
- **Estratégia**: Processar em lotes de ~9,500 cidades/dia

---

## 🚀 Uso Básico

### 1. Primeiro Lote (Hoje - 9,500 cidades)

```bash
# Ativar ambiente virtual
.\.venv\Scripts\activate

# Processar primeiro lote
python scripts/add_elevation_to_cities.py --batch 9500
```

**Tempo estimado**: ~17-20 minutos  
**Output**: `data/csv/worldcities_with_elevation.csv`

---

### 2. Verificar Progresso

```bash
python scripts/add_elevation_to_cities.py --check-progress
```

**Output**:
```
📊 PROGRESSO
====================================
Processadas: 9,500 / 48,060
Percentual: 19.77%
Restantes: 38,560
====================================
```

---

### 3. Continuar Amanhã (Lote 2)

```bash
# Continuar de onde parou (pula cidades já processadas)
python scripts/add_elevation_to_cities.py --batch 9500 --continue
```

**Repetir por 5 dias**:
- Dia 1: 9,500 cidades (19.77%)
- Dia 2: 9,500 cidades (39.54%)
- Dia 3: 9,500 cidades (59.31%)
- Dia 4: 9,500 cidades (79.08%)
- Dia 5: 9,560 cidades (100%) ✅

---

## 🎯 Características do Script

### ✅ **Funcionalidades:**

1. **Rate Limiting Inteligente**
   - 0.11s delay entre requisições
   - ~9 req/s = 540 req/min (seguro para 600/min)
   - Respeita limite diário de 10k

2. **Fallback Automático**
   - Tenta Open-Meteo primeiro
   - Se falhar, usa Open-Elevation (sem limite)
   - Garante 100% de cobertura

3. **Continuar de Onde Parou**
   - Flag `--continue` pula cidades já processadas
   - Pode interromper e retomar a qualquer momento

4. **Logs Detalhados**
   - Progresso a cada 100 cidades
   - ETA (tempo restante estimado)
   - Taxa de processamento
   - Estatísticas finais

5. **Estatísticas**
   - Total de requisições
   - Requisições por API (Open-Meteo vs Open-Elevation)
   - Erros
   - Tempo total

---

## 📊 Formato do Output

### Input (worldcities.csv):
```csv
city,lat,long,country,sigla
Tokyo,35.6870,139.7495,Japan,JPN
Jakarta,-6.1750,106.8275,Indonesia,IDN
```

### Output (worldcities_with_elevation.csv):
```csv
city,lat,long,country,sigla,elevation
Tokyo,35.687,139.7495,Japan,JPN,40.2
Jakarta,-6.175,106.8275,Indonesia,IDN,8.5
```

---

## 🛡️ APIs Utilizadas

### Open-Meteo (Principal)
```
✅ Limite: 10k/dia, 5k/hora, 600/min
✅ Dados: Copernicus DEM 90m
✅ Precisão: ±5-10m
✅ Custo: GRÁTIS
```

### Open-Elevation (Backup)
```
✅ Sem limite oficial
✅ Dados: SRTM 30m (NASA)
✅ Cobertura: -56° a 60° latitude
✅ Custo: GRÁTIS
```

---

## ⏱️ Cronograma

### Dia 1 (Hoje)
```bash
python scripts/add_elevation_to_cities.py --batch 9500
```
**Resultado**: 9,500 cidades (~20 minutos)

### Dia 2
```bash
python scripts/add_elevation_to_cities.py --batch 9500 --continue
```
**Resultado**: 19,000 cidades acumuladas

### Dia 3
```bash
python scripts/add_elevation_to_cities.py --batch 9500 --continue
```
**Resultado**: 28,500 cidades acumuladas

### Dia 4
```bash
python scripts/add_elevation_to_cities.py --batch 9500 --continue
```
**Resultado**: 38,000 cidades acumuladas

### Dia 5 (Final)
```bash
python scripts/add_elevation_to_cities.py --batch 10060 --continue
```
**Resultado**: 48,060 cidades ✅ COMPLETO!

---

## 📈 Exemplo de Saída do Script

```
🚀 Iniciando processamento...
📂 Input: data/csv/worldcities.csv
📁 Output: data/csv/worldcities_with_elevation.csv
📊 Lote: 9500 cidades
🆕 Modo: Novo processamento

✅ Processadas: 100/9500 (1.1%) | Taxa: 5.2 cidades/s | ETA: 30.2 min | Requisições: 100
✅ Processadas: 200/9500 (2.1%) | Taxa: 5.4 cidades/s | ETA: 28.7 min | Requisições: 200
✅ Processadas: 300/9500 (3.2%) | Taxa: 5.3 cidades/s | ETA: 29.0 min | Requisições: 300
...
✅ Processadas: 9500/9500 (100.0%) | Taxa: 5.1 cidades/s | ETA: 0.0 min | Requisições: 9500

============================================================
🎉 PROCESSAMENTO CONCLUÍDO!
============================================================
Cidades processadas: 9500
Cidades puladas (já existentes): 0
Tempo total: 18.2 minutos
Taxa média: 8.69 cidades/segundo
============================================================

============================================================
📊 ESTATÍSTICAS DE PROCESSAMENTO
============================================================
Total de requisições: 9500
  - Open-Meteo: 9485
  - Open-Elevation: 15
Erros: 0
============================================================

📁 Output salvo em: data/csv/worldcities_with_elevation.csv
```

---

## 🐛 Troubleshooting

### Problema: "Too many requests"
**Solução**: Aguardar 1 hora e continuar com `--continue`

### Problema: Script interrompido
**Solução**: Rodar novamente com `--continue` (continua de onde parou)

### Problema: Coordenadas inválidas
**Solução**: Script pula automaticamente e registra erro no log

### Problema: API lenta
**Solução**: Open-Elevation será usado como fallback automaticamente

---

## ✅ Próximos Passos (Após Completar Downloads)

1. **Importar para PostgreSQL**
   ```bash
   python backend/database/scripts/import_world_locations.py \
       data/csv/worldcities_with_elevation.csv
   ```

2. **Criar Marcadores no Mapa**
   - Implementar frontend com marcadores
   - Callback para calcular ETo ao clicar

3. **Testar**
   - Verificar marcadores no mapa
   - Testar cálculo de ETo em tempo real

---

**Pronto para começar?** Execute o primeiro comando! 🚀

```bash
python scripts/add_elevation_to_cities.py --batch 9500
```
