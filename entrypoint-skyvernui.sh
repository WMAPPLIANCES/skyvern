#!/bin/bash
set -e

echo "Iniciando a UI do Skyvern..."

# Primeiro instale as dependências se necessário
# npm install

# Para ambiente de produção
npm run build
npm run preview -- --host 0.0.0.0 --port 80
