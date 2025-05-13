#!/bin/bash
set -e

echo "Aguardando um pouco para a rede e DB (se externo)..."
sleep 10

echo "Executando migrações do banco de dados Skyvern..."
# --- TENTATIVA DE CORREÇÃO PARA CHAMAR ALEMBIC ---
# Chamar alembic diretamente como um módulo python
python -m alembic upgrade head
# --- FIM DA TENTATIVA DE CORREÇÃO ---
echo "Migrações do banco de dados (tentativa) concluídas."

echo "Iniciando o servidor Skyvern..."
python -m skyvern run server --port 8000 &

echo "Aguardando inicialização do servidor Skyvern..."
sleep 15

echo "Iniciando o MCP..."
python -m skyvern run mcp
