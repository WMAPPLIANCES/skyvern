from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

def setup_cors(app: FastAPI):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["https://ui.skyvern.wmappliances.cloud", "http://localhost:3000", "http://localhost:5173"], # Adicione as portas que você usa localmente
        allow_credentials=True,
        allow_methods=["*"],  # Todos os métodos
        allow_headers=["*"],  # Todos os cabeçalhos
    )
    
    return app
