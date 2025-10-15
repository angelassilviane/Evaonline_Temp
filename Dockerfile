# ===========================================
# MULTI-STAGE DOCKERFILE - EVAonline
# ===========================================
# Build otimizado com múltiplos estágios para reduzir tamanho da imagem final

# ===========================================
# Stage 1: Builder
# ===========================================
FROM python:3.10-slim as builder

LABEL maintainer="Ângela Cunha Soares <angelassilviane@gmail.com>"
LABEL stage="builder"

# Instalar dependências de build
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Criar diretório de trabalho
WORKDIR /build

# Copiar apenas requirements para cache otimizado
COPY requirements.txt .

# Criar wheels das dependências (mais rápido para instalar depois)
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip wheel --no-cache-dir --wheel-dir /build/wheels \
    -r requirements.txt \
    gunicorn \
    uvicorn[standard] \
    prometheus_client

# ===========================================
# Stage 2: Runtime
# ===========================================
FROM python:3.10-slim as runtime

LABEL maintainer="Ângela Cunha Soares <angelassilviane@gmail.com>"
LABEL stage="runtime"

# Instalar apenas dependências de runtime (não precisa de build-essential)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    locales \
    curl \
    dos2unix \
    netcat-traditional \
    libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Configurar localidade
RUN echo "pt_BR.UTF-8 UTF-8" > /etc/locale.gen && \
    locale-gen pt_BR.UTF-8 && \
    update-locale LANG=pt_BR.UTF-8

# Criar usuário não-root antes de copiar arquivos
RUN useradd -m -u 1000 -s /bin/bash evaonline

# Configurar variáveis de ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    LANG=pt_BR.UTF-8 \
    LANGUAGE=pt_BR:pt \
    LC_ALL=pt_BR.UTF-8 \
    TZ=America/Sao_Paulo \
    SERVICE=all

WORKDIR /app

# Copiar wheels do builder
COPY --from=builder /build/wheels /wheels

# Instalar dependências a partir dos wheels (muito mais rápido)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --no-index --find-links=/wheels /wheels/* && \
    rm -rf /wheels

# Copiar entrypoint e configurar permissões
COPY --chown=evaonline:evaonline entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh && \
    dos2unix /usr/local/bin/entrypoint.sh

# Criar diretórios necessários com permissões corretas
RUN mkdir -p /app/logs /app/data /app/temp && \
    chown -R evaonline:evaonline /app

# Copiar código da aplicação
COPY --chown=evaonline:evaonline . .

# Mudar para usuário não-root
USER evaonline

# Expor portas
EXPOSE 8000 8050

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || \
    curl -f http://localhost:8050/ || \
    exit 1

# Comando padrão
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

# ===========================================
# Stage 3: Development (opcional)
# ===========================================
FROM runtime as development

LABEL stage="development"

USER root

# Nota: requirements.txt já contém todas as dependências
# (produção + desenvolvimento), não precisa de arquivo separado

# Reinstalar build tools para desenvolvimento
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    vim \
    git \
    && rm -rf /var/lib/apt/lists/*

USER evaonline

# Ativar reload automático em dev
ENV FASTAPI_RELOAD=true \
    DASH_DEBUG=true

# ===========================================
# Stage 4: Testing (opcional)
# ===========================================
FROM development as testing

LABEL stage="testing"

USER root

# Copiar testes
COPY --chown=evaonline:evaonline tests/ /app/tests/

USER evaonline

# Comando para rodar testes
CMD ["pytest", "-v", "--cov=backend", "--cov-report=term-missing"]
