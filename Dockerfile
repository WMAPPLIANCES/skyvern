# Stage 1: Instalar dependências Python usando Poetry
FROM python:3.11 as requirements-stage
WORKDIR /tmp
RUN pip install poetry
# Instala o plugin necessário para exportar requirements.txt
RUN poetry self add poetry-plugin-export
COPY ./pyproject.toml /tmp/pyproject.toml
COPY ./poetry.lock /tmp/poetry.lock
# Exporta as dependências para requirements.txt sem hashes
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

# Stage 2: Construir a imagem final
FROM python:3.11-slim-bookworm
WORKDIR /app

# Copia o requirements.txt gerado no stage anterior
COPY --from=requirements-stage /tmp/requirements.txt /app/requirements.txt

# Atualiza pip e instala as dependências Python
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Instala Playwright e suas dependências de sistema
RUN playwright install-deps
RUN playwright install

# Instala dependências de sistema adicionais e limpa o cache do apt
RUN apt-get update && apt-get install -y \
    xauth \
    x11-apps \
    netpbm \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# --- Instalação do Node.js via NVM ---
RUN mkdir -p /usr/local/nvm
ENV NVM_DIR /usr/local/nvm
# Use uma versão LTS estável ou a específica necessária
ENV NODE_VERSION v20.12.2
# Instala nvm, node e npm
RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
RUN /bin/bash -c "source $NVM_DIR/nvm.sh && nvm install $NODE_VERSION && nvm use --delete-prefix $NODE_VERSION && nvm alias default $NODE_VERSION && nvm cache clear"
# Adiciona node e npm ao PATH permanentemente para futuras sessões
ENV NODE_PATH $NVM_DIR/versions/node/$NODE_VERSION/lib/node_modules
ENV PATH $NVM_DIR/versions/node/$NODE_VERSION/bin:$PATH
# Confirma as versões (opcional, bom para debug)
RUN node -v
RUN npm -v

# --- Instalação do Bitwarden CLI ---
# Instala globalmente usando o npm gerenciado pelo NVM
RUN npm install -g @bitwarden/cli@2024.9.0
# Verifica a versão (também inicializa a config)
RUN bw --version

# Copia o código da aplicação para o diretório de trabalho
COPY . /app

# Define variáveis de ambiente para a aplicação Skyvern
ENV PYTHONPATH="/app:${PYTHONPATH}"
ENV VIDEO_PATH=/data/videos
ENV HAR_PATH=/data/har
ENV LOG_PATH=/data/log
ENV ARTIFACT_STORAGE_PATH=/data/artifacts

# --- Configuração do MCP (Management Control Plane) ---
ENV SKYVERN_MCP_ENABLED=true
ENV MCP_PORT=9090
# Adiciona MCP_HOST para garantir que escute em todas as interfaces,
# caso o servidor web interno do MCP use esta variável.
ENV MCP_HOST=0.0.0.0

# Expõe as portas que a aplicação usará
EXPOSE 8000 # Porta da API principal
EXPOSE 9090 # Porta do MCP/UI

# Copia e torna o script de entrypoint executável
COPY ./entrypoint-mcp.sh /app/entrypoint-mcp.sh
RUN chmod +x /app/entrypoint-mcp.sh

# Define o comando que será executado quando o container iniciar
CMD [ "/bin/bash", "/app/entrypoint-mcp.sh" ]
