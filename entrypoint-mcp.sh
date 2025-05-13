#!/bin/bash
set -e

# Iniciar o servidor Skyvern em background
python -m skyvern run server &

# Aguardar alguns segundos para garantir que o servidor esteja funcionando
sleep 5

# Iniciar o MCP em foreground (sem a opção --port)
# A porta é controlada pela variável de ambiente MCP_PORT
exec python -m skyvern run mcp
