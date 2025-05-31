from PyPDF2 import PdfReader, PdfWriter
from typing import Tuple, List
import os

class PDFHandler:
    def __init__(self, pdf_path: str):
        """
        Inicializa el manejador de PDF
        
        Args:
            pdf_path (str): Ruta al archivo PDF
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"No se encontró el archivo: {pdf_path}")
            
        self.pdf_path = pdf_path
        self.reader = PdfReader(pdf_path)
        
    def get_number_of_pages(self) -> int:
        """Retorna el número total de páginas del PDF"""
        return len(self.reader.pages)
        
    def get_page_dimensions(self, page_number: int) -> Tuple[float, float]:
        """
        Obtiene las dimensiones de una página específica
        
        Args:
            page_number (int): Número de página (comenzando desde 0)
            
        Returns:
            Tuple[float, float]: (ancho, alto) en puntos
        """
        if page_number >= len(self.reader.pages):
            raise ValueError(f"Número de página inválido: {page_number}")
            
        page = self.reader.pages[page_number]
        return (float(page.mediabox.width), float(page.mediabox.height))

    def extract_page(self, page_number: int) -> PdfReader:
        """
        Extrae una página específica como un nuevo PdfReader
        
        Args:
            page_number (int): Número de página a extraer (comenzando desde 0)
            
        Returns:
            PdfReader: Nuevo PdfReader conteniendo solo la página extraída
        """
        if page_number >= len(self.reader.pages):
            raise ValueError(f"Número de página inválido: {page_number}")
            
        writer = PdfWriter()
        writer.add_page(self.reader.pages[page_number])
        
        # Crear archivo temporal
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            writer.write(temp_file)
            temp_path = temp_file.name
            
        return PdfReader(temp_path) 