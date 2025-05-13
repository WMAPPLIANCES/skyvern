#!/bin/bash
set -e

# Iniciar o servidor Skyvern em background
python -m skyvern run server &

# Aguardar alguns segundos para garantir que o servidor esteja funcionando
sleep 5

# Iniciar o MCP em foreground para que os logs apareçam
exec python -m skyvern run mcp
