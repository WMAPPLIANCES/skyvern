# Dockerfile para o backend Skyvern (API + MCP)
FROM python:3.11 as requirements-stage
WORKDIR /tmp
RUN pip install poetry
# poetry-plugin-export pode não ser necessário se você estiver usando versões mais recentes do poetry
# RUN poetry self add poetry-plugin-export
COPY ./pyproject.toml ./poetry.lock /tmp/
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

FROM python:3.11-slim-bookworm
WORKDIR /app

# Copiar primeiro o requirements.txt e instalar as dependências
COPY --from=requirements-stage /tmp/requirements.txt /app/requirements.txt
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir --upgrade -r /app/requirements.txt

# Instalar Playwright e suas dependências
RUN playwright install-deps
RUN playwright install # Você pode especificar navegadores aqui, ex: playwright install chromium

# Instalar outras dependências do sistema
RUN apt-get update && apt-get install -y xauth x11-apps netpbm curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Instalar Node.js e Bitwarden CLI (se realmente necessário para o runtime do backend)
# Considere se estas ferramentas são apenas para desenvolvimento/build ou se o backend Python as utiliza diretamente.
RUN mkdir -p /usr/local/nvm
ENV NVM_DIR /usr/local/nvm
ENV NODE_VERSION v20.12.2 # Mantenha atualizado conforme necessário
RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash && \
    /bin/bash -c "source $NVM_DIR/nvm.sh && \
                  nvm install $NODE_VERSION && \
                  nvm use --delete-prefix $NODE_VERSION && \
                  npm install -g @bitwarden/cli@2024.9.0 && \
                  bw --version" # bw --version também inicializa a config
ENV NODE_PATH $NVM_DIR/versions/node/$NODE_VERSION/bin
ENV PATH $NODE_PATH:$PATH

# Copiar o restante do código da aplicação
COPY . /app

ENV PYTHONPATH="/app:$PYTHONPATH"
ENV PYTHONUNBUFFERED=1 # Para logs não bufferizados

# Caminhos para dados (mapear volumes persistentes no Easypanel para /data)
ENV DATA_BASE_PATH=/data
ENV VIDEO_PATH=${DATA_BASE_PATH}/videos
ENV HAR_PATH=${DATA_BASE_PATH}/har
ENV LOG_PATH=${DATA_BASE_PATH}/log
ENV ARTIFACT_STORAGE_PATH=${DATA_BASE_PATH}/artifacts

# Configuração MCP
ENV SKYVERN_MCP_ENABLED=true
ENV MCP_PORT=9090 # Porta interna do contêiner para o MCP

# Expor as portas
EXPOSE 8000 # API principal
EXPOSE 9090 # MCP

COPY ./entrypoint-mcp.sh /app/entrypoint-mcp.sh
RUN chmod +x /app/entrypoint-mcp.sh

CMD [ "/bin/bash", "/app/entrypoint-mcp.sh" ]
