from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from PIL import Image
from pathlib import Path
import io
from typing import Dict, Any
import logging
import traceback
import os
import tempfile

logger = logging.getLogger(__name__)

class GeradorCracha:
    def __init__(self):
        self.output_dir = Path("crachas_gerados")
        self.output_dir.mkdir(exist_ok=True)
        logger.debug(f"Diretório de saída criado/verificado: {self.output_dir}")
        
        # Formatos de imagem suportados pelo Pillow
        self.supported_formats = {
            'JPEG': ['.jpg', '.jpeg', '.jfif', '.pjpeg', '.pjp'],
            'PNG': ['.png'],
            'GIF': ['.gif'],
            'BMP': ['.bmp'],
            'WebP': ['.webp'],
            'TIFF': ['.tiff', '.tif'],
            'ICO': ['.ico']
        }
        logger.debug(f"Formatos de imagem suportados: {list(self.supported_formats.keys())}")

    def _validar_formato_imagem(self, file_path: str) -> bool:
        """Valida se o formato da imagem é suportado."""
        logger.debug(f"Validando formato da imagem: {file_path}")
        try:
            with Image.open(file_path) as img:
                formato = img.format
                logger.debug(f"Formato da imagem detectado: {formato}")
                valido = formato in self.supported_formats
                if not valido:
                    logger.warning(f"Formato de imagem não suportado: {formato}")
                return valido
        except Exception as e:
            logger.error(f"Erro ao validar formato da imagem: {str(e)}")
            logger.error(traceback.format_exc())
            return False

    def _processar_imagem(self, image_path: str) -> Image.Image:
        """Processa a imagem para garantir compatibilidade com o PDF."""
        logger.debug(f"Iniciando processamento da imagem: {image_path}")
        try:
            with Image.open(image_path) as img:
                logger.debug(f"Imagem original - Modo: {img.mode}, Tamanho: {img.size}")
                
                # Converter para RGB se necessário
                if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                    logger.debug("Convertendo imagem com transparência para RGB")
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                elif img.mode != 'RGB':
                    logger.debug(f"Convertendo imagem do modo {img.mode} para RGB")
                    img = img.convert('RGB')
                
                # Redimensionar mantendo a proporção
                target_width = int(3 * cm)
                target_height = int(4 * cm)
                logger.debug(f"Dimensões alvo: {target_width}x{target_height}")
                
                # Calcular nova dimensão mantendo proporção
                ratio = min(target_width/img.width, target_height/img.height)
                new_size = (int(img.width * ratio), int(img.height * ratio))
                logger.debug(f"Nova dimensão calculada: {new_size}")
                
                # Redimensionar
                img = img.resize(new_size, Image.Resampling.LANCZOS)
                logger.debug(f"Imagem redimensionada para: {img.size}")
                
                return img
        except Exception as e:
            logger.error(f"Erro ao processar imagem: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    def gerar_cracha(self, cracha_data: Dict[str, Any]) -> str:
        """
        Gera um crachá em PDF com os dados do aluno esportista.
        Retorna o caminho do arquivo PDF gerado.
        """
        logger.info(f"Iniciando geração de crachá para {cracha_data['nome']}")
        
        if not self._validar_formato_imagem(cracha_data['foto_path']):
            erro = "Formato de imagem não suportado"
            logger.error(erro)
            raise ValueError(erro)

        # Validar logo se fornecido
        if 'logo_path' in cracha_data and not self._validar_formato_imagem(cracha_data['logo_path']):
            erro = "Formato do logo não suportado"
            logger.error(erro)
            raise ValueError(erro)

        # Nome do arquivo baseado na matrícula
        pdf_path = self.output_dir / f"cracha_{cracha_data['matricula']}.pdf"
        logger.debug(f"Caminho do PDF: {pdf_path}")
        
        temp_img_path = None
        temp_logo_path = None
        try:
            # Criar o PDF
            c = canvas.Canvas(str(pdf_path), pagesize=A4)
            width, height = A4
            logger.debug(f"Dimensões do PDF: {width}x{height}")

            # Adicionar logo se fornecido
            if 'logo_path' in cracha_data and Path(cracha_data['logo_path']).exists():
                logger.debug("Processando logo para o PDF")
                try:
                    # Processar logo
                    with Image.open(cracha_data['logo_path']) as logo_img:
                        # Redimensionar logo para um tamanho pequeno (1.5cm x 1.5cm)
                        target_size = (int(1.5 * cm), int(1.5 * cm))
                        logo_img.thumbnail(target_size, Image.Resampling.LANCZOS)
                        
                        # Salvar logo temporariamente
                        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_logo:
                            temp_logo_path = temp_logo.name
                            logo_img.save(temp_logo_path, format='PNG')
                            logger.debug("Logo processado e salvo temporariamente")
                        
                        # Adicionar logo ao PDF (canto superior direito)
                        c.drawImage(temp_logo_path, width - 3*cm, height - 2*cm, 
                                  width=1.5*cm, height=1.5*cm, preserveAspectRatio=True)
                        logger.debug("Logo adicionado ao PDF")
                except Exception as e:
                    logger.error(f"Erro ao processar logo: {str(e)}")
                    logger.error(traceback.format_exc())
                    # Continuar sem o logo em caso de erro

            # Configurar fonte e tamanho
            c.setFont("Helvetica-Bold", 14)
            logger.debug("Fonte configurada")

            # Adicionar informações do lado esquerdo
            c.drawString(2*cm, height - 4*cm, f"Nome: {cracha_data['nome']}")
            c.drawString(2*cm, height - 5*cm, f"Instituição: {cracha_data['instituicao']}")
            c.drawString(2*cm, height - 6*cm, f"Matrícula: {cracha_data['matricula']}")
            c.drawString(2*cm, height - 7*cm, f"Modalidade: {cracha_data['modalidade']}")
            logger.debug("Informações do crachá adicionadas")

            # Processar e adicionar foto do lado direito
            if cracha_data['foto_path'] and Path(cracha_data['foto_path']).exists():
                logger.debug("Processando foto para o PDF")
                img = self._processar_imagem(cracha_data['foto_path'])
                
                # Criar arquivo temporário para a imagem processada
                with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_img:
                    temp_img_path = temp_img.name
                    logger.debug(f"Arquivo temporário criado: {temp_img_path}")
                    
                    # Salvar imagem processada no arquivo temporário
                    img.save(temp_img_path, format='JPEG', quality=95)
                    logger.debug("Imagem processada salva no arquivo temporário")
                
                # Adicionar imagem ao PDF (fora do bloco with para garantir que o arquivo esteja fechado)
                c.drawImage(temp_img_path, width - 5*cm, height - 7*cm, 
                           width=3*cm, height=4*cm, preserveAspectRatio=True)
                logger.debug("Imagem adicionada ao PDF")

            # Salvar o PDF
            c.save()
            logger.debug("PDF salvo com sucesso")

            # Remover arquivos temporários
            if temp_img_path and os.path.exists(temp_img_path):
                try:
                    os.unlink(temp_img_path)
                    logger.debug("Arquivo de foto temporário removido")
                except Exception as e:
                    logger.warning(f"Não foi possível remover o arquivo de foto temporário: {str(e)}")

            if temp_logo_path and os.path.exists(temp_logo_path):
                try:
                    os.unlink(temp_logo_path)
                    logger.debug("Arquivo de logo temporário removido")
                except Exception as e:
                    logger.warning(f"Não foi possível remover o arquivo de logo temporário: {str(e)}")

            logger.info(f"PDF gerado com sucesso: {pdf_path}")
            return str(pdf_path)
            
        except Exception as e:
            # Tentar remover arquivos temporários em caso de erro
            for temp_path in [temp_img_path, temp_logo_path]:
                if temp_path and os.path.exists(temp_path):
                    try:
                        os.unlink(temp_path)
                        logger.debug(f"Arquivo temporário removido após erro: {temp_path}")
                    except Exception as cleanup_error:
                        logger.warning(f"Não foi possível remover o arquivo temporário após erro: {str(cleanup_error)}")
            
            logger.error(f"Erro ao gerar PDF: {str(e)}")
            logger.error(traceback.format_exc())
            raise 