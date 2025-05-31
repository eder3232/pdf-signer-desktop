from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional
from .signature_model import SignatureModel
import os

class PageDimensions(BaseModel):
    width: float = Field(..., gt=0, description="Ancho de la página en puntos PDF")
    height: float = Field(..., gt=0, description="Alto de la página en puntos PDF")

class DocumentModel(BaseModel):
    pdf_path: str = Field(..., description="Ruta al archivo PDF")
    total_pages: int = Field(..., gt=0, description="Número total de páginas")
    page_dimensions: Dict[int, PageDimensions] = Field(
        ...,
        description="Dimensiones de cada página indexadas por número de página"
    )
    signatures: List[SignatureModel] = Field(
        default_factory=list,
        description="Lista de firmas a insertar"
    )
    
    @validator('pdf_path')
    def validate_pdf_path(cls, v):
        if not os.path.exists(v):
            raise ValueError(f"El archivo PDF no existe: {v}")
        if not v.lower().endswith('.pdf'):
            raise ValueError("El archivo debe ser un PDF")
        return v

    def add_signature(self, signature: SignatureModel) -> None:
        """Añade una firma al documento"""
        if signature.page_number >= self.total_pages:
            raise ValueError(f"Número de página inválido: {signature.page_number}")
        self.signatures.append(signature)

    class Config:
        arbitrary_types_allowed = True 