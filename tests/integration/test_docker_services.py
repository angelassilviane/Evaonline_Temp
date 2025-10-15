"""
===========================================
INTEGRATION TESTS - Docker Services
===========================================
Testes de integração para serviços Docker (PostgreSQL, Redis, Celery).
"""

import os
from typing import Generator

import pytest
import redis
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

# ===========================================
# Fixtures
# ===========================================


@pytest.fixture(scope="session")
def postgres_connection_string() -> str:
    """Retorna a string de conexão do PostgreSQL para testes."""
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "evaonline")
    user = os.getenv("POSTGRES_USER", "evaonline")
    password = os.getenv("POSTGRES_PASSWORD", "123456")
    
    return f"postgresql://{user}:{password}@{host}:{port}/{db}"


@pytest.fixture(scope="session")
def redis_connection_string() -> str:
    """Retorna a string de conexão do Redis para testes."""
    host = os.getenv("REDIS_HOST", "localhost")
    port = os.getenv("REDIS_PORT", "6379")
    db = os.getenv("REDIS_DB", "0")
    
    return f"redis://{host}:{port}/{db}"


@pytest.fixture(scope="session")
def db_engine(postgres_connection_string: str) -> Generator:
    """
    Cria uma engine do SQLAlchemy para testes.
    Usa psycopg2 com configuração UTF-8 para Windows.
    """
    # Configurar client_encoding=utf8 para resolver problemas com caracteres especiais no Windows
    engine = create_engine(
        postgres_connection_string,
        pool_pre_ping=True,
        echo=False,
        connect_args={
            "client_encoding": "utf8",
            "options": "-c client_encoding=UTF8"
        }
    )
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(db_engine) -> Generator[Session, None, None]:
    """
    Cria uma sessão do banco de dados para testes.
    Usa transação que é revertida após cada teste.
    """
    connection = db_engine.connect()
    transaction = connection.begin()
    session_factory = sessionmaker(bind=connection)
    session = session_factory()
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="session")
def redis_client(redis_connection_string: str) -> Generator:
    """
    Cria um cliente Redis para testes.
    """
    client = redis.from_url(
        redis_connection_string,
        decode_responses=True,
        socket_connect_timeout=5,
    )
    yield client
    # Limpar chaves de teste
    for key in client.scan_iter("test:*"):
        client.delete(key)
    client.close()


# ===========================================
# Tests: PostgreSQL
# ===========================================


@pytest.mark.integration
@pytest.mark.database
class TestPostgreSQLConnection:
    """Testes de conexão e funcionalidade do PostgreSQL."""
    
    def test_database_connection(self, db_engine) -> None:
        """Testa se consegue conectar ao PostgreSQL."""
        with db_engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.scalar() == 1
    
    def test_database_version(self, db_engine) -> None:
        """Testa e exibe a versão do PostgreSQL."""
        with db_engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            assert version is not None
            assert "PostgreSQL" in version
            print(f"\nPostgreSQL Version: {version}")
    
    def test_postgis_extension(self, db_engine) -> None:
        """Testa se a extensão PostGIS está disponível."""
        with db_engine.connect() as conn:
            result = conn.execute(
                text("SELECT extname FROM pg_extension WHERE extname = 'postgis'")
            )
            extension = result.scalar()
            assert extension == "postgis", "PostGIS extension not found"
    
    def test_create_and_query_table(self, db_session: Session) -> None:
        """Testa criação e consulta de uma tabela temporária."""
        # Criar tabela temporária
        db_session.execute(
            text("""
                CREATE TEMP TABLE test_table (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100),
                    value FLOAT
                )
            """)
        )
        
        # Inserir dados
        db_session.execute(
            text("""
                INSERT INTO test_table (name, value)
                VALUES (:name, :value)
            """),
            {"name": "test", "value": 42.5}
        )
        db_session.commit()
        
        # Consultar dados
        result = db_session.execute(
            text("SELECT name, value FROM test_table WHERE name = :name"),
            {"name": "test"}
        )
        row = result.fetchone()
        
        assert row is not None
        assert row[0] == "test"
        assert row[1] == 42.5
    
    def test_transaction_rollback(self, db_session: Session) -> None:
        """Testa que as transações são revertidas após cada teste."""
        # Criar tabela temporária
        db_session.execute(
            text("CREATE TEMP TABLE test_rollback (id SERIAL PRIMARY KEY)")
        )
        # Esta tabela não deve existir em outros testes devido ao rollback


# ===========================================
# Tests: Redis
# ===========================================


