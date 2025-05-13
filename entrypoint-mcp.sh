#!/bin/bash

echo "Iniciando a API principal na porta 8000..."
# Inicia a API em background
uvicorn skyvern.main:app --host 0.0.0.0 --port 8000 &

# Aguarda um pouco para a API iniciar (opcional, pode não ser necessário)
sleep 5
echo "API (supostamente) iniciada."

# Verifica se o MCP deve ser iniciado
if [ "$SKYVERN_MCP_ENABLED" = "true" ]; then
  echo "Iniciando o MCP na porta $MCP_PORT..."
  # Inicia o MCP em foreground (mantém o container vivo)
  # Garanta que --host 0.0.0.0 está presente!
  python -m skyvern run mcp --host 0.0.0.0 --port ${MCP_PORT:-9090}
else
  echo "MCP desabilitado. Aguardando processo da API..."
  # Se só a API rodar, precisamos esperar o processo em background
  wait $!
fi

echo "Script finalizado." # Não deve chegar aqui se o MCP rodar em foreground
