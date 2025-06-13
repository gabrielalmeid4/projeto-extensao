from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from ..services.gerador_cracha import GeradorCracha
from pathlib import Path
import shutil
import logging
import traceback

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

@router.post("/gerar-cracha")
async def gerar_cracha(
    nome: str = Form(...),
    instituicao: str = Form(...),
    matricula: str = Form(...),
    modalidade: str = Form(...),
    foto: UploadFile = File(...),
    logo: UploadFile = File(None)
):
    """
    Gera um crachá em PDF com os dados do aluno e sua foto.
    O logo da instituição é opcional.
    """
    logger.info(f"Iniciando geração de crachá para aluno: {nome} (Matrícula: {matricula})")
    logger.debug(f"Dados recebidos - Instituição: {instituicao}, Modalidade: {modalidade}")
    logger.debug(f"Arquivo de foto: {foto.filename} ({foto.content_type})")
    if logo:
        logger.debug(f"Logo da instituição: {logo.filename} ({logo.content_type})")
    
    try:
        # Salvar a foto temporariamente
        foto_path = Path("fotos_temp") / foto.filename
        logger.debug(f"Caminho temporário da foto: {foto_path}")
        
        foto_path.parent.mkdir(exist_ok=True)
        logger.debug("Diretório temporário criado/verificado")
        
        try:
            with foto_path.open("wb") as buffer:
                shutil.copyfileobj(foto.file, buffer)
            logger.debug("Foto salva temporariamente com sucesso")
        except Exception as e:
            logger.error(f"Erro ao salvar foto temporária: {str(e)}")
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"Erro ao salvar foto: {str(e)}")

        # Salvar o logo temporariamente se fornecido
        logo_path = None
        if logo:
            logo_path = Path("fotos_temp") / logo.filename
            logger.debug(f"Caminho temporário do logo: {logo_path}")
            
            try:
                with logo_path.open("wb") as buffer:
                    shutil.copyfileobj(logo.file, buffer)
                logger.debug("Logo salvo temporariamente com sucesso")
            except Exception as e:
                logger.error(f"Erro ao salvar logo temporário: {str(e)}")
                logger.error(traceback.format_exc())
                raise HTTPException(status_code=500, detail=f"Erro ao salvar logo: {str(e)}")
        
        # Criar dicionário com os dados do crachá
        cracha_data = {
            "nome": nome,
            "instituicao": instituicao,
            "matricula": matricula,
            "modalidade": modalidade,
            "foto_path": str(foto_path)
        }
        
        if logo_path:
            cracha_data["logo_path"] = str(logo_path)
            
        logger.debug("Dados do crachá preparados")
        
        try:
            # Gerar o crachá
            pdf_path = gerador.gerar_cracha(cracha_data)
            logger.info(f"Crachá gerado com sucesso: {pdf_path}")
        except Exception as e:
            logger.error(f"Erro ao gerar crachá: {str(e)}")
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"Erro ao gerar crachá: {str(e)}")
        
        try:
            # Limpar arquivos temporários
            foto_path.unlink()
            logger.debug("Arquivo de foto temporário removido")
            
            if logo_path and logo_path.exists():
                logo_path.unlink()
                logger.debug("Arquivo de logo temporário removido")
                
        except Exception as e:
            logger.warning(f"Erro ao remover arquivos temporários: {str(e)}")
        
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
    
    finally:
        # Garantir que os arquivos sejam fechados
        try:
            await foto.close()
            logger.debug("Arquivo de foto fechado")
            if logo:
                await logo.close()
                logger.debug("Arquivo de logo fechado")
        except Exception as e:
            logger.warning(f"Erro ao fechar arquivos: {str(e)}") 