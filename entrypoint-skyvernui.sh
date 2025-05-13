#!/bin/bash
set -e

echo "Skyvern UI Entrypoint: Iniciando..."

# Navegar para o diretório da aplicação se necessário (geralmente /app)
# cd /app

echo "Skyvern UI Entrypoint: Instalando dependências (npm install)..."
npm install --prefer-offline --no-audit --progress=false

echo "Skyvern UI Entrypoint: Limpando build anterior (rm -rf dist)..."
rm -rf dist

echo "Skyvern UI Entrypoint: Construindo aplicação frontend (npm run build)..."
# Este comando usa as variáveis VITE_* definidas no Easypanel
npm run build

echo "Skyvern UI Entrypoint: Iniciando servidor de preview (npm run preview)..."
npm run preview -- --host 0.0.0.0 --port 80

echo "Skyvern UI Entrypoint: Finalizado."
