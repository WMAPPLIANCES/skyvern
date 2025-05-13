#!/bin/bash
set -e

echo "Aguardando um pouco para a rede e DB (se externo)..."
sleep 10 # Pode ajudar com problemas de timing na inicialização

echo "Executando migrações do banco de dados Skyvern..."
# Substitua pelo comando de migração correto do Skyvern!
# Pode ser:
# poetry run alembic upgrade head
# ou
# python -m alembic upgrade head
# ou
# python -m skyvern db upgrade
# Verifique a documentação do Skyvern para o comando correto.
echo "Migrações do banco de dados (tentativa) concluídas."

echo "Iniciando o servidor Skyvern..."
python -m skyvern run server &

echo "Aguardando inicialização do servidor Skyvern..."
sleep 10 # Dê tempo para o servidor principal iniciar antes do MCP

echo "Iniciando o MCP..."
python -m skyvern run mcp
