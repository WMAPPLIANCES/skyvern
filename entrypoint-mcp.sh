#!/bin/bash
set -e

echo "ENTRYPOINT: Aguardando um pouco para a rede e DB (se externo)..."
sleep 10

echo "ENTRYPOINT: Executando migrações do banco de dados Skyvern..."
python -m alembic upgrade head
echo "ENTRYPOINT: Migrações do banco de dados (tentativa) concluídas."

# --- INÍCIO DAS CONFIGURAÇÕES PARA XVFB e VNC ---
XVFB_DISPLAY_NUM=99 # Usar um número de display alto para evitar conflitos
XVFB_DISPLAY=":${XVFB_DISPLAY_NUM}"
SCREEN_RESOLUTION="1280x1024x24" # Largura x Altura x Profundidade de Cor
VNC_PORT=$((5900 + XVFB_DISPLAY_NUM)) # Calcula a porta VNC baseada no número do display

echo "ENTRYPOINT: Iniciando Xvfb no display $XVFB_DISPLAY com resolução $SCREEN_RESOLUTION"
# -nolisten tcp desabilita conexões TCP diretas ao Xserver, o VNC cuidará do acesso.
# -ac desabilita o controle de acesso ao X server.
Xvfb $XVFB_DISPLAY -screen 0 $SCREEN_RESOLUTION -nolisten tcp -ac &
XVFB_PID=$!
export DISPLAY=$XVFB_DISPLAY # Exportar a variável DISPLAY para os processos filhos
sleep 3 # Dar um tempo para o Xvfb iniciar completamente
echo "ENTRYPOINT: Xvfb iniciado com PID $XVFB_PID no display $DISPLAY."

echo "ENTRYPOINT: Iniciando servidor VNC (x11vnc) na porta $VNC_PORT para o display $DISPLAY"
# -forever: mantém o x11vnc rodando mesmo após o primeiro cliente desconectar.
# -usepw: (Opcional, mas recomendado) usa um arquivo de senha. Você precisaria criar este arquivo.
#         Para um teste rápido sem senha (INSEGURO): remova -usepw ou use -nopw (verifique man x11vnc)
#         Se usar -usepw, você precisa criar um arquivo de senha com 'x11vnc -storepasswd SUA_SENHA_VNC /caminho/para/vnc_password_file'
#         e depois montar esse arquivo no contêiner ou criá-lo no Dockerfile.
#         Para simplificar este exemplo, vamos rodar sem senha (INSEGURO PARA AMBIENTES NÃO CONFIÁVEIS).
# -shared: Permite múltiplas conexões VNC (opcional).
# -rfbport $VNC_PORT: Define a porta para o VNC.
x11vnc -display $DISPLAY -forever -nopw -rfbport $VNC_PORT &
VNC_PID=$!
sleep 2 # Dar um tempo para o VNC iniciar
echo "ENTRYPOINT: Servidor VNC x11vnc iniciado com PID $VNC_PID na porta $VNC_PORT."
# --- FIM DAS CONFIGURAÇÕES PARA XVFB e VNC ---


echo "ENTRYPOINT: Iniciando o servidor Skyvern (API Principal)..."
# O DISPLAY já está exportado, então o Playwright headful deve usá-lo.
python -m skyvern run server & # Skyvern usará a variável de ambiente PORT (ex: 8000)
SERVER_PID=$!

echo "ENTRYPOINT: Servidor Skyvern (API Principal) iniciado com PID $SERVER_PID. Aguardando inicialização..."
sleep 15

echo "ENTRYPOINT: Iniciando o MCP (Media Capture Processor)..."
python -m skyvern run mcp & # MCP usará a variável de ambiente MCP_PORT (ex: 9090)
MCP_PID=$!

echo "ENTRYPOINT: MCP iniciado com PID $MCP_PID."
echo "ENTRYPOINT: Todos os servidores estão rodando. O entrypoint aguardará os processos."

cleanup() {
    echo "ENTRYPOINT: Recebido sinal de encerramento. Parando processos..."
    # Parar VNC, Servidor, MCP, Xvfb na ordem inversa ou como apropriado
    # O kill pode precisar ser mais gracioso para alguns processos
    if ps -p $VNC_PID > /dev/null; then kill $VNC_PID; fi
    if ps -p $MCP_PID > /dev/null; then kill $MCP_PID; fi
    if ps -p $SERVER_PID > /dev/null; then kill $SERVER_PID; fi
    if ps -p $XVFB_PID > /dev/null; then kill $XVFB_PID; fi
    wait $VNC_PID $MCP_PID $SERVER_PID $XVFB_PID 2>/dev/null
    echo "ENTRYPOINT: Processos parados."
}
trap cleanup EXIT INT TERM

wait -n $SERVER_PID $MCP_PID
EXIT_CODE=$?
echo "ENTRYPOINT: Um dos processos principais (Servidor ou MCP) terminou com código de saída $EXIT_CODE. Encerrando..."
# O trap EXIT chamará cleanup()
exit $EXIT_CODE
