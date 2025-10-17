# 🧪 Guia de Teste Visual - Tabs Implementadas

## ✅ Status dos Logs

**Logs confirmam:**
```
✅ "Criando mapa mundial interativo com tabs"
✅ Layout created successfully
✅ Cache HIT: Elevation funcionando
```

## 🎯 O que Você Deve Ver no Navegador

### 1. Estrutura da Página HOME

```
╔═══════════════════════════════════════════════╗
║  🌍 EVAonline                                 ║
║  An online tool for reference ETo             ║
╠═══════════════════════════════════════════════╣
║                                               ║
║  🗺️ Mapa Mundial - Cálculo de ETo            ║
║  Escolha o modo: Explore cidades ou calcule   ║
║                                               ║
╠═══════════════════════════════════════════════╣
║ ┌─────────────────────────────────────────┐  ║
║ │ [📍 Calcular ETo✓] [🗺️ Explorar Cidades]│  ║
║ └─────────────────────────────────────────┘  ║
╠═══════════════════════════════════════════════╣
║                                               ║
║ ℹ️ Clique em qualquer ponto do mapa para     ║
║    calcular ETo usando múltiplas fontes       ║
║                                               ║
║  ┌────────────────────────────────────────┐  ║
║  │                                        │  ║
║  │      🗺️ MAPA LEAFLET INTERATIVO       │  ║
║  │      (cinza claro, sem marcadores)     │  ║
║  │                                        │  ║
║  └────────────────────────────────────────┘  ║
║                                               ║
║  📍 -22.2936° S, -48.5842° W                 ║
║  ⛰️ Altitude: XXX m                           ║
║                                               ║
║  ⚡ Ações: [📍][📊][📈][⭐]                  ║
║                                               ║
╚═══════════════════════════════════════════════╝
```

### 2. Tab "📍 Calcular ETo" (Ativa por Padrão)

**Características:**
- ✅ Tab tem fundo mais escuro (ativa)
- ✅ Alert azul explicando funcionalidade
- ✅ Mapa Leaflet limpo (sem pontos)
- ✅ Barra de informações embaixo
- ✅ Botões de ação rápida visíveis

**Teste:**
1. Clique em qualquer ponto do mapa
2. Veja lat/lon aparecer na barra
3. Altitude é calculada automaticamente
4. Botões ficam habilitados

### 3. Tab "🗺️ Explorar Cidades" (Inativa)

**Para ativar:**
1. Clique na tab "🗺️ Explorar Cidades"
2. Aguarde ~2 segundos

**O que deve acontecer:**
```
╔═══════════════════════════════════════════════╗
║ ┌─────────────────────────────────────────┐  ║
║ │ [📍 Calcular ETo] [🗺️ Explorar Cidades✓]│  ║
║ └─────────────────────────────────────────┘  ║
╠═══════════════════════════════════════════════╣
║                                               ║
║ ✅ Visualize 6,738 cidades pré-carregadas.    ║
║    Passe o mouse sobre os pontos verdes       ║
║                                               ║
║  ┌────────────────────────────────────────┐  ║
║  │  🟢🟢🟢                   🟢🟢🟢🟢      │  ║
║  │    🟢🟢🟢             🟢🟢🟢🟢🟢🟢     │  ║
║  │      🟢🟢           🟢🟢🟢🟢🟢🟢🟢    │  ║
║  │  🟢🟢   🟢        🟢🟢🟢🟢🟢🟢🟢🟢   │  ║
║  │    🟢🟢🟢          🟢🟢🟢🟢🟢🟢🟢🟢  │  ║
║  │  🟢🟢🟢🟢            🟢🟢🟢🟢🟢🟢    │  ║
║  │                                        │  ║
║  └────────────────────────────────────────┘  ║
║                                               ║
║  MAPA PLOTLY COM 6,738 MARCADORES            ║
║                                               ║
╚═══════════════════════════════════════════════╝
```

**Logs esperados ao clicar:**
```
🌍 Carregando marcadores mundiais da API...
Retrieved 6738 markers for map
✅ 6738 marcadores carregados
```

