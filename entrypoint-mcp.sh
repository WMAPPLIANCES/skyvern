#!/bin/bash
set -e

echo "Porta MCP: $MCP_PORT"
echo "SKYVERN_MCP_ENABLED: $SKYVERN_MCP_ENABLED"

echo "Iniciando a API principal na porta 8000..."
python -m skyvern run server &
API_PID=$!

echo "Aguardando o servidor iniciar..."
sleep 10

# Verificar se o servidor está rodando
if ps -p $API_PID > /dev/null
then
   echo "Servidor iniciado com sucesso na porta 8000"
else
   echo "Falha ao iniciar o servidor!"
   exit 1
fi

echo "Opções disponíveis para o MCP:"
python -m skyvern run mcp --help

echo "Iniciando o MCP..."
# Remova a opção --port, use apenas a variável de ambiente
exec python -m skyvern run mcp
