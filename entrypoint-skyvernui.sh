#!/bin/bash
set -e

echo "Iniciando a UI do Skyvern..."

# Opcional: Remover node_modules e reinstalar para garantir um estado limpo
# rm -rf node_modules
# npm install --prefer-offline --no-audit --progress=false

# Se você não copia node_modules no Dockerfile, o npm install é crucial aqui
npm install

echo "Limpando build anterior (se existir)..."
rm -rf dist

echo "Construindo a aplicação frontend com as variáveis de ambiente..."
# Este comando é crucial para injetar VITE_SKYVERN_API_KEY
npm run build

echo "Iniciando o servidor de preview na porta 80..."
npm run preview -- --host 0.0.0.0 --port 80
