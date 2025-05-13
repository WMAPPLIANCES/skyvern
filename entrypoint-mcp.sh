#!/bin/bash
set -e

echo "Iniciando o servidor Skyvern..."

# Iniciar o servidor Skyvern em background
python -m skyvern run server &

# Aguardar o servidor iniciar
sleep 10

# Iniciar o MCP (sem usar a opção --port)
echo "Iniciando o MCP..."
exec python -m skyvern run mcp
