#!/bin/bash
set -e # Sair imediatamente se um comando falhar
echo "----------------------------------------------------"
echo "Skyvern UI Entrypoint: INICIADO"
echo "Variáveis de ambiente VITE disponíveis:"
env | grep VITE_ # Mostra todas as variáveis que começam com VITE_
echo "----------------------------------------------------"

echo "Skyvern UI Entrypoint: Diretório atual: $(pwd)"
echo "Skyvern UI Entrypoint: Listando arquivos em /app:"
ls -la /app
echo "----------------------------------------------------"

echo "Skyvern UI Entrypoint: Instalando dependências (npm install)..."
npm install --prefer-offline --no-audit --progress=false
echo "Skyvern UI Entrypoint: npm install CONCLUÍDO"
echo "----------------------------------------------------"

echo "Skyvern UI Entrypoint: Limpando build anterior (rm -rf dist)..."
rm -rf dist
echo "Skyvern UI Entrypoint: Limpeza CONCLUÍDA"
echo "----------------------------------------------------"

echo "Skyvern UI Entrypoint: Construindo aplicação frontend (npm run build)..."
npm run build
echo "Skyvern UI Entrypoint: npm run build CONCLUÍDO"
echo "----------------------------------------------------"

echo "Skyvern UI Entrypoint: Listando arquivos em /app/dist (após build):"
ls -la /app/dist || echo "Diretório /app/dist não encontrado"
echo "----------------------------------------------------"

echo "Skyvern UI Entrypoint: Iniciando servidor de preview (npm run preview)..."
npm run preview -- --host 0.0.0.0 --port 80

echo "Skyvern UI Entrypoint: Script teoricamente finalizado (mas preview deve manter rodando)"
echo "----------------------------------------------------"
