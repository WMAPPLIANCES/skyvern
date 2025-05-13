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
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="/app:${PYTHONPATH}"

COPY --from=requirements-stage /tmp/requirements.txt /app/requirements.txt

RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir --upgrade -r /app/requirements.txt && \
    pip install alembic

RUN playwright install-deps && \
    playwright install chromium

# --- INÍCIO DAS MODIFICAÇÕES PARA XVFB e VNC ---
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
    # Servidor VNC - x11vnc é uma boa opção para compartilhar um display X existente
    x11vnc \
    # Opcional: um gerenciador de janelas leve se o x11vnc precisar ou para melhor visualização
    # fluxbox \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*
# --- FIM DAS MODIFICAÇÕES PARA XVFB e VNC ---

# ... (Instalação do Node.js e Bitwarden CLI - se você ainda os usa) ...
# ... (COPY ., ENV DATA_BASE_PATH, etc.) ...

# Expor a porta do VNC (além das portas da aplicação)
# A porta padrão do VNC é 5900. Se o display for :0, x11vnc pode usar 5900.
# Se o display for :99, x11vnc pode usar 5999 (5900 + número do display).
# Vamos expor uma faixa ou uma porta específica que configuraremos.
EXPOSE 8000 # API principal
EXPOSE 9090 # MCP
EXPOSE 5900 # Porta padrão para VNC (pode precisar ser ajustada)

COPY ./entrypoint-mcp.sh /app/entrypoint-mcp.sh
RUN chmod +x /app/entrypoint-mcp.sh

CMD [ "/bin/bash", "/app/entrypoint-mcp.sh" ]
