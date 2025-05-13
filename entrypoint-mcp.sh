#!/bin/bash
set -e

echo "Iniciando o servidor Skyvern..."
python -m skyvern run server &

echo "Aguardando inicialização..."
sleep 10

echo "Iniciando o MCP..."
python -m skyvern run mcp
