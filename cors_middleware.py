from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

def setup_cors(app: FastAPI):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["https://ui.skyvern.wmappliances.cloud"],
        allow_credentials=True,
        allow_methods=["*"],  # Todos os métodos
        allow_headers=["*"],  # Todos os cabeçalhos
    )
    
    return app
