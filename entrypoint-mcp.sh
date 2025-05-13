#!/bin/bash

echo "Iniciando a API principal na porta 8000..."
# Inicia a API em background
uvicorn skyvern.main:app --host 0.0.0.0 --port 8000 &
API_PID=$! # Capture PID of background process

# Aguarda um pouco para a API iniciar (opcional, mas pode ajudar)
sleep 5
echo "API (supostamente) iniciada."

# Verifica se o MCP deve ser iniciado
if [ "$SKYVERN_MCP_ENABLED" = "true" ]; then
  echo "Iniciando o MCP na porta $MCP_PORT..."
  # Tenta iniciar o MCP em foreground - REMOVIDO --host
  # Assumindo que a variável MCP_PORT é lida automaticamente ou que --port é válido
  python -m skyvern run mcp --port ${MCP_PORT:-9090}
  # OU, se --port também não for válido e ele ler MCP_PORT do ambiente:
  # python -m skyvern run mcp

  # --- Adicione tratamento de erro (opcional mas recomendado) ---
  MCP_EXIT_CODE=$?
  if [ $MCP_EXIT_CODE -ne 0 ]; then
      echo "Falha ao iniciar o MCP (código de saída: $MCP_EXIT_CODE)."
      # Você pode querer parar a API também se o MCP falhar
      # kill $API_PID
      exit $MCP_EXIT_CODE # Sair do script com o erro do MCP
  fi
  # -------------------------------------------------------------
else
  echo "MCP desabilitado. Aguardando processo da API..."
  # Se só a API rodar, precisamos esperar o processo em background
  wait $API_PID
fi

echo "Script finalizado." # Não deve chegar aqui se o MCP rodar em foreground com sucesso
