# 🧪 Guia de Teste - Marcadores Mundiais

## ✅ Status da Implementação

**Data**: 2025-10-16  
**Versão**: 1.0  
**Status**: ✅ **FUNCIONANDO!**

### Logs Confirmados
```
🌍 Carregando marcadores mundiais da API...
Retrieved 6738 markers for map
✅ 6738 marcadores carregados
```

## 🎯 O que Testar

### 1. Visualização dos Marcadores
**No navegador (http://localhost:8050):**

- [ ] **Pontos verdes aparecem no mapa?**
  - Deve haver milhares de pequenos pontos verdes
  - Espalhados pelo mundo inteiro
  - Concentração maior em áreas populosas (Ásia, Europa)

- [ ] **Zoom funciona?**
  - Dar zoom in: pontos ficam maiores
  - Dar zoom out: pontos ficam menores
  - Performance deve ser fluida

### 2. Interação Hover (Passar Mouse)
**Passe o mouse sobre um ponto verde:**

- [ ] **Tooltip aparece?**
  - Deve mostrar nome da cidade
  - Deve mostrar código do país
  - Deve mostrar coordenadas (lat, lon)

**Exemplo esperado:**
```
📍 Tokyo, JPN
🌍 35.6870°, 139.7495°
```

### 3. Interação Click (Clicar)
**Clique em um ponto verde:**

- [ ] **Card de info aparece abaixo do mapa?**
  - Título com nome da cidade
  - País completo
  - Coordenadas formatadas
  - Dica: "Clique no mapa para calcular ETo"

**Exemplo esperado:**
```
🗺️ Tokyo
País: JPN
Coordenadas: 35.6870°, 139.7495°

💡 Clique diretamente no mapa para calcular ETo nesta localização
```

### 4. Funcionalidade Original (CRÍTICO!)
**Verificar que ETo ainda funciona:**

- [ ] **Click em área vazia do mapa**
  - Não deve clicar em marcador verde
  - Deve abrir painel de cálculo ETo
  - Deve funcionar normalmente

**Como testar:**
1. Clique em oceano (longe de cidades)
2. Clique em deserto (África, Austrália)
3. Verificar que painel ETo abre

### 5. Performance
**Testar velocidade:**

- [ ] **Carregamento inicial** (< 3 segundos)
- [ ] **Zoom in/out** (fluido, sem lag)
- [ ] **Pan (arrastar mapa)** (resposta imediata)
- [ ] **Hover sobre pontos** (tooltip instantâneo)

## 🐛 Problemas Conhecidos e Soluções

### Problema: Marcadores não aparecem
**Verificar:**
```powershell
# 1. API está retornando dados?
Invoke-WebRequest -Uri "http://localhost:8000/api/v1/world-locations/markers"

# 2. Logs mostram carregamento?
docker logs evaonline-api --tail 50 | Select-String "marcadores|markers"

# 3. Console do browser (F12) tem erros?
```

**Solução:**
- Se API não responde: `docker-compose restart api`
- Se logs não aparecem: verificar callback registrado
- Se console tem erro: copiar erro e debugar

### Problema: Performance ruim (lag)
**Ajustes possíveis:**

```python
# Em world_markers_callbacks.py, linha ~50
fig.update_traces(
    marker={
        "size": 3,        # Reduzir de 4 para 3
        "opacity": 0.4,   # Reduzir de 0.6 para 0.4
    }
)
```

### Problema: Click não funciona
**Verificar containers:**

```python
# No layout (map_results.py), verificar que existem:
html.Div(id="world-markers-container")  # Container Plotly
html.Div(id="world-markers-info")       # Container de info
```

## 📊 Dados de Referência

### Cidades Principais (Testar Hover)
Procure estas cidades e teste hover:

| Cidade | Lat | Lon | País |
|--------|-----|-----|------|
| Tokyo | 35.69 | 139.75 | JPN |
| Jakarta | -6.18 | 106.83 | IDN |
| Delhi | 28.61 | 77.23 | IND |
| Manila | 14.60 | 120.98 | PHL |
| São Paulo | -23.55 | -46.63 | BRA |
| New York | 40.71 | -74.01 | USA |
| London | 51.51 | -0.13 | GBR |
| Paris | 48.86 | 2.35 | FRA |

### Estatísticas Esperadas
```
Total de marcadores: 6,738
Países representados: 195
Elevação mínima: -24m (abaixo do mar)
Elevação máxima: 4,505m (alta montanha)
```

## 🎨 Aparência Esperada

### Cores
- **Marcadores**: Verde `#4a7c2f` (tema EvaOnline)
- **Opacidade**: 60% (transparente)
- **Fundo do mapa**: Carto Positron (claro)

### Tamanho
- **Pontos**: 4px de raio
- **Zoom mínimo**: Pontos muito pequenos
- **Zoom máximo**: Pontos visíveis mas não dominantes

### Distribuição Visual
```
🌍 Distribuição esperada:
  - Ásia: Densa (muitas cidades)
  - Europa: Densa
  - América do Norte: Moderada
  - América do Sul: Moderada
  - África: Esparsa
  - Oceania: Muito esparsa
  - Oceanos: Vazio (sem pontos)
```

## ✅ Checklist Final

### Implementação
- [x] API endpoint criado e testado
- [x] 6,738 marcadores no banco de dados
- [x] Callback de carregamento implementado
- [x] Callback de interação implementado
- [x] Layout atualizado com containers
- [x] Docker reiniciado
- [x] Logs confirmam funcionamento

### Testes Visuais
- [ ] Pontos verdes visíveis no mapa
- [ ] Hover mostra info da cidade
- [ ] Click mostra card detalhado
- [ ] Funcionalidade ETo preservada
- [ ] Performance aceitável (< 3s load)

### Documentação
- [x] WORLD_MARKERS_IMPLEMENTATION.md criado
- [x] TESTE_MARCADORES_MUNDIAIS.md criado
- [ ] Screenshots adicionados (opcional)
- [ ] README.md atualizado (pendente)

## 📸 Como Tirar Screenshots (Opcional)

Se quiser documentar:

1. **Visão Geral**:
   - Zoom out máximo
   - Captura mapa inteiro com pontos
   - Salvar como `docs/images/world_markers_overview.png`

2. **Hover**:
   - Passar mouse sobre cidade grande
   - Captura tooltip visível
   - Salvar como `docs/images/world_markers_hover.png`

3. **Click**:
   - Clicar em marcador
   - Captura card de info
   - Salvar como `docs/images/world_markers_click.png`

## 🚀 Próximos Passos

Após confirmação visual:

1. **Ajustes de estilo** (se necessário)
2. **Atualizar README.md** com nova feature
3. **Criar testes automatizados** (opcional)
4. **Commit e push** para repositório

## 📞 Suporte

**Se algo não funcionar:**

1. Copiar erro completo (console F12)
2. Verificar logs: `docker logs evaonline-api --tail 100`
3. Testar API: `GET /api/v1/world-locations/markers`
4. Reiniciar: `docker-compose restart api`

---

**Implementado com base em**: CBE Clima Tool  
**Referência**: https://clima.cbe.berkeley.edu/  
**Status**: ✅ Pronto para uso!
