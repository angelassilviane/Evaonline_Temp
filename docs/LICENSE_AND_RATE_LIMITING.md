# Licença e Rate Limiting - EVAonline

## Mudanças Implementadas

### 1. Atualização de Licença para GNU AGPL v3

**Motivo**: Conformidade com requisitos da revista SoftwareX para publicação científica.

#### Arquivos Atualizados:
- ✅ `LICENSE` - Já continha GNU AGPL v3
- ✅ `frontend/pages/documentation.py` - Atualizado de MIT para GNU AGPL v3
- ✅ `frontend/components/footer.py` - Link atualizado para "GNU AGPL v3"

#### Características da GNU AGPL v3:
- ✅ **Código aberto obrigatório**: Todo código derivado deve permanecer open source
- ✅ **Network copyleft**: Uso em serviços web requer disponibilização do código
- ✅ **Compatível com SoftwareX**: Atende requisitos de publicação científica
- ✅ **Proteção de liberdade**: Garante que melhorias retornem à comunidade

### 2. Implementação de Rate Limiting

**Motivo**: Conformidade com [Open-Meteo Terms of Service](https://open-meteo.com/en/terms)

#### Limites Open-Meteo:
- **Uso não-comercial**: 10,000 requisições/dia
- **Atribuição obrigatória**: ✅ Implementada no footer e documentação

#### Nossa Implementação (Conservadora):
- **Limite diário**: 5,000 requisições/dia (50% do limite Open-Meteo)
- **Storage**: Redis com chave `elevation:rate_limit:daily`
- **Reset**: Automático a cada 24 horas (TTL do Redis)
- **Logs**: `📊 Rate limit: X/5000 requests today`

#### Código Implementado (`backend/api/services/elevation_api.py`):

```python
# Verificar rate limit antes de cada requisição
rate_limit_key = "elevation:rate_limit:daily"
current_count = redis_client.get(rate_limit_key)

if current_count and int(current_count) >= 5000:
    logger.error("⛔ Rate limit exceeded: 5000 elevation requests/day")
    raise ValueError(
        "Rate limit exceeded (5000 requests/day). "
        "Please try again tomorrow."
    )

# Após requisição bem-sucedida, incrementar contador
pipe = redis_client.pipeline()
pipe.incr(rate_limit_key)
pipe.expire(rate_limit_key, 86400)  # 24 horas
current = pipe.execute()[0]
logger.info(f"📊 Rate limit: {current}/5000 requests today")
```

### 3. Proteções Adicionais Contra Abuso

#### Cache Redis (30 dias):
- **Chave**: `elevation:{lat:.4f}:{lon:.4f}`
- **TTL**: 2,592,000 segundos (30 dias)
- **Impacto**: Reduz drasticamente requisições à API
- **Logs**: `🎯 Cache HIT` / `💾 Cache SAVE`

#### Retry Logic com Backoff:
- **Max retries**: 3 tentativas
- **Delay**: 1s para erros de rede, 0.5s para outros
- **Sem retry**: Erros HTTP (404, 500, etc.)

#### Validações:
- **Coordenadas**: -90 ≤ lat ≤ 90, -180 ≤ long ≤ 180
- **Elevação**: -1000m ≤ elevation ≤ 9000m (range realista)
- **Requisições**: Apenas iniciadas pelo usuário (clique no mapa)

### 4. Documentação Atualizada

#### Página de Documentação (`/documentation`):
- ✅ Seção de licença GNU AGPL v3 com explicação
- ✅ Alerta sobre termos Open-Meteo
- ✅ Lista de proteções implementadas:
  - Redis cache (30 dias)
  - Retry logic com backoff
  - User-initiated requests only

#### Footer:
- ✅ Link "GNU AGPL v3" → `/documentation#license`
- ✅ Atribuição Open-Meteo: "Copernicus DEM 90m, CC-BY 4.0"
- ✅ Link para documentação completa

### 5. Monitoramento

#### Logs de Rate Limiting:
```bash
# Ver contador atual de requisições
docker logs evaonline-api | Select-String "Rate limit"

# Ver uso de cache
docker logs evaonline-api | Select-String "Cache HIT|Cache SAVE"

# Ver erros de rate limit
docker logs evaonline-api | Select-String "⛔ Rate limit exceeded"
```

#### Métricas Redis:
```bash
# Conectar ao Redis
docker exec -it evaonline-redis-test redis-cli

# Ver contador atual
GET elevation:rate_limit:daily

# Ver TTL restante
TTL elevation:rate_limit:daily

# Ver todas as chaves de elevação em cache
KEYS elevation:*
```

## Conformidade SoftwareX

### Checklist de Publicação:
- ✅ **Licença open source**: GNU AGPL v3
- ✅ **Repositório público**: GitHub
- ✅ **Documentação clara**: `/documentation` page
- ✅ **Atribuições corretas**: Open-Meteo, NASA POWER, MET Norway, NWS
- ✅ **Formato de citação**: BibTeX e APA fornecidos
- ✅ **Termos de serviço**: Rate limiting implementado
- ✅ **Código comentado**: Docstrings e comentários em todo código

## Próximos Passos

1. **Testar Rate Limiting**:
   ```bash
   # Reiniciar API
   docker-compose restart evaonline-api
   
   # Clicar em vários pontos no mapa
   # Verificar logs
   docker logs evaonline-api --follow | Select-String "Rate limit|Cache"
   ```

2. **Validar Documentação**:
   - Acessar http://localhost:8050/documentation
   - Verificar seção de licença
   - Testar links do footer

3. **Submeter ao SoftwareX**:
   - Preparar manuscript
   - Incluir link do repositório
   - Citar formato fornecido na documentação

## Referências

- [Open-Meteo Terms of Service](https://open-meteo.com/en/terms)
- [GNU AGPL v3 License](https://www.gnu.org/licenses/agpl-3.0.en.html)
- [SoftwareX Guide for Authors](https://www.elsevier.com/journals/softwarex/2352-7110/guide-for-authors)
- [Copernicus DEM License](https://spacedata.copernicus.eu/documents/20126/0/CSCDA_ESA_Mission-specific+Annex.pdf)