## 🎯 Testes Interativos

### Teste 1: Alternância entre Tabs
```
1. [✓] Tab "Calcular" ativa por padrão
2. [  ] Clicar "Explorar Cidades"
3. [  ] Ver marcadores aparecerem (~2s)
4. [  ] Voltar para "Calcular"
5. [  ] Ver marcadores desaparecerem
6. [  ] Voltar para "Explorar"
7. [  ] Ver marcadores (já carregados, instantâneo)
```

### Teste 2: Funcionalidade Calcular
```
Na tab "📍 Calcular ETo":
1. [  ] Clicar em Paris (Europa)
2. [  ] Ver: "📍 48.8566° N, 2.3522° E"
3. [  ] Ver: "⛰️ Altitude: ~100 m"
4. [  ] Clicar botão "Calcular ETo Hoje"
5. [  ] Ver modal com resultado
```

### Teste 3: Funcionalidade Explorar
```
Na tab "🗺️ Explorar Cidades":
1. [  ] Ver milhares de pontos verdes
2. [  ] Passar mouse sobre ponto na Ásia
3. [  ] Ver tooltip: "Tokyo, JPN, 35.69°..."
4. [  ] Clicar no ponto
5. [  ] Ver card abaixo com detalhes
```

## 📊 Monitoramento de Logs em Tempo Real

### Comando para acompanhar:
```powershell
docker logs evaonline-api --tail 20 --follow
```

### O que procurar:
```
✅ "Criando mapa mundial interativo com tabs"
✅ "🌍 Carregando marcadores mundiais da API..."
✅ "Retrieved 6738 markers for map"
✅ "✅ 6738 marcadores carregados"
✅ "🎯 Cache HIT: Elevation"
```

### Erros a observar:
```
❌ "module 'dash_leaflet' has no attribute..."
❌ "KeyError: 'map-tabs'"
❌ "404 Not Found"
❌ "Connection refused"
```

## 🎨 Aparência Visual Esperada

### Tab Ativa (Calcular)
- **Cor**: Fundo branco/claro
- **Borda**: Inferior colorida (azul)
- **Texto**: Negrito
- **Ícone**: 📍 destacado

### Tab Inativa (Explorar)
- **Cor**: Fundo cinza claro
- **Borda**: Sem destaque
- **Texto**: Normal
- **Ícone**: 🗺️ opaco

### Alerts (Descrições)
- **Tab Calcular**: 🔵 Azul (color="info")
- **Tab Explorar**: 🟢 Verde (color="success")

### Mapas
- **Leaflet**: Fundo cinza, continentes brancos, sem marcadores
- **Plotly**: Fundo claro (carto-positron), 6,738 pontos verdes

## 🐛 Se Algo Não Funcionar

### Problema: Tabs não aparecem
```powershell
# Verificar se componente foi criado
docker logs evaonline-api | Select-String "tabs"

# Reiniciar se necessário
docker-compose restart api
```

### Problema: Marcadores não carregam
```powershell
# Verificar API
curl http://localhost:8000/api/v1/world-locations/markers

# Verificar callback
docker logs evaonline-api | Select-String "marcadores"
```

### Problema: Click não funciona
- Verificar console do browser (F12)
- Ver se há erros JavaScript
- Checar IDs dos componentes

## ✅ Checklist de Sucesso

- [ ] Vejo 2 tabs na página HOME
- [ ] Tab "Calcular ETo" está ativa (fundo claro)
- [ ] Alert azul explica funcionalidade
- [ ] Mapa Leaflet aparece limpo
- [ ] Posso clicar no mapa e ver coordenadas
- [ ] Ao clicar "Explorar Cidades", vejo marcadores
- [ ] Pontos verdes aparecem (~6,738)
- [ ] Hover mostra nome da cidade
- [ ] Volto para "Calcular" e marcadores somem
- [ ] Logs mostram "tabs" e "marcadores"

---

**Status**: 🧪 Pronto para teste visual  
**Ação**: Verifique o navegador em http://localhost:8050  
**Logs**: Acompanhe em tempo real com Docker
