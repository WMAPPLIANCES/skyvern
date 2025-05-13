#!/bin/bash
set -e

echo "Aguardando um pouco para a rede e DB (se externo)..."
sleep 10

echo "Executando migrações do banco de dados Skyvern..."
# --- TENTATIVA DE CORREÇÃO PARA 'poetry: command not found' ---
# Chamar poetry através do módulo python
python -m poetry run alembic upgrade head
# Se o comando acima ainda falhar, e você souber que alembic está instalado
# e configurado para ser chamado diretamente, você poderia tentar:
# python -m alembic upgrade head
# ou apenas
# alembic upgrade head (se estiver no PATH)
# Mas 'python -m poetry run alembic upgrade head' é geralmente mais robusto
# se alembic é gerenciado como uma dependência do poetry.
# --- FIM DA TENTATIVA DE CORREÇÃO ---
echo "Migrações do banco de dados (tentativa) concluídas."

echo "Iniciando o servidor Skyvern..."
python -m skyvern run server --port 8000 &

echo "Aguardando inicialização do servidor Skyvern..."
sleep 15

echo "Iniciando o MCP..."
python -m skyvern run mcp
