from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, ClassVar
from .signature_model import SignatureModel
import os
from enum import Enum
from .signature_mode_config import SignatureMode, SignatureModeConfig

class PageDimensions(BaseModel):
    width: float = Field(..., gt=0, description="Ancho de la página en puntos PDF")
    height: float = Field(..., gt=0, description="Alto de la página en puntos PDF")

class SignatureMode(Enum):
    LIBRE = "libre"          # Modo actual: página por página
    MASIVO = "masivo"        # Primera hoja define todas excepto última
    PLANTILLA = "plantilla"  # Patrón definido (cada N páginas)
    SELECTIVO = "selectivo"  # Una configuración para páginas seleccionadas

class SignatureModeConfig:
    def __init__(self, mode: SignatureMode):
        self.mode = mode
        self.affected_pages: List[int] = []  # Páginas que serán firmadas
        self.excluded_pages: List[int] = []  # Páginas excluidas
        self.pattern_interval: int = 1       # Para modo plantilla
        self.template_page: int = 0          # Página de referencia

    def validate_for_document(self, total_pages: int) -> bool:
        """Valida si el modo es aplicable al documento actual"""
        if total_pages < 1:
            return False
            
        return {
            SignatureMode.LIBRE: self._validate_libre,
            SignatureMode.MASIVO: self._validate_masivo,
            SignatureMode.PLANTILLA: self._validate_plantilla,
            SignatureMode.SELECTIVO: self._validate_selectivo
        }[self.mode](total_pages)

    def _validate_libre(self, total_pages: int) -> bool:
        return True  # Siempre válido

    def _validate_masivo(self, total_pages: int) -> bool:
        return total_pages >= 2  # Mínimo 2 páginas

    def _validate_plantilla(self, total_pages: int) -> bool:
        return total_pages >= self.pattern_interval

    def _validate_selectivo(self, total_pages: int) -> bool:
        return all(page < total_pages for page in self.affected_pages)

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
    
    # Constantes de conversión con anotación de tipo
    POINTS_PER_CM: ClassVar[float] = 28.3465  # 1 cm = 28.3465 puntos PDF
    
    signature_mode: SignatureModeConfig = Field(
        default_factory=lambda: SignatureModeConfig(SignatureMode.LIBRE),
        description="Modo de inserción de firmas"
    )
    
    @validator('pdf_path')
    def validate_pdf_path(cls, v):
        if not os.path.exists(v):
            raise ValueError(f"El archivo PDF no existe: {v}")
        if not v.lower().endswith('.pdf'):
            raise ValueError("El archivo debe ser un PDF")
        return v

    @staticmethod
    def points_to_cm(points: float) -> float:
        return points / DocumentModel.POINTS_PER_CM
    
    @staticmethod
    def cm_to_points(cm: float) -> float:
        return cm * DocumentModel.POINTS_PER_CM

    def add_signature(self, signature: SignatureModel) -> None:
        """Añade una firma al documento"""
        if signature.page_number >= self.total_pages:
            raise ValueError(f"Número de página inválido: {signature.page_number}")
        
        print(f"\n=== Añadiendo firma en modo {self.signature_mode.mode.value} ===")
        print(f"Página inicial: {signature.page_number + 1}")
        print(f"Total de páginas en documento: {self.total_pages}")
        
        # En modo masivo, replicar la firma en todas las páginas excepto la última
        if self.signature_mode.mode == SignatureMode.MASIVO:
            print("\n=== DEBUG MODO MASIVO ===")
            print(f"Página de firma actual: {signature.page_number + 1}")
            
            if signature.page_number == 0:  # Si es la primera página
                print("Detectada firma en primera página - Replicando...")
                print(f"Replicando firma en {self.total_pages - 1} páginas")
                
                # Limpiar firmas existentes en modo masivo
                self.signatures = []
                print("Firmas existentes limpiadas")
                
                # Crear copias para todas las páginas excepto la última
                for page in range(self.total_pages - 1):
                    new_sig = SignatureModel(
                        image_path=signature.image_path,
                        position=SignaturePosition(
                            x=signature.position.x,
                            y=signature.position.y
                        ),
                        size=SignatureSize(
                            width=signature.size.width,
                            height=signature.size.height
                        ),
                        page_number=page
                    )
                    print(f"Creada firma para página {page + 1}")
                    self.signatures.append(new_sig)
                
                print(f"Total de firmas creadas: {len(self.signatures)}")
                
            elif signature.page_number == self.total_pages - 1:
                print("\nAñadiendo firma específica para última página")
                self.signatures.append(signature)
            
            print(f"\nEstado final de firmas:")
            print(f"Total de firmas en documento: {len(self.signatures)}")
            for idx, sig in enumerate(self.signatures):
                print(f"Firma #{idx + 1}: Página {sig.page_number + 1}")
        else:
            print("Añadiendo firma en modo normal")
            self.signatures.append(signature)

    def get_pages_to_sign(self) -> List[int]:
        """Retorna lista de páginas que serán firmadas según el modo"""
        try:
            if not self.signature_mode.validate_for_document(self.total_pages):
                print("Modo de firma no válido para este documento")
                return []
            
            if self.signature_mode.mode == SignatureMode.LIBRE:
                return list(range(self.total_pages))
            
            elif self.signature_mode.mode == SignatureMode.MASIVO:
                # Todas excepto la última
                return list(range(self.total_pages - 1))
            
            elif self.signature_mode.mode == SignatureMode.PLANTILLA:
                # Cada N páginas
                return list(range(0, self.total_pages, 
                                self.signature_mode.pattern_interval))
            
            elif self.signature_mode.mode == SignatureMode.SELECTIVO:
                # Solo páginas seleccionadas
                return [p for p in self.signature_mode.affected_pages 
                       if p not in self.signature_mode.excluded_pages]
                   
            return []  # Por defecto, lista vacía
        except Exception as e:
            print(f"Error en get_pages_to_sign: {e}")
            return []

    class Config:
        arbitrary_types_allowed = True 