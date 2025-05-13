# Dockerfile para o backend Skyvern (API + MCP)

# Estágio para instalar dependências usando Poetry e exportar requirements.txt
FROM python:3.11 AS requirements-stage
WORKDIR /tmp

RUN pip install --upgrade pip
RUN pip uninstall -y poetry || true
RUN pip install poetry==1.8.2
RUN poetry --version

COPY ./pyproject.toml /tmp/pyproject.toml
COPY ./poetry.lock /tmp/poetry.lock
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

# Estágio final da imagem
FROM python:3.11-slim-bookworm
WORKDIR /app

ENV DEBIAN_FRONTEND=noninteractive
# Para logs não bufferizados, garantindo que saiam imediatamente
ENV PYTHONUNBUFFERED=1
# O warning sobre PYTHONPATH indefinido aqui é geralmente aceitável
ENV PYTHONPATH="/app:${PYTHONPATH}"

COPY --from=requirements-stage /tmp/requirements.txt /app/requirements.txt

RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir --upgrade -r /app/requirements.txt && \
    pip install alembic

RUN playwright install-deps && \
    playwright install chromium

# Instalar outras dependências do sistema, incluindo xvfb e fontes e x11vnc
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    xauth \
    x11-apps \
    netpbm \
    curl \
    xvfb \
    xfonts-base \
    xfonts-75dpi \
    xfonts-100dpi \
    libxfont2 \
    libxft2 \
    libfreetype6 \
    libfontconfig1 \
    x11vnc \
    && apt-get clean && \
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

COPY . /app

ENV DATA_BASE_PATH=/data
ENV VIDEO_PATH=${DATA_BASE_PATH}/videos
ENV HAR_PATH=${DATA_BASE_PATH}/har
ENV LOG_PATH=${DATA_BASE_PATH}/log
ENV ARTIFACT_STORAGE_PATH=${DATA_BASE_PATH}/artifacts

ENV SKYVERN_MCP_ENABLED=true
# Porta interna do contêiner para o MCP
ENV MCP_PORT=9090

# Expor as portas que a aplicação usa
# API principal
EXPOSE 8000
# MCP
EXPOSE 9090
# Porta para VNC (calculada como 5900 + display_num (99) = 5999 no entrypoint)
EXPOSE 5999

COPY ./entrypoint-mcp.sh /app/entrypoint-mcp.sh
RUN chmod +x /app/entrypoint-mcp.sh

CMD [ "/bin/bash", "/app/entrypoint-mcp.sh" ]
