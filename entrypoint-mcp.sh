#!/bin/bash
set -e # Sair imediatamente se um comando falhar

echo "ENTRYPOINT: Aguardando um pouco para a rede e DB (se externo)..."
sleep 10

echo "ENTRYPOINT: Executando migrações do banco de dados Skyvern..."
python -m alembic upgrade head
echo "ENTRYPOINT: Migrações do banco de dados (tentativa) concluídas."

echo "ENTRYPOINT: Iniciando o servidor Skyvern (API Principal)..."
# --- REMOVA O ARGUMENTO --port 8000 ---
# O Skyvern deve usar a variável de ambiente PORT=8000
python -m skyvern run server &
SERVER_PID=$!

echo "ENTRYPOINT: Servidor Skyvern (API Principal) iniciado com PID $SERVER_PID. Aguardando inicialização..."
sleep 15 # Dê tempo para o servidor principal iniciar completamente

echo "ENTRYPOINT: Iniciando o MCP (Media Capture Processor)..."
# O MCP usará a variável de ambiente MCP_PORT (que você definiu como 9090 no Easypanel)
python -m skyvern run mcp &
MCP_PID=$!

echo "ENTRYPOINT: MCP iniciado com PID $MCP_PID."
echo "ENTRYPOINT: Ambos os servidores estão rodando. O entrypoint aguardará os processos."

wait -n $SERVER_PID $MCP_PID
EXIT_CODE=$?
echo "ENTRYPOINT: Um dos processos (Servidor ou MCP) terminou com código de saída $EXIT_CODE. Encerrando..."
exit $EXIT_CODE
