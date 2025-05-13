#!/bin/bash

# Para o script se qualquer comando falhar
set -e

echo "Iniciando a API principal na porta 8000..."
# Inicia a API em background e captura seu PID
uvicorn skyvern.main:app --host 0.0.0.0 --port 8000 &
API_PID=$!

# Pequena pausa para permitir que a API comece a iniciar (opcional)
sleep 3
echo "API principal (PID: $API_PID) iniciada em background."

# Verifica se o MCP deve ser iniciado
if [ "$SKYVERN_MCP_ENABLED" = "true" ]; then
  # Usa o valor de MCP_PORT, ou 9090 como padrão se não estiver definida
  MCP_TARGET_PORT=${MCP_PORT:-9090}
  echo "Iniciando o MCP na porta $MCP_TARGET_PORT..."

  # --- Comando CORRIGIDO para iniciar o MCP ---
  # Removida a opção inválida '--host'.
  # Mantida a opção '--port' (verifique se é válida para 'skyvern run mcp').
  python -m skyvern run mcp --port "$MCP_TARGET_PORT"

  # Captura o código de saída do comando MCP
  MCP_EXIT_CODE=$?
  if [ $MCP_EXIT_CODE -ne 0 ]; then
      echo "****************************************************"
      echo "ERRO: Falha ao iniciar o MCP (código de saída: $MCP_EXIT_CODE)."
      echo "Verifique se o comando 'python -m skyvern run mcp --port $MCP_TARGET_PORT' está correto"
      echo "e se a opção '--port' é suportada. Se não for, tente remover '--port' também."
      echo "****************************************************"
      # Opcional: parar a API se o MCP falhar
      # kill $API_PID
      exit $MCP_EXIT_CODE # Sai do script com o código de erro do MCP
  fi
  # Se o MCP iniciar e rodar em foreground, o script ficará aqui.

else
  echo "MCP desabilitado (SKYVERN_MCP_ENABLED não é 'true')."
  echo "Aguardando o processo da API principal (PID: $API_PID) terminar..."
  # Espera o processo da API em background terminar para manter o container vivo
  wait $API_PID
fi

echo "Script entrypoint finalizado."
