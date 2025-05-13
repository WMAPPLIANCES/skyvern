#!/bin/bash
set -e # Sair imediatamente se um comando falhar

echo "Iniciando a UI do Skyvern..."

# Navegar para o diretório da aplicação (já deve estar em /app)
# cd /app

echo "Instalando dependências (se o node_modules não estiver completo)..."
# Se o COPY ./skyvern-frontend /app já inclui node_modules, você pode otimizar isso.
# Caso contrário, npm install é necessário.
npm install --prefer-offline --no-audit --progress=false

echo "Limpando build anterior (se existir)..."
rm -rf dist

echo "Construindo a aplicação frontend..."
# As variáveis de ambiente VITE_* fornecidas pelo Easypanel estarão disponíveis aqui
# e o Vite as incorporará no build.
npm run build

echo "Iniciando o servidor de preview na porta 80..."
# O comando preview usa a porta 80, que está exposta no Dockerfile
npm run preview -- --host 0.0.0.0 --port 80
