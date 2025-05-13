#!/bin/bash
set -e

echo "Aguardando 15 segundos para a rede estabilizar..."
sleep 15

echo "Executando migrações do banco de dados..."
# SEU_COMANDO_DE_MIGRACAO_AQUI (ex: poetry run alembic upgrade head)
echo "Migrações do banco de dados concluídas."

echo "Iniciando o servidor Skyvern..."
# ... (resto do script) ...
