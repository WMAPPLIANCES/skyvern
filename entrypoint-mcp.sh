#!/bin/bash
set -e

echo "Aguardando um pouco para a rede e DB (se externo)..."
sleep 10 # Pode ajudar com problemas de timing na inicialização

echo "Executando migrações do banco de dados Skyvern..."
# --- SUBSTITUA A LINHA ABAIXO PELO COMANDO CORRETO ---
# Exemplo 1: Se usar alembic diretamente e estiver no PATH ou via poetry
poetry run alembic upgrade head
# Exemplo 2: Se alembic estiver instalado globalmente no contêiner
# alembic upgrade head
# Exemplo 3: Se o Skyvern tiver um comando de gerenciamento
# poetry run python -m skyvern db upgrade
# --- FIM DA SUBSTITUIÇÃO ---
echo "Migrações do banco de dados (tentativa) concluídas."

echo "Iniciando o servidor Skyvern..."
# Seu Dockerfile já define MCP_PORT=9090 e o servidor principal na 8000
# O comando abaixo inicia o servidor principal na porta definida por --port (ou padrão 8000)
# e o MCP se SKYVERN_MCP_ENABLED=true na porta definida por MCP_PORT (ou padrão 9090)
# Se você quer que o servidor principal rode na 9090 como nos logs de inicialização,
# você precisaria ajustar o comando ou as variáveis de ambiente.
# No entanto, seu docker-compose original expõe 8000 para a API principal.
# Vamos assumir que o comando padrão do Skyvern lida com as portas corretamente
# com base nas variáveis de ambiente.
python -m skyvern run server --port 8000 & # Garante que o servidor principal rode na 8000

echo "Aguardando inicialização do servidor Skyvern..."
# Aumentar o sleep pode ajudar se o servidor demorar para iniciar antes do MCP
sleep 15

echo "Iniciando o MCP..."
# O MCP usará a variável de ambiente MCP_PORT (que você definiu como 9090)
python -m skyvern run mcp
