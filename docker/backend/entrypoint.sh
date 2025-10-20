#!/bin/bash

# =============================================================================
# ENTRYPOINT OTIMIZADO PARA PRODUÇÃO - EVAonline Backend
# =============================================================================

set -euo pipefail

# Configurações
MAX_RETRIES=${MAX_RETRIES:-30}
RETRY_INTERVAL=${RETRY_INTERVAL:-2}
SERVICE=${SERVICE:-api}

# Função de logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Função para aguardar serviço
wait_for_service() {
    local host=$1
    local port=$2
    local service_name=$3
    local attempt=1

    log "🕐 Aguardando $service_name em $host:$port (máximo: ${MAX_RETRIES}tentativas)..."

    while [ $attempt -le $MAX_RETRIES ]; do
        if nc -z -w 2 "$host" "$port" 2>/dev/null; then
            log "✅ $service_name está disponível!"
            return 0
        fi

        log "⏳ Tentativa $attempt/$MAX_RETRIES: $service_name ainda não está disponível..."
        sleep $RETRY_INTERVAL
        ((attempt++))
    done

    log "❌ ERRO: $service_name não ficou disponível após $MAX_RETRIES tentativas"
    return 1
}

# Função para verificar saúde do banco
check_database_health() {
    log "🔍 Verificando saúde do banco de dados..."
    
    if python -c "
import sys
try:
    from backend.database.connection import get_db
    from sqlalchemy import text
    db = next(get_db())
    db.execute(text('SELECT 1'))
    print('✅ Conexão com banco estabelecida e saudável')
    sys.exit(0)
except Exception as e:
    print(f'❌ Erro na conexão com banco: {e}')
    sys.exit(1)
"; then
        return 0
    else
        return 1
    fi
}

# Função para executar migrações
run_migrations() {
    log "🔄 Verificando migrações do banco de dados..."
    
    if command -v alembic >/dev/null 2>&1; then
        if alembic current >/dev/null 2>&1; then
            log "📦 Aplicando migrações pendentes..."
            if alembic upgrade head; then
                log "✅ Migrações aplicadas com sucesso"
            else
                log "⚠️  Aviso: Falha ao aplicar migrações"
            fi
        else
            log "ℹ️  Alembic não configurado, criando tabelas diretamente..."
            python -c "
try:
    from backend.database.connection import engine
    from backend.database.models import Base
    Base.metadata.create_all(bind=engine)
    print('✅ Tabelas criadas/verificadas com sucesso')
except Exception as e:
    print(f'⚠️  Aviso ao criar tabelas: {e}')
"
        fi
    else
        log "ℹ️  Alembic não disponível, criando tabelas diretamente..."
        python -c "
try:
    from backend.database.connection import engine
    from backend.database.models import Base
    Base.metadata.create_all(bind=engine)
    print('✅ Tabelas criadas/verificadas com sucesso')
except Exception as e:
    print(f'⚠️  Aviso ao criar tabelas: {e}')
"
    fi
}

# Função principal
main() {
    log "🚀 Iniciando EVAonline Backend (Serviço: $SERVICE)"
    
    # Aguardar dependências baseadas no serviço
    case "$SERVICE" in
        "api"|"all")
            wait_for_service "${POSTGRES_HOST:-postgres}" "${POSTGRES_PORT:-5432}" "PostgreSQL"
            wait_for_service "${REDIS_HOST:-redis}" "6379" "Redis"
            
            # Verificar saúde do banco
            if ! check_database_health; then
                log "❌ Banco de dados não está saudável, saindo..."
                exit 1
            fi
            
            # Executar migrações
            run_migrations
            ;;
        "worker"|"beat"|"flower")
            wait_for_service "${REDIS_HOST:-redis}" "6379" "Redis"
            ;;
    esac
    
    # Iniciar serviço específico
    case "$SERVICE" in
        "api")
            log "🌐 Iniciando API FastAPI..."
            exec gunicorn backend.main:app \
                --bind 0.0.0.0:8000 \
                --workers 4 \
                --worker-class uvicorn.workers.UvicornWorker \
                --timeout 120 \
                --keep-alive 5 \
                --max-requests 1000 \
                --max-requests-jitter 100 \
                --access-logfile - \
                --error-logfile - \
                --log-level info
            ;;
            
        "worker")
            log "🔧 Iniciando Celery Worker..."
            exec celery -A backend.infrastructure.celery.celery_config worker \
                --loglevel=info \
                --concurrency=4 \
                --prefetch-multiplier=4 \
                --task-events \
                --without-gossip \
                --without-mingle \
                --without-heartbeat
            ;;
            
        "beat")
            log "⏰ Iniciando Celery Beat..."
            exec celery -A backend.infrastructure.celery.celery_config beat \
                --loglevel=info \
                --scheduler redbeat.RedBeatScheduler
            ;;
            
        "flower")
            log "📊 Iniciando Flower Monitor..."
            exec celery -A backend.infrastructure.celery.celery_config flower \
                --address=0.0.0.0 \
                --port=5555 \
                --basic_auth=admin:admin \
                --url_prefix=flower
            ;;
            
        "all")
            log "🔄 Iniciando todos os serviços em modo desenvolvimento..."
            
            # Iniciar API em background
            gunicorn backend.main:app \
                --bind 0.0.0.0:8000 \
                --workers 2 \
                --worker-class uvicorn.workers.UvicornWorker \
                --reload \
                --log-level debug &
            
            # Iniciar worker em background
            celery -A backend.infrastructure.celery.celery_config worker \
                --loglevel=info \
                --concurrency=2 &
            
            # Iniciar beat em background
            celery -A backend.infrastructure.celery.celery_config beat \
                --loglevel=info &
            
            # Aguardar um pouco
            sleep 5
            
            # Manter container rodando
            log "✅ Todos os serviços iniciados. Container ativo..."
            wait
            ;;
            
        *)
            log "❌ Serviço desconhecido: $SERVICE"
            log "📚 Serviços disponíveis: api, worker, beat, flower, all"
            exit 1
            ;;
    esac
}

# Capturar sinais para shutdown graceful
trap 'log "🛑 Recebido sinal de desligamento"; exit 0' SIGTERM SIGINT

# Executar função principal
main "$@"