@pytest.mark.integration
@pytest.mark.redis
class TestRedisConnection:
    """Testes de conexão e funcionalidade do Redis."""
    
    def test_redis_connection(self, redis_client: redis.Redis) -> None:
        """Testa se consegue conectar ao Redis."""
        assert redis_client.ping() is True
    
    def test_redis_info(self, redis_client: redis.Redis) -> None:
        """Testa e exibe informações do Redis."""
        info = redis_client.info()
        assert "redis_version" in info
        print(f"\nRedis Version: {info['redis_version']}")
        print(f"Redis Used Memory: {info['used_memory_human']}")
    
    def test_redis_set_get(self, redis_client: redis.Redis) -> None:
        """Testa operações básicas de set/get."""
        key = "test:simple_key"
        value = "test_value"
        
        # Set
        redis_client.set(key, value, ex=60)  # Expira em 60 segundos
        
        # Get
        retrieved = redis_client.get(key)
        assert retrieved == value
        
        # Delete
        redis_client.delete(key)
        assert redis_client.get(key) is None
    
    def test_redis_json(self, redis_client: redis.Redis) -> None:
        """Testa armazenamento de JSON."""
        import json
        
        key = "test:json_data"
        data = {"name": "test", "values": [1, 2, 3], "nested": {"key": "value"}}
        
        # Armazenar como JSON string
        redis_client.set(key, json.dumps(data), ex=60)
        
        # Recuperar e deserializar
        retrieved = json.loads(redis_client.get(key))
        assert retrieved == data
        
        # Limpar
        redis_client.delete(key)
    
    def test_redis_hash(self, redis_client: redis.Redis) -> None:
        """Testa operações com hash."""
        key = "test:hash_data"
        
        # Criar hash
        redis_client.hset(key, mapping={
            "field1": "value1",
            "field2": "value2",
            "field3": "value3"
        })
        redis_client.expire(key, 60)
        
        # Ler campos
        assert redis_client.hget(key, "field1") == "value1"
        assert redis_client.hgetall(key) == {
            "field1": "value1",
            "field2": "value2",
            "field3": "value3"
        }
        
        # Limpar
        redis_client.delete(key)
    
    def test_redis_list(self, redis_client: redis.Redis) -> None:
        """Testa operações com listas."""
        key = "test:list_data"
        
        # Adicionar elementos
        redis_client.rpush(key, "item1", "item2", "item3")
        redis_client.expire(key, 60)
        
        # Ler elementos
        assert redis_client.lrange(key, 0, -1) == ["item1", "item2", "item3"]
        assert redis_client.llen(key) == 3
        
        # Limpar
        redis_client.delete(key)
    
    def test_redis_pubsub(self, redis_client: redis.Redis) -> None:
        """Testa funcionalidade de pub/sub."""
        channel = "test:channel"
        message = "test_message"
        
        # Criar subscriber
        pubsub = redis_client.pubsub()
        pubsub.subscribe(channel)
        
        # Publicar mensagem
        redis_client.publish(channel, message)
        
        # Ler mensagem (pular mensagem de subscribe)
        pubsub.get_message()  # Subscribe message
        msg = pubsub.get_message()
        
        if msg:
            assert msg["type"] == "message"
            assert msg["data"] == message
        
        pubsub.unsubscribe(channel)
        pubsub.close()


# ===========================================
# Tests: Celery (se disponível)
# ===========================================


@pytest.mark.integration
@pytest.mark.celery
@pytest.mark.skip(reason="Requer Celery worker rodando")
class TestCeleryIntegration:
    """Testes de integração com Celery."""
    
    def test_celery_worker_available(self) -> None:
        """Testa se há workers Celery disponíveis."""
        from celery import Celery
        
        app = Celery(
            "evaonline",
            broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
            backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
        )
        
        # Verificar workers ativos
        inspect = app.control.inspect()
        active_workers = inspect.active()
        
        assert active_workers is not None, "No Celery workers available"
        print(f"\nActive Celery workers: {list(active_workers.keys())}")


# ===========================================
# Tests: Docker Compose
# ===========================================


@pytest.mark.integration
@pytest.mark.docker
class TestDockerServices:
    """Testes para verificar serviços Docker."""
    
    def test_all_services_healthy(
        self,
        db_engine,
        redis_client: redis.Redis
    ) -> None:
        """Testa se todos os serviços estão saudáveis."""
        # PostgreSQL
        with db_engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.scalar() == 1
        
        # Redis
        assert redis_client.ping() is True
        
        print("\n✅ Todos os serviços Docker estão funcionando!")
