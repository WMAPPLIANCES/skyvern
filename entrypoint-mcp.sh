#!/bin/bash
set -e # Sair imediatamente se um comando falhar

echo "ENTRYPOINT: Aguardando um pouco para a rede e DB (se externo)..."
sleep 10 # Pode ajudar com problemas de timing na inicialização, especialmente para DBs externos

echo "ENTRYPOINT: Executando migrações do banco de dados Skyvern..."
# Tentar executar alembic como um módulo Python.
# Isso assume que 'alembic' está instalado no ambiente Python
# e que o arquivo alembic.ini está no diretório raiz do projeto (ou onde o Alembic espera encontrá-lo).
# O diretório de trabalho padrão para o CMD/ENTRYPOINT é o WORKDIR definido no Dockerfile (/app).
# Certifique-se que seu alembic.ini e os scripts de migração estão em /app ou em um subdiretório
# que o alembic consiga encontrar (geralmente o alembic.ini está na raiz do projeto).
python -m alembic upgrade head
echo "ENTRYPOINT: Migrações do banco de dados (tentativa) concluídas."

echo "ENTRYPOINT: Iniciando o servidor Skyvern (API Principal)..."
# Inicia o servidor principal na porta 8000 em background
python -m skyvern run server --port 8000 &
SERVER_PID=$! # Captura o PID do servidor em background

echo "ENTRYPOINT: Servidor Skyvern (API Principal) iniciado com PID $SERVER_PID. Aguardando inicialização..."
sleep 15 # Dê tempo para o servidor principal iniciar completamente

echo "ENTRYPOINT: Iniciando o MCP (Media Capture Processor)..."
# O MCP usará a variável de ambiente MCP_PORT (que você definiu como 9090 no Easypanel)
python -m skyvern run mcp &
MCP_PID=$! # Captura o PID do MCP em background

echo "ENTRYPOINT: MCP iniciado com PID $MCP_PID."
echo "ENTRYPOINT: Ambos os servidores estão rodando. O entrypoint aguardará os processos."

# Aguardar que qualquer um dos processos (servidor ou MCP) termine
# Isso mantém o contêiner rodando enquanto os processos em background estão ativos.
# Se um deles falhar, o 'set -e' fará o script sair, e o contêiner parará.
wait -n $SERVER_PID $MCP_PID

# Se chegarmos aqui, significa que um dos processos terminou.
# Podemos adicionar um tratamento de saída se necessário.
EXIT_CODE=$?
echo "ENTRYPOINT: Um dos processos (Servidor ou MCP) terminou com código de saída $EXIT_CODE. Encerrando..."
exit $EXIT_CODE
