# Como Funciona a Proteção Contra Abuso de Requisições

## 🎯 Visão Geral

A proteção atual implementada **NÃO rastreia por IP individual**, mas sim **por toda a aplicação** (global). Vou explicar como funciona e depois mostrar como implementar proteção por IP se necessário.

## 📊 Sistema Atual: Rate Limiting Global

### Como Funciona

```
┌─────────────────────────────────────────────────────────────┐
│  Usuário Clica no Mapa                                      │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  1. Validação de Coordenadas                                │
│     ✓ Latitude: -90 a 90                                    │
│     ✓ Longitude: -180 a 180                                 │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  2. Verificar Cache (Redis)                                 │
│     Chave: "elevation:lat:lon"                              │
│     TTL: 30 dias                                            │
│                                                              │
│     ✅ Se encontrado → RETORNA (sem consumir rate limit)   │
│     ❌ Se não encontrado → Continua                         │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  3. Verificar Rate Limit Global                             │
│     Chave Redis: "elevation:rate_limit:daily"               │
│     Limite: 5000 requisições/dia                            │
│                                                              │
│     current_count = redis_client.get(rate_limit_key)        │
│                                                              │
│     if current_count >= 5000:                               │
│         ⛔ BLOQUEIA → "Rate limit exceeded"                 │
│     else:                                                    │
│         ✅ PERMITE → Chama Open-Meteo API                   │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  4. Requisição à API Open-Meteo                             │
│     GET https://api.open-meteo.com/v1/elevation             │
│     ?latitude=X&longitude=Y                                 │
│                                                              │
│     ✅ Sucesso → Continua                                   │
│     ❌ Erro → Retry (3 tentativas)                          │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  5. Salvar e Incrementar (Pipeline Redis)                   │
│                                                              │
│     pipe = redis_client.pipeline()                          │
│     pipe.incr("elevation:rate_limit:daily")  # +1           │
│     pipe.expire("elevation:rate_limit:daily", 86400) # 24h  │
│     pipe.setex("elevation:lat:lon", 2592000, elevation)     │
│     pipe.execute()                                           │
│                                                              │
│     Log: "📊 Rate limit: 42/5000 requests today"           │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  6. Retorna Elevação ao Usuário                             │
└─────────────────────────────────────────────────────────────┘
```

### Código Simplificado

```python
# Chave GLOBAL (toda aplicação compartilha)
rate_limit_key = "elevation:rate_limit:daily"

# 1. Verificar contador atual
current_count = redis_client.get(rate_limit_key)

# 2. Bloquear se excedeu limite
if current_count and int(current_count) >= 5000:
    raise ValueError("Rate limit exceeded (5000 requests/day)")

# 3. Após API bem-sucedida, incrementar contador
pipe = redis_client.pipeline()
pipe.incr(rate_limit_key)           # Incrementa: 1, 2, 3, ...
pipe.expire(rate_limit_key, 86400)  # Reset automático em 24h
current = pipe.execute()[0]

# 4. Log para monitoramento
logger.info(f"📊 Rate limit: {current}/5000 requests today")
```

## 🔍 Limitações do Sistema Atual

### ⚠️ Problema: Proteção Global (Não por IP)

**Cenário de Abuso Possível:**

```
┌──────────────────────────────────────────────────────────┐
│  Usuário A (IP: 192.168.1.10)                           │
│  Clica 4000 vezes no mapa                               │
│  Contador global: 4000/5000                             │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  Usuário B (IP: 192.168.1.20) - USUÁRIO LEGÍTIMO        │
│  Tenta clicar 5 vezes no mapa                           │
│  Contador global: 4005/5000                             │
│                                                          │
│  ⛔ BLOQUEADO após 1000 cliques                         │
│  (porque Usuário A consumiu 4000)                       │
└──────────────────────────────────────────────────────────┘
```

**Impacto:**
- ✅ Protege a aplicação de exceder limite Open-Meteo (10k/dia)
- ❌ Um único usuário pode bloquear todos os outros
- ❌ Não identifica qual IP está abusando

## ✨ Solução: Rate Limiting por IP

### Como Implementar Proteção por IP

