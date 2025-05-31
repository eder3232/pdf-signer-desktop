from enum import Enum
from typing import List

class SignatureMode(Enum):
    LIBRE = "libre"
    MASIVO = "masivo"
    PLANTILLA = "plantilla"
    SELECTIVO = "selectivo"

class SignatureModeConfig:
    def __init__(self, mode: SignatureMode):
        self.mode = mode
        self.affected_pages: List[int] = []
        self.excluded_pages: List[int] = []
        self.pattern_interval: int = 1
        self.template_page: int = 0

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