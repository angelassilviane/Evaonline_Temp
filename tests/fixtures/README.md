# Fixtures de Testes - Referencia Completa

## Estrutura de Conftest

```
tests/
├── conftest.py                 # GLOBAL (todas fixtures compartilhadas)
│   ├── event_loop             # Para async
│   ├── test_settings          # Config de teste
│   └── mock_redis             # Mock basico
│
├── unit/
│   └── conftest.py            # UNIT TESTS (tudo mockado)
│       ├── mock_location_repo
│       ├── mock_climate_repo
│       ├── mock_cache_service
│       ├── location_data
│       ├── climate_data
│       └── assert_valid_location
│
├── integration/
│   └── conftest.py            # INTEGRATION (BD e Redis REAIS)
│       ├── integration_db_engine
│       ├── integration_db_session
│       ├── redis_client
│       ├── location_in_db
│       ├── climate_service
│       └── verify_cache_data
│
└── api/
    └── conftest.py            # API TESTS (endpoints HTTP)
        ├── client (TestClient)
        ├── auth_headers
        ├── location_create_payload
        ├── assert_api_success
        ├── assert_api_error
        └── performance_thresholds
```

---

## Como Usar Fixtures em Testes

### EXEMPLO 1: Unit Test com Mocks

```python
# tests/unit/test_location_service.py
import pytest

def test_get_location(mock_location_repo, location_data):
    """Teste unitario - tudo mockado."""
    # ARRANGE
    repo = mock_location_repo
    expected = location_data

    # ACT
    result = repo.get_by_id(1)

    # ASSERT
    assert result["name"] == expected["name"]
    repo.get_by_id.assert_called_once_with(1)


def test_validate_location_data(assert_valid_location, location_data):
    """Usar helper para validar."""
    assert_valid_location(location_data)  # Levanta AssertionError se invalido
```

### EXEMPLO 2: Integration Test com BD Real

```python
# tests/integration/test_location_repository.py
import pytest

def test_save_location_in_database(integration_db_session, location_in_db):
    """Teste de integracao - BD real."""
    from backend.database.models import Location

    # ARRANGE
    session = integration_db_session
    location = location_in_db

    # ACT
    records = session.query(Location).filter_by(name="Sao Paulo").all()

    # ASSERT
    assert len(records) == 1
    assert records[0].latitude == -23.5505
    # Automatic rollback apos teste!


@pytest.mark.asyncio
async def test_cache_with_redis(redis_client, cache_populated):
    """Teste async com Redis."""
    # ARRANGE
    cache = cache_populated

    # ACT
    value = await cache.get("climate:1:2025-10-22")

    # ASSERT
    assert value is not None
```

### EXEMPLO 3: API Test com TestClient

```python
# tests/api/test_locations_endpoints.py
import pytest

def test_list_locations(client, location_in_db, assert_api_success):
    """Teste de API - endpoint real."""
    # ACT
    response = client.get("/api/locations")

    # ASSERT
    data = assert_api_success(response, expected_status=200)
    assert isinstance(data, list)
    assert len(data) >= 1


def test_create_location_unauthorized(client, location_create_payload):
    """Teste de erro - sem autenticacao."""
    # ACT
    response = client.post(
        "/api/locations",
        json=location_create_payload,
        headers={"Content-Type": "application/json"},
    )

    # ASSERT
    assert response.status_code == 401


def test_get_location_by_id(client, location_in_db, assert_api_success):
    """Teste com parametro."""
    # ACT
    response = client.get(f"/api/locations/{location_in_db.id}")

    # ASSERT
    data = assert_api_success(response)
    assert data["id"] == location_in_db.id
    assert data["name"] == location_in_db.name


def test_performance(client, performance_thresholds):
    """Teste de performance."""
    import time

    # ACT
    start = time.time()
    response = client.get("/api/locations")
    elapsed = time.time() - start

    # ASSERT
    assert response.status_code == 200
    assert elapsed < performance_thresholds["list_endpoints"], \
        f"Tempo {elapsed}s > limite {performance_thresholds['list_endpoints']}s"
```

---

## Fixtures por Categoria

### GLOBAL (tests/conftest.py)

| Fixture | Escopo | Uso |
|---------|--------|-----|
| `event_loop` | session | Testes async |
| `test_settings` | session | Config de teste |
| `mock_redis` | function | Mock basico Redis |
| `pytest_configure` | - | Registra marcadores |

### UNIT (tests/unit/conftest.py)

| Fixture | Escopo | Uso | Nota |
|---------|--------|-----|------|
| `mock_location_repo` | function | Mock do LocationRepository | Mock puro |
| `mock_climate_repo` | function | Mock do ClimateRepository | Mock puro |
| `mock_cache_service` | function | Mock do CacheService | Async Mock |
| `mock_external_api` | function | Mock de APIs | Simula responses |
| `location_data` | function | Dados de locacao | Dict fixture |
| `climate_data` | function | Dados de clima | Dict fixture |
| `user_data` | function | Dados de usuario | Dict fixture |
| `favorite_data` | function | Dados de favorito | Dict fixture |
| `assert_valid_location` | function | Valida estrutura | Helper |
| `assert_valid_climate` | function | Valida climate | Helper |
| `tolerance` | function | Tolerancia de float | Para comparacoes |
| `timestamps` | function | Timestamps utils | Data/hora |

