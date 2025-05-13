#!/bin/bash
set -e # Sair imediatamente se um comando falhar

echo "Iniciando a UI do Skyvern..."

# Mude para o diretório da aplicação se não estiver lá (geralmente /app)
# cd /app

echo "Instalando dependências (se necessário)..."
# Se você não copiou node_modules no seu Dockerfile da UI, este passo é vital.
# Considere adicionar --prefer-offline se as dependências já estiverem cacheadas
# para acelerar, mas remova se estiver tendo problemas de dependência.
npm install

echo "Limpando build anterior (se existir)..."
rm -rf dist

echo "Construindo a aplicação frontend com as variáveis de ambiente atuais..."
# Este é o comando CRUCIAL que injeta VITE_SKYVERN_API_KEY no código
npm run build

echo "Iniciando o servidor de preview na porta 80..."
# O host 0.0.0.0 permite que seja acessível de fora do contêiner
npm run preview -- --host 0.0.0.0 --port 80
