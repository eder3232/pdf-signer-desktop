from pydantic import BaseModel, Field, validator
from typing import Tuple, Optional
from PIL import Image
import os
from enum import Enum

# Añadir la clase SignatureMode
class SignatureMode(Enum):
    NORMAL = "normal"
    PLANTILLA = "plantilla"
    SELECTIVO = "selectivo"

class SignaturePosition(BaseModel):
    x: float = Field(..., description="Posición X en puntos PDF")
    y: float = Field(..., description="Posición Y en puntos PDF")
    
    @validator('x', 'y')
    def validate_coordinates(cls, v):
        if v < 0:
            raise ValueError("Las coordenadas deben ser positivas")
        return v

class SignatureSize(BaseModel):
    width: float = Field(..., gt=0, description="Ancho en puntos PDF")
    height: float = Field(..., gt=0, description="Alto en puntos PDF")

class SignatureModel:
    def __init__(self, image_path: str, position: SignaturePosition, size: SignatureSize, page_number: int):
        self.image_path = image_path
        self.position = position
        self.size = size
        self.page_number = page_number
        
        # Validar y ajustar tamaño inicial
        with Image.open(image_path) as img:
            aspect_ratio = img.height / img.width
            self.size.height = int(self.size.width * aspect_ratio)

    @validator('image_path')
    def validate_image_path(cls, v):
        if not os.path.exists(v):
            raise ValueError(f"El archivo de imagen no existe: {v}")
        try:
            Image.open(v)
        except:
            raise ValueError("El archivo no es una imagen válida")
        return v

    class Config:
        arbitrary_types_allowed = True 