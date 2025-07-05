from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, inch
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

    def _processar_imagem(self, image_path: str, target_width_cm: float, target_height_cm: float) -> Image.Image:
        """Processa a imagem, redimensionando-a para as dimensões alvo em cm."""
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
                
                # Redimensionar mantendo a proporção para as dimensões alvo em pixels
                dpi = 300 # Exemplo de DPI, pode ser ajustado ou lido da imagem se disponível
                target_width_px = int(target_width_cm * dpi / 2.54)
                target_height_px = int(target_height_cm * dpi / 2.54)

                # Calcula a nova dimensão mantendo a proporção
                img.thumbnail((target_width_px, target_height_px), Image.Resampling.LANCZOS)
                
                logger.debug(f"Imagem redimensionada para: {img.size}")
                
                # Carregar a imagem completamente na memória para liberar o arquivo
                img.load()
                logger.debug("Imagem carregada completamente na memória")

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
            erro = "Formato de imagem da foto não suportado"
            logger.error(erro)
            raise ValueError(erro)

        # Validar imagem base se fornecida
        if 'base_image_path' in cracha_data and cracha_data['base_image_path'] and not self._validar_formato_imagem(cracha_data['base_image_path']):
            erro = "Formato da imagem base não suportado"
            logger.error(erro)
            raise ValueError(erro)

        # Nome do arquivo baseado na matrícula
        pdf_path = self.output_dir / f"cracha_{cracha_data['matricula']}.pdf"
        logger.debug(f"Caminho do PDF: {pdf_path}")
        
        temp_files_to_clean = [] # Para limpar arquivos temporários criados nesta função
        temp_img_path = None
        temp_base_image_path = None

        try:
            # Carregar a imagem base
            base_img_pil = Image.open(cracha_data['base_image_path'])
            # Definir o tamanho do canvas do PDF com base na imagem base
            pdf_width = base_img_pil.width
            pdf_height = base_img_pil.height
            logger.debug(f"Usando imagem base. Dimensões do PDF: {pdf_width}x{pdf_height} pontos.")
            
            # Salvar imagem base temporariamente para o ReportLab
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_base:
                temp_base_image_path = temp_base.name
                base_img_pil.save(temp_base_image_path, format='PNG')
                logger.debug(f"Imagem base salva temporariamente: {temp_base_image_path}")
            temp_files_to_clean.append(Path(temp_base_image_path))

            c = canvas.Canvas(str(pdf_path), pagesize=(pdf_width, pdf_height))
            c.drawImage(temp_base_image_path, 0, 0, width=pdf_width, height=pdf_height, preserveAspectRatio=False)
            logger.debug("Imagem base desenhada como fundo do PDF")
            
            # Coordenadas estimadas para a imagem base (pixels da imagem ~ pontos do PDF)
            # CAMPUS (Instituição): ~30px from left, ~220px from bottom
            # NOME: ~30px from left, ~190px from bottom
            # RG: ~30px from left, ~160px from bottom
            # MATRÍCULA: ~30px from left, ~130px from bottom
            # MODALIDADE: ~30px from left, ~100px from bottom
            # FOTO: ~220px from left, ~250px from bottom, ~150x200px

            # Ajustes finos podem ser necessários.
            # Textos
            font_size = 30
            c.setFont("Helvetica-Bold", font_size)

            # Função para centralizar texto
            def get_centered_x(text, canvas_width):
                text_width = c.stringWidth(text, "Helvetica-Bold", font_size)
                return (canvas_width - text_width) / 2

            # CONFIGURAÇÕES DE POSICIONAMENTO VERTICAL - AJUSTE ESTES VALORES CONFORME NECESSÁRIO
            # Coordenadas Y base (em pontos) - quanto maior o valor, mais alto no crachá
            y_base = 380  # Posição inicial (mais alta)
            
            # Espaçamento entre linhas (em pontos) - quanto maior, mais separado
            espacamento_linhas = 73  # Espaçamento entre cada linha de texto
            
            # Ordem do template: CAMPUS, NOME, RG, MATRÍCULA, MODALIDADE
            # Coordenadas y são do bottom-left

            # CAMPUS (Instituição)
            y_instituicao = y_base
            x_instituicao = get_centered_x(cracha_data['instituicao'], pdf_width)
            c.drawString(x_instituicao, y_instituicao, f"{cracha_data['instituicao']}")

            # NOME
            y_nome = y_instituicao - espacamento_linhas
            x_nome = get_centered_x(cracha_data['nome'], pdf_width)
            c.drawString(x_nome, y_nome, f"{cracha_data['nome']}")

            # RG
            y_rg = y_nome - espacamento_linhas
            x_rg = get_centered_x(cracha_data['rg'], pdf_width)
            c.drawString(x_rg, y_rg, f"{cracha_data['rg']}")

            # MATRÍCULA
            y_matricula = y_rg - espacamento_linhas
            x_matricula = get_centered_x(cracha_data['matricula'], pdf_width)
            c.drawString(x_matricula, y_matricula, f"{cracha_data['matricula']}")

            # MODALIDADE
            y_modalidade = y_matricula - espacamento_linhas
            x_modalidade = get_centered_x(cracha_data['modalidade'], pdf_width)
            c.drawString(x_modalidade, y_modalidade, f"{cracha_data['modalidade']}")
            logger.debug("Textos sobrepostos na imagem base")

            # Foto do Aluno
            # Definir o centro da área da foto no crachá base
            # Essas coordenadas foram estimadas com base no layout atual do crachá.
            # Se a imagem base mudar significativamente, esses valores podem precisar de ajuste.
            CRITICAL_PHOTO_CENTER_X = 208.5 + (170 / 2) # Centro X original
            CRITICAL_PHOTO_CENTER_Y = 570 + (210 / 2)  # Centro Y original

            # Dimensões da foto em pontos (ajuste estas para mudar o tamanho da foto)
            # Ao ajustar photo_width/photo_height, a imagem tentará manter-se centralizada
            # em torno de CRITICAL_PHOTO_CENTER_X e CRITICAL_PHOTO_CENTER_Y.
            photo_width = 300 # pontos   (~3cm)
            photo_height = 210 # pontos (~4cm)

            # Calcular as coordenadas X e Y para que a foto fique centralizada
            photo_x = CRITICAL_PHOTO_CENTER_X - (photo_width / 2)
            photo_y = CRITICAL_PHOTO_CENTER_Y - (photo_height / 2)

            img_aluno = self._processar_imagem(cracha_data['foto_path'], photo_width/cm, photo_height/cm)
            
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_img_file:
                temp_img_path = temp_img_file.name
                img_aluno.save(temp_img_path, format='JPEG', quality=95)
                logger.debug(f"Foto do aluno processada e salva temporariamente: {temp_img_path}")
            temp_files_to_clean.append(Path(temp_img_path))

            c.drawImage(temp_img_path, photo_x, photo_y, 
                       width=photo_width, height=photo_height, preserveAspectRatio=True)
            logger.debug("Foto do aluno adicionada na imagem base")

            c.showPage()
            c.save()
            logger.debug("PDF salvo")
            return str(pdf_path)
        
        except Exception as e:
            logger.error(f"Erro na geração do crachá: {str(e)}")
            logger.error(traceback.format_exc())
            raise
        finally:
            # Limpar arquivos temporários
            for p in temp_files_to_clean:
                if p.exists():
                    try:
                        os.unlink(p)
                        logger.debug(f"Arquivo temporário limpo: {p}")
                    except Exception as e:
                        logger.warning(f"Não foi possível remover o arquivo temporário {p}: {str(e)}") 
