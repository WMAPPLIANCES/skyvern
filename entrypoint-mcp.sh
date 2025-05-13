#!/bin/bash
set -e

# Exibir as variáveis de ambiente (para depuração)
echo "Porta MCP: $MCP_PORT"
echo "SKYVERN_MCP_ENABLED: $SKYVERN_MCP_ENABLED"

# Iniciar o servidor Skyvern em background
python -m skyvern run server &
SERVER_PID=$!

# Aguardar o servidor iniciar
echo "Aguardando o servidor iniciar..."
sleep 10

# Verificar se o servidor está rodando
if ps -p $SERVER_PID > /dev/null
then
   echo "Servidor iniciado com sucesso na porta 8000"
else
   echo "Falha ao iniciar o servidor!"
   exit 1
fi

# Mostrar ajuda do MCP para ver as opções disponíveis
echo "Opções disponíveis para o MCP:"
python -m skyvern run mcp --help

# Iniciar o MCP sem opções adicionais
echo "Iniciando o MCP..."
exec python -m skyvern run mcp
