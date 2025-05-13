from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

def setup_cors(app: FastAPI):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Permitir todos os origens (para desenvolvimento)
        allow_credentials=True,
        allow_methods=["*"],  # Todos os métodos
        allow_headers=["*"],  # Todos os cabeçalhos
    )
    
    return app
