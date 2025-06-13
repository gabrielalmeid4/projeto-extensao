from fastapi import FastAPI
from .api.routes import router

def create_app() -> FastAPI:
    app = FastAPI(
        title="Sistema de Crachás IFPI",
        description="API para geração de crachás para alunos esportistas do IFPI",
        version="1.0.0"
    )
    
    app.include_router(router, prefix="/api")
    
    return app 