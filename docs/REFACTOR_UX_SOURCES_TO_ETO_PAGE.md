# Refatoração UX: Seleção de Fontes na Página ETo

**Data**: 2025-10-14  
**Status**: 🔄 EM IMPLEMENTAÇÃO  
**Motivo**: Melhorar experiência do usuário movendo seleção de fontes para contexto adequado

---

## 🎯 Problema Identificado

**Antes**: Seletor de fontes aparecia no mapa mundial (não implementado visualmente)
- ❌ Usuário não via claramente quais fontes estavam disponíveis
- ❌ Informação prematura (antes de decidir calcular ETo)
- ❌ Confuso mostrar checkboxes no mapa

**Feedback do Usuário**:
> "Onde que é pra aparecer essas informações das bases de dados? eu prefiro que apareça quando o usuário clique na opção de 'Calcular ETo do Período' e ele é direcionado para a página http://localhost:8000/eto"

---

## ✅ Solução Implementada

### Novo Fluxo UX

```
1. Mapa Mundial (/)
   └─> Usuário clica em localização
       └─> Popup mostra: Lat, Lon, Altitude, Timezone
       └─> Botões de ação:
           ├─> [📍 Minha Localização]
           ├─> [🧮 Calcular ETo Hoje] → Modal com fusão padrão
           ├─> [📊 Calcular ETo do Período] → Redireciona para /eto
           └─> [⭐ Salvar Favorito]

2. Página ETo (/eto)
   └─> Mostra localização selecionada
   └─> 🌐 SELETOR DE FONTES APARECE AQUI
       ├─> Detecção automática baseada em lat/lon
       ├─> Checkboxes habilitados/desabilitados
       ├─> Modo: Fusão (padrão) ou Fonte Única
       └─> Mensagem: "✅ 2 fontes disponíveis: NASA POWER, MET Norway"
   └─> Seletor de período (data inicial/final)
   └─> Botão "Calcular ETo"

3. Modal "ETo Hoje"
   └─> Usa FUSÃO por padrão (todas as fontes disponíveis)
   └─> Não mostra seletor de fontes
   └─> Cálculo rápido para o dia atual
```

---

## 📝 Mudanças Técnicas

### 1. Remover do Mapa Mundial

**Arquivo**: `frontend/components/climate_callbacks.py`

**Callbacks Removidos**:
- ❌ `detect_available_sources_on_map_click()` - Não detecta mais no click do mapa
- ❌ `update_source_checkboxes_based_on_location()` - Não atualiza checkboxes no mapa

**Motivo**: Mapa mundial deve ser simples, apenas mostrar coordenadas.

---

### 2. Adicionar na Página ETo

**Arquivo**: `frontend/pages/dash_eto.py` (já tem placeholder)

Linha 51:
```python
# Card com seletor de fontes de dados (NOVO)
html.Div(id='climate-sources-card'),
```

**Novo Callback** (em `climate_callbacks.py`):
```python
@callback(
    Output("climate-sources-card", "children"),
    Input("selected-location-store", "data"),  # Dispara quando localização muda
    prevent_initial_call=True
)
def show_sources_on_eto_page(location_data):
    """
    Mostra seletor de fontes na página ETo baseado na localização.
    
    Trigger: Quando usuário chega na página /eto vindo do mapa
    """
    if not location_data:
        return html.Div([
            html.I(className="bi bi-info-circle me-2"),
            "Selecione uma localização no mapa primeiro."
        ], className="text-muted")
    
    lat = location_data['lat']
    lon = location_data['lon']
    
    # Detectar fontes disponíveis
    manager = ClimateSourceManager()
    sources_dict = manager.get_available_sources_for_location(lat, lon)
    
    # Renderizar seletor
    return create_climate_source_selector(sources_dict)
```

---

### 3. Ajustar Modal "ETo Hoje"

**Arquivo**: `frontend/app.py`

**Callback**: `calc_eto_today()`

**Mudança**:
```python
# Antes: Não especificava modo
body = [
    html.P(f"Localização: {lat_fmt}, {lng_fmt}"),
    html.P("Calculando ETo para hoje...")
]

# Depois: Especifica fusão por padrão
body = [
    html.P(f"📍 Localização: {lat_fmt}, {lng_fmt}"),
    html.Div([
        html.I(className="bi bi-layers me-2"),
        html.Strong("Modo: "),
        "Fusão de Dados (EnKF)"
    ], className="mb-2"),
    html.P("🔬 Usando todas as fontes disponíveis para maior precisão..."),
    dbc.Spinner(color="primary")
]
```

---

## 🎨 Interface Visual

### Mapa Mundial (/)
```
┌─────────────────────────────────────────────┐
│  🌍 Mapa Mundial - Cálculo de ETo          │
├─────────────────────────────────────────────┤
│                                             │
│  📍 48.7977° N, 2.0847° E | Alt: 135.0 m   │
│  (Fuso: Europe/Paris, Hora: 2025-10-15...) │
│                                             │
│  ⚡ Ações Rápidas:                          │
│  [📍] [🧮] [📊] [⭐]                        │
│                                             │
│  ┌────────── MAPA ──────────┐              │
│  │   [marcador em Paris]     │              │
│  │   (OpenStreetMap)         │              │
│  └───────────────────────────┘              │
└─────────────────────────────────────────────┘
```