```python
def get_openmeteo_elevation(lat: float, long: float, client_ip: str = None):
    """
    Busca elevação com rate limiting por IP.
    
    Args:
        lat: Latitude
        long: Longitude
        client_ip: IP do cliente (obtido via request)
    """
    
    # ============================================
    # 1. RATE LIMITING POR IP (Individual)
    # ============================================
    if client_ip and redis_client:
        # Cada IP tem seu próprio contador
        ip_limit_key = f"elevation:rate_limit:ip:{client_ip}"
        ip_count = redis_client.get(ip_limit_key)
        
        # Limite por IP: 100 requisições/dia
        if ip_count and int(ip_count) >= 100:
            logger.warning(f"⛔ Rate limit IP {client_ip}: {ip_count}/100")
            raise ValueError(
                f"You have exceeded your daily limit (100 requests/day). "
                f"Try again tomorrow or contact support."
            )
    
    # ============================================
    # 2. RATE LIMITING GLOBAL (Aplicação inteira)
    # ============================================
    rate_limit_key = "elevation:rate_limit:daily"
    current_count = redis_client.get(rate_limit_key)
    
    # Limite global: 5000 requisições/dia
    if current_count and int(current_count) >= 5000:
        logger.error("⛔ Global rate limit exceeded: 5000/day")
        raise ValueError("Service temporarily unavailable. Try again tomorrow.")
    
    # Cache check (mesmo código atual)
    cache_key = f"elevation:{lat:.4f}:{long:.4f}"
    cached = redis_client.get(cache_key)
    if cached:
        logger.info(f"🎯 Cache HIT: {client_ip or 'unknown'}")
        return float(cached), []
    
    # API call...
    # (código existente)
    
    # ============================================
    # 3. INCREMENTAR CONTADORES (Após sucesso)
    # ============================================
    pipe = redis_client.pipeline()
    
    # Contador global
    pipe.incr(rate_limit_key)
    pipe.expire(rate_limit_key, 86400)
    
    # Contador por IP (se fornecido)
    if client_ip:
        ip_limit_key = f"elevation:rate_limit:ip:{client_ip}"
        pipe.incr(ip_limit_key)
        pipe.expire(ip_limit_key, 86400)
    
    results = pipe.execute()
    global_count = results[0]
    
    if client_ip:
        ip_count = results[2]
        logger.info(
            f"📊 Rate limit - Global: {global_count}/5000, "
            f"IP {client_ip}: {ip_count}/100"
        )
    else:
        logger.info(f"📊 Rate limit - Global: {global_count}/5000")
    
    return float(elevation), warnings
```

### Como Obter o IP do Cliente

#### No FastAPI (backend/api/routers/elevation.py):

```python
from fastapi import Request

@router.get("/elevation")
async def get_elevation_endpoint(
    lat: float,
    lon: float,
    request: Request  # ← Injetar Request
):
    # Obter IP real (considera proxies como nginx)
    client_ip = request.headers.get("X-Forwarded-For")
    if client_ip:
        # X-Forwarded-For pode ter múltiplos IPs: "client, proxy1, proxy2"
        client_ip = client_ip.split(",")[0].strip()
    else:
        # Fallback para IP direto
        client_ip = request.client.host
    
    # Chamar serviço com IP
    elevation, warnings = get_openmeteo_elevation(lat, lon, client_ip)
    
    return {
        "elevation": elevation,
        "warnings": warnings,
        "client_ip": client_ip  # Debug (remover em produção)
    }
```

## 📈 Estrutura de Dados Redis

### Sistema Atual (Global):
```
┌─────────────────────────────────────────────────────┐
│ Redis Key                           │ Value │ TTL   │
├─────────────────────────────────────┼───────┼───────┤
│ elevation:rate_limit:daily          │ 4253  │ 86400 │
│ elevation:40.7128:-74.0060          │ 10.2  │ 2592000│
│ elevation:-23.5505:-46.6333         │ 760.5 │ 2592000│
└─────────────────────────────────────────────────────┘
```

