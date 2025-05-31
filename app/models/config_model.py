from pydantic import BaseModel, Field
from typing import Dict, Optional
from .signature_model import SignatureSize

class ApplicationConfig(BaseModel):
    last_directory: str = Field(
        default="",
        description="Último directorio utilizado"
    )
    default_signature_size: SignatureSize = Field(
        default=SignatureSize(width=100, height=50),
        description="Tamaño predeterminado para nuevas firmas"
    )
    preview_quality: str = Field(
        default="high",
        description="Calidad de vista previa (low/medium/high)"
    )
    auto_save: bool = Field(
        default=True,
        description="Guardar cambios automáticamente"
    )
    recent_files: Dict[str, str] = Field(
        default_factory=dict,
        description="Archivos recientes (nombre: ruta)"
    )
    
    @property
    def preview_dpi(self) -> int:
        """Retorna el DPI según la calidad configurada"""
        dpi_map = {
            "low": 72,
            "medium": 150,
            "high": 300
        }
        return dpi_map.get(self.preview_quality, 150)

    class Config:
        use_enum_values = True 