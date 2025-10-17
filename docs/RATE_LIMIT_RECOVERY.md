# ⏱️ Guia: Continuar Após Rate Limit (429 Too Many Requests)

## 📊 **Situação Atual**

### ✅ **O que Conseguimos:**
- **4.831 cidades** processadas com sucesso
- **Arquivo**: `data/csv/worldcities_with_elevation.csv`
- **Última cidade OK**: Ferrara, Italy (linha 4831)
- **Primeira cidade com erro**: Zhangbei, China (linha 4832)

### ❌ **O que Aconteceu:**
- **Erro 429**: "Too Many Requests"
- **Causa**: Atingimos limite de **5.000 requisições/hora** da Open-Meteo API
- **Início**: ~18:20
- **Rate Limit**: 18:53
- **Total de requisições**: ~4.831 (incluindo testes anteriores na aplicação)

---

## ⏰ **Timeline e Janela de Rate Limit**

### Open-Meteo Limits:
```
- 10.000 requisições/dia   ✅ OK (usamos ~4.8k)
- 5.000 requisições/hora    ❌ ATINGIDO
- 600 requisições/minuto    ✅ OK (usamos ~9/min)
```

### Janela de Reset:
```
Início:     18:20 (primeira requisição)
Rate Limit: 18:53 (após 4.831 requisições)
Reset:      19:20 (1 hora após início)
```

**⏱️ AGUARDAR ATÉ: 19:20** (horário de Brasília)

---

## 🔄 **Como Continuar (às 19:20)**

### Opção 1: Script Automático (RECOMENDADO)

```powershell
# Às 19:20, executar:
python scripts/continue_elevation_batch.py --batch 5000
```

**O que faz:**
- ✅ Lê o arquivo `worldcities_with_elevation.csv`
- ✅ Identifica cidades com `elevation = 0.0` (rate limit)
- ✅ Reprocessa essas cidades
- ✅ Atualiza o arquivo existente
- ✅ Para automaticamente se atingir rate limit novamente

### Opção 2: Reprocessar Tudo com --continue

```powershell
# Deletar arquivo atual
Remove-Item data\csv\worldcities_with_elevation.csv

# Reiniciar do zero
python scripts/add_elevation_batch.py --batch 9500
```

**⚠️ Não recomendado**: Perde as 4.831 cidades já processadas

---

## 📝 **Verificar Progresso Atual**

```powershell
# Contar linhas processadas
Get-Content data\csv\worldcities_with_elevation.csv | Measure-Object -Line

# Ver últimas 10 linhas (verificar elevações zeradas)
Get-Content data\csv\worldcities_with_elevation.csv -Tail 10

# Contar cidades com elevação zerada
(Get-Content data\csv\worldcities_with_elevation.csv | Select-String ",0.0$").Count
```

---

## 🎯 **Estratégia Completa**

### Sessão 1 (HOJE - 18:20 a 18:53) ✅
- **Processadas**: 4.831 cidades
- **Status**: Rate limit atingido
- **Arquivo**: `worldcities_with_elevation.csv` (4.831 linhas)

### Sessão 2 (HOJE - 19:20+) ⏳
```powershell
# Executar às 19:20
python scripts/continue_elevation_batch.py --batch 4669
```
- **A processar**: 4.669 cidades restantes (9.500 - 4.831)
- **Tempo estimado**: ~23 minutos
- **Total dia 1**: 9.500 cidades ✅

### Sessão 3 (AMANHÃ - 16/10) ⏳
```powershell
python scripts/add_elevation_batch.py --batch 9500 --continue
```
- **A processar**: 9.500 cidades (19.000 total)

### Sessões 4-6 (17-19/10) ⏳
- Continuar com 9.500/dia até completar 48.060

---

## 📊 **Monitoramento**

### Ver quantas cidades faltam processar:
```powershell
# Total de linhas no arquivo atual (menos header)
$processed = (Get-Content data\csv\worldcities_with_elevation.csv).Count - 1
Write-Host "Processadas: $processed / 48060"
Write-Host "Percentual: $([math]::Round(100 * $processed / 48060, 2))%"
Write-Host "Restantes: $(48060 - $processed)"
```

### Ver cidades com elevação zerada (rate limit):
```powershell
# Contar linhas com ,0.0 no final
$zeradas = (Get-Content data\csv\worldcities_with_elevation.csv | Select-String ",0\.0$").Count
Write-Host "Cidades com elevação zerada: $zeradas"
```

---

## 🛡️ **Prevenção Futura**

### Para evitar rate limit novamente:

1. **Aumentar delay entre requisições**:
   ```python
   self.delay_seconds = 0.75  # 1.3 req/s = 4800/hora (safe)
   ```

2. **Processar em lotes menores**:
   ```powershell
   # Ao invés de 9500, fazer 4500 por hora
   python scripts/add_elevation_batch.py --batch 4500
   ```

3. **Monitorar taxa de requisições**:
   - Script já mostra: `Taxa: 3.1 cidades/s`
   - Ideal: < 1.4 cidades/s (5000/hora)

---

## ✅ **Checklist de Ação (19:20)**

- [ ] ⏰ Aguardar até 19:20 (1 hora após início)
- [ ] 🔍 Verificar quantas cidades estão zeradas
- [ ] 🚀 Executar: `python scripts/continue_elevation_batch.py --batch 4669`
- [ ] 👀 Monitorar logs para error 429
- [ ] ✅ Verificar se completou 9.500 cidades
- [ ] 📊 Atualizar `docs/ELEVATION_PROCESSING_STATUS.md`

---

## 🐛 **Se Atingir Rate Limit Novamente**

```powershell
# 1. Parar o script (Ctrl+C)

# 2. Aguardar mais 1 hora

# 3. Executar novamente
python scripts/continue_elevation_batch.py --batch 2000
```

---

## 📈 **Progresso Esperado**

| Horário | Ação | Cidades | Total |
|---------|------|---------|-------|
| 18:20 | Início Sessão 1 | - | 0 |
| 18:53 | Rate Limit | +4.831 | 4.831 |
| 19:20 | Início Sessão 2 | - | 4.831 |
| 19:43 | Completar Sessão 2 | +4.669 | **9.500** ✅ |

---

**⏰ AGUARDAR ATÉ 19:20 PARA CONTINUAR!**

**Comando para executar às 19:20:**
```powershell
python scripts/continue_elevation_batch.py --batch 4669
```
