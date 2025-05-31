from PIL import Image
from PyPDF2 import PdfReader, PdfWriter
from typing import Tuple, Optional
import os
import math

class SignatureManager:
    def __init__(self):
        """Inicializa el gestor de firmas"""
        self.signature_cache = {}  # Cache para imágenes de firma

    def load_signature(self, image_path: str) -> Image.Image:
        """
        Carga una imagen de firma y la convierte a RGBA
        
        Args:
            image_path (str): Ruta a la imagen PNG de la firma
            
        Returns:
            Image.Image: Imagen de firma en formato RGBA
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"No se encontró la imagen: {image_path}")
            
        if image_path not in self.signature_cache:
            image = Image.open(image_path)
            if image.format != 'PNG':
                raise ValueError("La imagen debe estar en formato PNG")
            
            # Convertir a RGBA si no lo está
            if image.mode != 'RGBA':
                image = image.convert('RGBA')
                
            self.signature_cache[image_path] = image
            
        return self.signature_cache[image_path]

    def prepare_signature(
        self,
        image: Image.Image,
        size: Tuple[float, float],
        rotation: float = 0
    ) -> Image.Image:
        """
        Prepara una imagen de firma con el tamaño y rotación especificados
        
        Args:
            image (Image.Image): Imagen original de la firma
            size (Tuple[float, float]): (ancho, alto) en puntos
            rotation (float): Ángulo de rotación en grados
            
        Returns:
            Image.Image: Imagen procesada
        """
        # Redimensionar
        resized_image = image.resize((int(size[0]), int(size[1])), Image.Resampling.LANCZOS)
        
        # Rotar si es necesario
        if rotation != 0:
            resized_image = resized_image.rotate(
                rotation,
                expand=True,
                resample=Image.Resampling.BICUBIC
            )
            
        return resized_image

    def insert_signature(
        self,
        pdf_page: PdfReader,
        signature_image: Image.Image,
        position: Tuple[float, float],
        size: Tuple[float, float],
        rotation: float = 0
    ) -> PdfWriter:
        """
        Inserta una firma en una página PDF
        
        Args:
            pdf_page (PdfReader): Página PDF donde insertar la firma
            signature_image (Image.Image): Imagen de la firma
            position (Tuple[float, float]): (x, y) en puntos desde esquina inferior izquierda
            size (Tuple[float, float]): (ancho, alto) en puntos
            rotation (float): Ángulo de rotación en grados
            
        Returns:
            PdfWriter: Nueva página PDF con la firma insertada
        """
        # Preparar la firma
        prepared_signature = self.prepare_signature(signature_image, size, rotation)
        
        # TODO: Implementar la inserción real de la firma en el PDF
        # Esta parte requerirá usar PyPDF2 para sobreponer la imagen
        # Se completará en la siguiente iteración
        
        writer = PdfWriter()
        writer.add_page(pdf_page.pages[0])
        return writer 