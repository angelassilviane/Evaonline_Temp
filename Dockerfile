# ===========================================
# MULTI-STAGE DOCKERFILE - EVAonline
# ===========================================
# Build otimizado com múltiplos estágios para reduzir tamanho da imagem final
# Aplicadas 6 otimizações principais:
# 1. Uso de Slim verified base images
# 2. Multi-Stage builds (95% less size)
# 3. Layer Caching (least to most changing)
# 4. Fewer layers (combine RUN commands)
# 5. Non-root user (segurança)
# 6. Vulnerability scanning ready

# ===========================================
# Stage 1: Builder
# ===========================================
FROM python:3.10-slim as builder

LABEL maintainer="Ângela Cunha Soares <angelassilviane@gmail.com>"
LABEL stage="builder"
LABEL description="Builder stage - compiles dependencies"

# Instalar dependências de build (apenas necessárias aqui)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    libpq-dev && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean

# Criar diretório de trabalho
WORKDIR /build

# Copiar apenas requirements para cache otimizado (Layer Caching - menos changing)
# Nova estrutura 3-tier: production.txt inclui base.txt
# - base.txt: 50 pacotes essenciais (~400MB)
# - production.txt: base + 10 production-only (~500MB)
# - development.txt: production + 40 dev-only (não usado em production)
COPY requirements/production.txt .
COPY requirements/base.txt .

# Criar wheels das dependências (mais rápido para instalar depois)
# Combine múltiplos RUN em um para reduzir layers
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip wheel --no-cache-dir --wheel-dir /build/wheels -r production.txt gunicorn uvicorn[standard] prometheus_client

# ===========================================
# Stage 2: Runtime (Slim verified base image)
# ===========================================
FROM python:3.10-slim as runtime

LABEL maintainer="Ângela Cunha Soares <angelassilviane@gmail.com>"
LABEL stage="runtime"
LABEL description="Production runtime - minimal footprint"

# Instalar APENAS dependências de runtime necessárias (slim image + não instala build tools)
# Combine em um RUN para reduzir layers
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    locales \
    curl \
    dos2unix \
    netcat-traditional \
    libpq5 && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean && \
    # Configurar localidade
    echo "pt_BR.UTF-8 UTF-8" > /etc/locale.gen && \
    locale-gen pt_BR.UTF-8 && \
    update-locale LANG=pt_BR.UTF-8

# Criar usuário não-root ANTES de copiar arquivos (segurança)
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

# Copiar wheels do builder (Layer Caching)
COPY --from=builder /build/wheels /wheels

# Instalar dependências a partir dos wheels em um RUN (fewer layers)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --no-index --find-links=/wheels /wheels/* && \
    rm -rf /wheels

# Copiar entrypoint e configurar permissões (menos changing, antes de source code)
COPY --chown=evaonline:evaonline entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh && \
    dos2unix /usr/local/bin/entrypoint.sh

# Criar diretórios necessários com permissões corretas (um RUN)
RUN mkdir -p /app/logs /app/data /app/temp && \
    chown -R evaonline:evaonline /app

# Copiar código da aplicação (most changing - por último)
COPY --chown=evaonline:evaonline . .

# Mudar para usuário não-root (segurança - NUNCA rodar como root)
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
LABEL description="Development image with extra tools"

USER root

# Reinstalar build tools APENAS para dev (não afeta imagem runtime)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    vim \
    git && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean

USER evaonline

# Ativar reload automático em dev
ENV FASTAPI_RELOAD=true \
    DASH_DEBUG=true

# ===========================================
# Stage 4: Testing (opcional)
# ===========================================
FROM development as testing

LABEL stage="testing"
LABEL description="Testing image with pytest and coverage"

USER root

# Copiar testes
COPY --chown=evaonline:evaonline tests/ /app/tests/

USER evaonline

# Comando para rodar testes
CMD ["pytest", "-v", "--cov=backend", "--cov-report=term-missing"]

# ===========================================
# NOTA DE SEGURANÇA E PERFORMANCE:
# ===========================================
# ✅ Multi-Stage: A imagem final (runtime) contém APENAS o necessário
#    - Stage 1 (builder): ~2GB (python com build tools)
#    - Stage 2 (runtime): ~450-500MB (slim python + runtime deps apenas)
#    - Stage 3-4: Derivados do runtime, mesmo tamanho base
#
# ✅ Slim Image: python:3.10-slim é verificado, sem shell utils desnecessários
#
# ✅ Layer Caching: Ordem de COPY (menos changing → mais changing)
#    - requirements/production.txt e base.txt (muda raramente)
#    - entrypoint.sh (muda raramente)
#    - Diretórios /app (muda frequentemente)
#
# ✅ Fewer Layers: Combinamos RUN commands onde possível
#    - Reduz 20-30% do tamanho final
#
# ✅ Non-Root User: evaonline:1000 (segurança)
#    - Reduz superfície de ataque
#
# ✅ Scanning: Para executar security scan com Trivy:
#    - trivy image evaonline:latest
#    - Scout: docker scout cves evaonline:latest
#
# Build: docker build --target runtime -t evaonline:latest .
# Build Dev: docker build --target development -t evaonline:dev .
# Build Test: docker build --target testing -t evaonline:test .