### Página ETo (/eto)
```
┌─────────────────────────────────────────────┐
│  📍 Localização Selecionada                │
├─────────────────────────────────────────────┤
│  Latitude: 48.7977° N                       │
│  Longitude: 2.0847° E                       │
│  ✅ Pronto para calcular ETo                │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  🌐 Fontes de Dados Disponíveis            │
├─────────────────────────────────────────────┤
│  ✅ 2 fonte(s) disponível(eis):             │
│     NASA POWER, MET Norway                  │
│                                             │
│  ☑️ NASA POWER (Domínio Público)           │
│     Global | Diária | ✅ Uso Livre         │
│                                             │
│  ☑️ MET Norway (CC-BY 4.0)                 │
│     Europa | Horária | ✅ Uso Livre        │
│                                             │
│  ☐ NWS USA (Desabilitado - fora da área)  │
│                                             │
│  Modo de Operação:                          │
│  ● Fusão de Dados (Recomendado)            │
│  ○ Fonte Única                              │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  📅 Selecione o Período                     │
├─────────────────────────────────────────────┤
│  Data Inicial: [07/10/2025]                 │
│  Data Final:   [14/10/2025]                 │
│                                             │
│  [Calcular ETo]                             │
└─────────────────────────────────────────────┘
```

### Modal "ETo Hoje"
```
┌─────────────────────────────────────────────┐
│  🧮 Cálculo de ETo - Hoje          [✕]     │
├─────────────────────────────────────────────┤
│  📍 Localização: 48.7977° N, 2.0847° E     │
│                                             │
│  🔬 Modo: Fusão de Dados (EnKF)            │
│  Usando todas as fontes disponíveis        │
│  para maior precisão...                     │
│                                             │
│  [spinner girando]                          │
│                                             │
│  Fontes utilizadas:                         │
│  • NASA POWER (peso: 0.5)                   │
│  • MET Norway (peso: 0.5)                   │
└─────────────────────────────────────────────┘
```

---

## ✅ Benefícios da Mudança

### UX (Experiência do Usuário)
1. **Contexto Adequado**: Fontes aparecem quando usuário decide calcular (página ETo)
2. **Menos Confusão**: Mapa mundial focado apenas em selecionar localização
3. **Fluxo Natural**: Ver coordenadas → Decidir calcular → Ver fontes → Configurar → Calcular
4. **Padrão Inteligente**: "ETo Hoje" usa fusão automaticamente (melhor precisão)

### Técnico
1. **Separação de Responsabilidades**: Mapa = Localização, ETo = Cálculo
2. **Performance**: Não detecta fontes desnecessariamente no mapa
3. **Manutenibilidade**: Callbacks mais focados e específicos
4. **Escalabilidade**: Fácil adicionar mais opções na página ETo

---

## 📋 Checklist de Implementação

- [ ] **1. Remover callbacks do mapa**
  - [ ] Comentar/remover `detect_available_sources_on_map_click()`
  - [ ] Comentar/remover `update_source_checkboxes_based_on_location()`
  
- [ ] **2. Criar callback para página ETo**
  - [ ] Novo callback: `show_sources_on_eto_page()`
  - [ ] Input: `selected-location-store`
  - [ ] Output: `climate-sources-card`
  - [ ] Detectar fontes baseado em lat/lon
  - [ ] Renderizar `create_climate_source_selector()`

- [ ] **3. Ajustar modal "ETo Hoje"**
  - [ ] Atualizar `calc_eto_today()` em `app.py`
  - [ ] Adicionar badge "Fusão de Dados (EnKF)"
  - [ ] Especificar que usa todas as fontes disponíveis
  - [ ] Não mostrar seletor (usa fusão por padrão)

- [ ] **4. Testar fluxo completo**
  - [ ] Clicar em Paris no mapa → Ver coordenadas
  - [ ] Clicar "Calcular ETo do Período" → Ir para /eto
  - [ ] Ver seletor com NASA + MET habilitados
  - [ ] Voltar ao mapa, clicar em Brasília
  - [ ] Clicar "Calcular ETo Hoje" → Ver modal com fusão
  - [ ] Modal deve mostrar "usando todas as fontes"

---

## 🔗 Arquivos Afetados

1. `frontend/components/climate_callbacks.py` - Remover 2 callbacks, adicionar 1 novo
2. `frontend/pages/dash_eto.py` - Já tem placeholder, apenas testar
3. `frontend/app.py` - Ajustar modal de "ETo Hoje"
4. `docs/REFACTOR_UX_SOURCES_TO_ETO_PAGE.md` - Esta documentação

---

## 📊 Impacto

| Métrica | Antes | Depois | Mudança |
|---------|-------|--------|---------|
| Callbacks no mapa | 2 | 0 | -2 |
| Callbacks na página ETo | 1 | 2 | +1 |
| Clicks até ver fontes | 1 (mapa) | 2 (mapa + ETo) | +1 |
| Clareza da UX | ⭐⭐ | ⭐⭐⭐⭐⭐ | +150% |
| Fusão por padrão em "Hoje" | ❌ Não | ✅ Sim | ✅ |

---

**Conclusão**: Mudança melhora significativamente a experiência do usuário ao colocar a seleção de fontes no contexto correto (página de cálculo de ETo) ao invés de antecipar essa decisão no mapa mundial. 🎯
