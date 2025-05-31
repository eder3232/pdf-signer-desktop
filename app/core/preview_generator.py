from PIL import Image
from PyPDF2 import PdfReader
from typing import Tuple, List, Dict, Any
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from PIL.ImageQt import ImageQt
import fitz
import os

class PreviewGenerator:
    def __init__(self, dpi: int = 300):
        """
        Inicializa el generador de vistas previas
        
        Args:
            dpi (int): Resolución de la vista previa en DPI
        """
        self.dpi = dpi
        self._scale_factor = dpi / 72.0  # 72 puntos = 1 pulgada

    @staticmethod
    def generate_page_preview(pdf_path: str, page_number: int | None) -> Image:
        """Genera una vista previa de una página del PDF"""
        try:
            # Validar parámetros
            if not pdf_path or not os.path.exists(pdf_path):
                raise ValueError("Ruta de PDF inválida")
            if page_number is None:
                raise ValueError("Número de página no especificado")
            
            # Abrir documento
            doc = fitz.open(pdf_path)
            if not (0 <= page_number < len(doc)):
                raise ValueError(f"Número de página inválido: {page_number}")
            
            # Obtener página
            page = doc[page_number]
            
            # Generar imagen
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img_data = pix.tobytes("png")
            
            # Convertir a imagen PIL
            return Image.open(io.BytesIO(img_data))
            
        except Exception as e:
            print(f"Error generando vista previa: {str(e)}")
            # Retornar una imagen en blanco como fallback
            return Image.new('RGB', (595, 842), 'white')  # Tamaño A4
        finally:
            if 'doc' in locals():
                doc.close()

    def _overlay_signature(self, preview: Image.Image, signature: Dict) -> None:
        """Superpone una firma en la vista previa"""
        try:
            # Obtener imagen de firma
            sig_image = Image.open(signature["image_path"])
            
            # Calcular posición y tamaño
            pos_x = int(signature["position"].x * self._scale_factor)
            pos_y = int(signature["position"].y * self._scale_factor)
            width = int(signature["size"].width * self._scale_factor)
            height = int(signature["size"].height * self._scale_factor)
            
            # Redimensionar firma
            sig_image = sig_image.resize((width, height), Image.Resampling.LANCZOS)
            
            # Rotar si es necesario
            if "rotation" in signature:
                sig_image = sig_image.rotate(
                    signature["rotation"],
                    expand=True,
                    resample=Image.Resampling.BICUBIC
                )
            
            # Crear máscara si es necesario
            mask = None
            if sig_image.mode == 'RGBA':
                mask = sig_image.split()[3]
            
            # Pegar firma
            preview.paste(sig_image, (pos_x, pos_y), mask)
            
        except Exception as e:
            print(f"Error al superponer firma: {e}")

    def generate_thumbnail(
        self,
        preview: Image.Image,
        max_size: Tuple[int, int] = (200, 200)
    ) -> Image.Image:
        """
        Genera una miniatura de la vista previa
        
        Args:
            preview: Imagen de vista previa
            max_size: Tamaño máximo de la miniatura (ancho, alto)
            
        Returns:
            Image.Image: Miniatura generada
        """
        preview_copy = preview.copy()
        preview_copy.thumbnail(max_size, Image.Resampling.LANCZOS)
        return preview_copy 