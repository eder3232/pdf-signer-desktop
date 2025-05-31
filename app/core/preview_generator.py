from PIL import Image
from PyPDF2 import PdfReader
from typing import Tuple, List, Dict, Any
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from PIL.ImageQt import ImageQt

class PreviewGenerator:
    def __init__(self, dpi: int = 300):
        """
        Inicializa el generador de vistas previas
        
        Args:
            dpi (int): Resolución de la vista previa en DPI
        """
        self.dpi = dpi
        self._scale_factor = dpi / 72.0  # 72 puntos = 1 pulgada

    def generate_page_preview(
        self,
        pdf_reader: PdfReader,
        page_number: int = 0,
        signatures: List[Dict[str, Any]] = None
    ) -> Image.Image:
        """Genera vista previa de página PDF con firmas"""
        # Crear un PDF temporal con el contenido
        output = io.BytesIO()
        c = canvas.Canvas(output)
        
        # Obtener dimensiones de la página
        page = pdf_reader.pages[page_number]
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)
        
        # Dibujar contenido
        c.setPageSize((width, height))
        c.drawString(100, height - 50, "Página {}".format(page_number + 1))
        c.grid([x * 100 for x in range(0, int(width), 100)],
               [y * 100 for y in range(0, int(height), 100)])
        c.save()
        
        # Convertir a imagen
        output.seek(0)
        preview = Image.new('RGB', 
                          (int(width * self._scale_factor), 
                           int(height * self._scale_factor)), 
                          'white')
        
        # Superponer firmas si existen
        if signatures:
            for sig in signatures:
                self._overlay_signature(preview, sig)
        
        return preview

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