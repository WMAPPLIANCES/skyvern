# Dockerfile para o backend Skyvern (API + MCP)

# Estágio para instalar dependências usando Poetry e exportar requirements.txt
FROM python:3.11 AS requirements-stage
WORKDIR /tmp

# Atualizar pip e instalar uma versão específica do Poetry
RUN pip install --upgrade pip
RUN pip uninstall -y poetry || true # Tenta desinstalar qualquer versão existente
RUN pip install poetry==1.8.2 # Instala uma versão recente e estável do Poetry

# Verificar a versão do Poetry (para debugging nos logs)
RUN poetry --version

# Copiar arquivos de definição de projeto e dependências
# Ajuste os caminhos se seus arquivos estiverem em um subdiretório (ex: ./backend/)
COPY ./pyproject.toml /tmp/pyproject.toml
COPY ./poetry.lock /tmp/poetry.lock

# Exportar dependências de produção para requirements.txt
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

# Estágio final da imagem
FROM python:3.11-slim-bookworm
WORKDIR /app

# Definir variáveis de ambiente para o build (podem ser sobrescritas no runtime pelo Easypanel)
ENV DEBIAN_FRONTEND=noninteractive
# Para logs não bufferizados, garantindo que saiam imediatamente
ENV PYTHONUNBUFFERED=1
# O warning sobre PYTHONPATH indefinido aqui é geralmente aceitável
ENV PYTHONPATH="/app:${PYTHONPATH}"

# Copiar o requirements.txt do estágio anterior
COPY --from=requirements-stage /tmp/requirements.txt /app/requirements.txt

# Instalar dependências Python do requirements.txt e adicionar alembic
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir --upgrade -r /app/requirements.txt && \
    pip install alembic # <--- INSTALAR ALEMBIC DIRETAMENTE

# Instalar Playwright e suas dependências de sistema
RUN playwright install-deps && \
    playwright install # Você pode especificar navegadores aqui, ex: playwright install chromium

# Instalar outras dependências do sistema
RUN apt-get update && \
    apt-get install -y xauth x11-apps netpbm curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Instalar Node.js e Bitwarden CLI (se realmente necessário para o runtime do backend)
RUN mkdir -p /usr/local/nvm
ENV NVM_DIR=/usr/local/nvm
ENV NODE_VERSION=v20.12.2
RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash && \
    /bin/bash -c "source ${NVM_DIR}/nvm.sh && \
                  nvm install ${NODE_VERSION} && \
                  nvm use --delete-prefix ${NODE_VERSION} && \
                  npm install -g @bitwarden/cli@2024.9.0 && \
                  bw --version"
ENV NODE_PATH=${NVM_DIR}/versions/node/${NODE_VERSION}/bin
ENV PATH=${NODE_PATH}:${PATH}

# Copiar o restante do código da aplicação
# Ajuste o COPY se seu código Python estiver em um subdiretório (ex: ./backend)
COPY . /app

# Caminhos para dados (mapear volumes persistentes no Easypanel para /data)
ENV DATA_BASE_PATH=/data
ENV VIDEO_PATH=${DATA_BASE_PATH}/videos
ENV HAR_PATH=${DATA_BASE_PATH}/har
ENV LOG_PATH=${DATA_BASE_PATH}/log
ENV ARTIFACT_STORAGE_PATH=${DATA_BASE_PATH}/artifacts

# Configuração MCP (Media Capture Processor)
ENV SKYVERN_MCP_ENABLED=true
# Porta interna do contêiner para o MCP
ENV MCP_PORT=9090

# Expor as portas que a aplicação usa
# API principal
EXPOSE 8000
# MCP
EXPOSE 9090

# Copiar e dar permissão ao script de entrypoint
# Ajuste o COPY se seu entrypoint-mcp.sh estiver em um subdiretório (ex: ./backend)
COPY ./entrypoint-mcp.sh /app/entrypoint-mcp.sh
RUN chmod +x /app/entrypoint-mcp.sh

# Comando para iniciar a aplicação
CMD [ "/bin/bash", "/app/entrypoint-mcp.sh" ]
