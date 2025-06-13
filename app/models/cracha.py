from pydantic import BaseModel
from typing import Optional

class Cracha(BaseModel):
    nome: str
    campus: str
    matricula: str
    modalidade: str
    foto_path: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "nome": "João Silva",
                "campus": "Teresina Central",
                "matricula": "2023001234",
                "modalidade": "Futsal",
                "foto_path": "fotos/joao_silva.jpg"
            }
        } 