### INTEGRATION (tests/integration/conftest.py)

| Fixture | Escopo | Uso | Nota |
|---------|--------|-----|------|
| `integration_db_engine` | session | Engine SQLAlchemy | BD REAL |
| `integration_db_session` | function | Session com rollback | BD REAL, cleanup auto |
| `redis_client` | function | Redis async REAL | BD REAL |
| `redis_sync_client` | function | Redis síncrono REAL | BD REAL |
| `location_in_db` | function | Locacao no BD | CREATE + commit |
| `user_in_db` | function | Usuario no BD | CREATE + commit |
| `climate_record_in_db` | function | Clima no BD | CREATE + commit |
| `favorite_in_db` | function | Favorito no BD | CREATE + commit |
| `cache_populated` | function | Cache com dados | Popula Redis |
| `climate_service` | function | ClimateService real | BD + API mock |
| `cache_service` | function | CacheService real | Redis real |
| `favorites_service` | function | FavoritesService real | BD real |
| `count_db_records` | function | Contar registros | Helper |
| `verify_cache_data` | function | Verificar cache | Helper async |
| `transaction_context` | function | Context manager | Teste transacoes |

### API (tests/api/conftest.py)

| Fixture | Escopo | Uso | Nota |
|---------|--------|-----|------|
| `client` | function | TestClient FastAPI | Síncrono |
| `async_client` | function | AsyncClient FastAPI | Async |
| `auth_headers` | function | Headers com auth | Fake token |
| `api_key_headers` | function | Headers com API key | X-API-Key |
| `location_create_payload` | function | Payload criar locacao | JSON |
| `climate_query_params` | function | Query params clima | Dict |
| `favorite_payload` | function | Payload criar favorito | JSON |
| `expected_location_response` | function | Schema resposta | Tipos esperados |
| `expected_climate_response` | function | Schema resposta | Tipos esperados |
| `assert_api_success` | function | Validar sucesso | Helper |
| `assert_api_error` | function | Validar erro | Helper |
| `assert_valid_json_schema` | function | Validar schema | Helper |
| `api_paths` | function | Paths de endpoints | Dict de URLs |
| `session_id` | function | ID de sessao | String |
| `session_headers` | function | Headers com session | X-Session-ID |
| `performance_thresholds` | function | Limites performance | Dict de ms |
| `measure_request_time` | function | Medir tempo | Helper |
| `invalid_location_id` | function | ID invalido | Para erro tests |
| `invalid_payload` | function | Payload invalido | Para erro tests |

---

## Boas Praticas

### ✅ DO (Faca)

```python
# 1. Usar fixtures apropriadas para o tipo de teste
@pytest.mark.unit
def test_unit_logic(mock_location_repo, location_data):
    """Use mocks em unit tests."""
    pass

@pytest.mark.integration
def test_database_logic(integration_db_session, location_in_db):
    """Use BD real em integration tests."""
    pass

@pytest.mark.api
def test_api_endpoint(client, location_in_db, assert_api_success):
    """Use TestClient em API tests."""
    pass


# 2. Combinar multiplas fixtures
def test_complex_scenario(
    integration_db_session,
    location_in_db,
    user_in_db,
    redis_client,
    assert_valid_location,
):
    """Multiplas fixtures trabalham juntas."""
    pass


# 3. Usar helpers para assertions
def test_with_helper(location_data, assert_valid_location):
    """Helpers deixam tests mais legivel."""
    assert_valid_location(location_data)  # Limpo e intuitivo
```

### ❌ DON'T (Evite)

```python
# 1. Nao misturar mocks com BD real
def test_bad(mock_redis, integration_db_session):
    """Contradicao - qual usar?"""
    pass

# 2. Nao fazer queries diretas em unit tests
def test_bad_unit(mock_location_repo):
    """Unit tests devem ser rapidos, sem IO."""
    result = database.query(Location).all()  # ERRADO!
    pass

# 3. Nao ignorar o scope das fixtures
@pytest.mark.integration
def test_ignore_scope(integration_db_engine):
    """Engine eh session scope - nao limpa apos teste."""
    # Dados podem vazar entre testes!
    pass
```

---

## Executar Testes por Categoria

```bash
# Descobrir testes
pytest tests --collect-only -v

# Unit tests apenas
pytest tests/unit -v -m unit
pytest tests/unit -v --tb=short

# Integration tests apenas
pytest tests/integration -v -m integration
pytest tests/integration -v -s  # Show prints

# API tests apenas
pytest tests/api -v -m api
pytest tests/api -v --tb=long

# E2E tests
pytest tests/e2e -v -m e2e

# Rodar tudo com cobertura
pytest tests -v --cov=backend --cov-report=html --cov-report=term-missing

# Rodar tudo paralelizado (4x mais rapido)
pytest tests -v -n auto

# Rodar test especifico
pytest tests/unit/test_models.py::test_location_validation -v
```

---

## Proximas Etapas

Apos criar conftest.py:
1. ✅ FASE 2: Conftest specificos criados (completo)
2. ⏳ FASE 3: Mover testes backend/tests/ → tests/unit/
3. ⏳ PASSO 11: Implementar Frontend Cache
4. ⏳ PASSO 12: Implementar Frontend Favorites
5. ⏳ PASSO 13: E2E Testing
6. ⏳ PASSO 14: Documentacao Final

**Tempo restante: ~2 horas para tudo**