### Sistema com Rate Limit por IP:
```
┌──────────────────────────────────────────────────────────┐
│ Redis Key                                │ Value │ TTL   │
├──────────────────────────────────────────┼───────┼───────┤
│ elevation:rate_limit:daily               │ 4253  │ 86400 │ ← Global
│ elevation:rate_limit:ip:192.168.1.10     │ 87    │ 86400 │ ← IP específico
│ elevation:rate_limit:ip:192.168.1.20     │ 5     │ 86400 │ ← IP específico
│ elevation:rate_limit:ip:10.0.0.5         │ 142   │ 86400 │ ← IP específico
│ elevation:40.7128:-74.0060               │ 10.2  │ 2592000│ ← Cache
│ elevation:-23.5505:-46.6333              │ 760.5 │ 2592000│ ← Cache
└──────────────────────────────────────────────────────────┘
```

## 🛡️ Estratégia de Defesa em Camadas

### Camada 1: Cache (Máxima Proteção)
```
✅ TTL: 30 dias
✅ Elevação é dado estático (não muda)
✅ Reduz ~95% das requisições reais
✅ Não consome rate limit (HIT = grátis)
```

### Camada 2: Rate Limit por IP
```
✅ Limite: 100 requisições/dia por IP
✅ Protege contra abuso individual
✅ Usuários legítimos não afetados
✅ Identificação de IPs problemáticos
```

### Camada 3: Rate Limit Global
```
✅ Limite: 5000 requisições/dia (toda app)
✅ Protege contra exceder Open-Meteo (10k)
✅ Margem de segurança: 50%
✅ Última linha de defesa
```

### Camada 4: Retry Logic
```
✅ 3 tentativas com backoff
✅ Protege contra erros temporários
✅ Sem retry em erros HTTP (404, 500)
✅ Logs detalhados para debug
```

## 📊 Comandos de Monitoramento

### Ver Contador Global:
```bash
docker exec -it evaonline-redis-test redis-cli GET elevation:rate_limit:daily
# Output: "4253"
```

### Ver Contadores por IP:
```bash
docker exec -it evaonline-redis-test redis-cli KEYS "elevation:rate_limit:ip:*"
# Output:
# 1) "elevation:rate_limit:ip:192.168.1.10"
# 2) "elevation:rate_limit:ip:192.168.1.20"

# Ver contador específico
docker exec -it evaonline-redis-test redis-cli GET "elevation:rate_limit:ip:192.168.1.10"
# Output: "87"
```

### Ver TTL Restante:
```bash
docker exec -it evaonline-redis-test redis-cli TTL elevation:rate_limit:daily
# Output: 43200 (12 horas restantes)
```

### Ver Total de Cache:
```bash
docker exec -it evaonline-redis-test redis-cli DBSIZE
# Output: (integer) 1523
```

### Logs da Aplicação:
```powershell
# Ver rate limiting
docker logs evaonline-api | Select-String "Rate limit"

# Ver uso de cache
docker logs evaonline-api | Select-String "Cache HIT|Cache SAVE"

# Ver bloqueios
docker logs evaonline-api | Select-String "⛔"
```

## 🎯 Recomendações

### Para Produção:

1. **Implementar Rate Limit por IP** (código acima)
2. **Ajustar limites**:
   - IP individual: 100-500 req/dia (depende do uso esperado)
   - Global: 5000-8000 req/dia (50-80% do limite Open-Meteo)

3. **Adicionar Whitelist** (IPs confiáveis):
   ```python
   WHITELISTED_IPS = ["203.0.113.0", "198.51.100.0"]
   if client_ip in WHITELISTED_IPS:
       # Pular rate limiting
       pass
   ```

4. **Dashboard de Monitoramento**:
   - Grafana com métricas Redis
   - Alertas quando >80% do limite
   - Top 10 IPs mais ativos

5. **Configurar nginx/proxy**:
   ```nginx
   # Passar IP real do cliente
   proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
   proxy_set_header X-Real-IP $remote_addr;
   ```

### Vantagens da Implementação Atual:

✅ **Simples e eficaz** para MVP/teste
✅ **Cache agressivo** reduz requisições drasticamente
✅ **Protege contra exceder Open-Meteo**
✅ **Fácil de monitorar**

### Quando Implementar por IP:

⚠️ Se detectar **abuso de um único usuário**
⚠️ Se a aplicação for **pública** (não autenticada)
⚠️ Se precisar **identificar** usuários problemáticos
⚠️ Para **conformidade** com políticas de uso

---

**Quer que eu implemente o rate limiting por IP agora?** 🚀
