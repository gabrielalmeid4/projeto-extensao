from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from ..services.gerador_cracha import GeradorCracha
from pathlib import Path
import shutil
import logging
import traceback
import os

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
router = APIRouter()
gerador = GeradorCracha()

async def _cleanup_file(path: Path):
    if path.exists():
        try:
            os.unlink(path)
            logger.debug(f"Arquivo temporário removido em background: {path}")
        except Exception as e:
            logger.warning(f"Erro ao remover arquivo temporário em background {path}: {str(e)}")

@router.post("/gerar-cracha")
async def gerar_cracha(
    background_tasks: BackgroundTasks,
    nome: str = Form(...),
    instituicao: str = Form(...),
    rg: str = Form(...),
    matricula: str = Form(...),
    modalidade: str = Form(...),
    foto: UploadFile = File(...)
):
    """
    Gera um crachá em PDF com os dados do aluno e sua foto, utilizando uma imagem base fixa.
    """
    logger.info(f"Iniciando geração de crachá para aluno: {nome} (Matrícula: {matricula})")
    logger.debug(f"Dados recebidos - Instituição: {instituicao}, RG: {rg}, Modalidade: {modalidade}")
    logger.debug(f"Arquivo de foto: {foto.filename} ({foto.content_type})")
    
    # Lista para manter controle dos arquivos temporários que serão limpos em background
    temp_upload_files = [] 

    try:
        # Salvar a foto temporariamente
        foto_path = Path("fotos_temp") / foto.filename
        logger.debug(f"Caminho temporário da foto: {foto_path}")
        foto_path.parent.mkdir(exist_ok=True)
        temp_upload_files.append(foto_path)

        try:
            with foto_path.open("wb") as buffer:
                shutil.copyfileobj(foto.file, buffer)
            logger.debug("Foto salva temporariamente com sucesso")
        except Exception as e:
            logger.error(f"Erro ao salvar foto temporária: {str(e)}")
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"Erro ao salvar foto: {str(e)}")

        # Definir o caminho fixo para a imagem base do crachá
        base_image_path = Path("cracha_base") / "cracha_base.jpeg"
        if not base_image_path.exists():
            logger.error(f"Imagem base do crachá não encontrada: {base_image_path}")
            raise HTTPException(status_code=500, detail=f"Erro: Imagem base do crachá não encontrada em {base_image_path}")
        logger.debug(f"Utilizando imagem base do crachá: {base_image_path}")
        
        # Criar dicionário com os dados do crachá
        cracha_data = {
            "nome": nome,
            "instituicao": instituicao,
            "rg": rg,
            "matricula": matricula,
            "modalidade": modalidade,
            "foto_path": str(foto_path),
            "base_image_path": str(base_image_path) # Sempre incluir a imagem base
        }
        
        logger.debug("Dados do crachá preparados")
        
        try:
            # Gerar o crachá
            pdf_path = gerador.gerar_cracha(cracha_data)
            logger.info(f"Crachá gerado com sucesso: {pdf_path}")
        except Exception as e:
            logger.error(f"Erro ao gerar crachá: {str(e)}")
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"Erro ao gerar crachá: {str(e)}")
        
        # Adicionar tarefa em background para limpar os arquivos temporários
        for temp_file_path in temp_upload_files:
            background_tasks.add_task(_cleanup_file, temp_file_path)
        
        # Adicionar tarefa em background para fechar os arquivos de upload
        background_tasks.add_task(foto.close)

        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename=f"cracha_{matricula}.pdf"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro inesperado: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Erro interno do servidor: {str(e)}") 