# =============================================================================
# DOCKERFILE OTIMIZADO PARA PRODUÇÃO - EVAonline Backend
# =============================================================================

# Stage 1: Builder
FROM python:3.11-slim as builder

LABEL maintainer="EVAonline Team <angelassilviane@gmail.com>"
LABEL stage="builder"

# Instalar dependências de build
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /build

# Copiar requirements
COPY requirements.txt .

# Criar wheels otimizados
RUN pip install --no-cache-dir --upgrade pip wheel && \
    pip wheel --no-cache-dir --wheel-dir /wheels \
    -r requirements.txt \
    gunicorn \
    uvicorn[standard]

# Stage 2: Runtime
FROM python:3.11-slim as runtime

LABEL maintainer="EVAonline Team <angelassilviane@gmail.com>"
LABEL stage="runtime"

# Instalar dependências de runtime
RUN apt-get update && apt-get install -y \
    curl \
    netcat-traditional \
    libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Criar usuário não-root
RUN useradd -m -u 1000 -s /bin/bash evaonline

# Configurar ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PYTHONHASHSEED=random \
    TZ=America/Sao_Paulo \
    SERVICE=api

WORKDIR /app

# Copiar wheels do builder
COPY --from=builder /wheels /wheels

# Instalar dependências
RUN pip install --no-cache-dir --no-index --find-links=/wheels /wheels/* && \
    rm -rf /wheels

# Copiar código da aplicação
COPY --chown=evaonline:evaonline backend/ /app/backend/
COPY --chown=evaonline:evaonline config/ /app/config/

# Copiar e configurar entrypoint
COPY --chown=evaonline:evaonline docker/backend/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Criar diretórios necessários
RUN mkdir -p /app/logs /app/data /app/temp && \
    chown -R evaonline:evaonline /app

# Mudar para usuário não-root
USER evaonline

# Expor portas
EXPOSE 8000

# Healthcheck otimizado
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

# Comando padrão para produção
CMD ["gunicorn", "backend.main:app", \
    "--bind", "0.0.0.0:8000", \
    "--workers", "4", \
    "--worker-class", "uvicorn.workers.UvicornWorker", \
    "--timeout", "120", \
    "--keep-alive", "5", \
    "--max-requests", "1000", \
    "--max-requests-jitter", "100", \
    "--access-logfile", "-", \
    "--error-logfile", "-", \
    "--log-level", "info"]