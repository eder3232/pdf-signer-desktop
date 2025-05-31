from typing import Tuple, Dict, Any
from .units import PDFUnits

class PDFValidator:
    @staticmethod
    def validate_coordinates(
        x: float,
        y: float,
        page_size: Tuple[float, float]
    ) -> bool:
        """
        Valida si las coordenadas están dentro de los límites de la página
        
        Args:
            x: Coordenada X en puntos
            y: Coordenada Y en puntos
            page_size: (ancho, alto) de la página en puntos
            
        Returns:
            bool: True si las coordenadas son válidas
        """
        width, height = page_size
        return 0 <= x <= width and 0 <= y <= height

    @staticmethod
    def validate_signature_size(
        size: Tuple[float, float],
        page_size: Tuple[float, float],
        position: Tuple[float, float]
    ) -> bool:
        """
        Valida si el tamaño de la firma es válido para la posición dada
        
        Args:
            size: (ancho, alto) de la firma en puntos
            page_size: (ancho, alto) de la página en puntos
            position: (x, y) de la firma en puntos
            
        Returns:
            bool: True si el tamaño es válido
        """
        sig_width, sig_height = size
        page_width, page_height = page_size
        x, y = position
        
        # Verificar dimensiones positivas
        if sig_width <= 0 or sig_height <= 0:
            return False
            
        # Verificar que la firma no se salga de la página
        if x + sig_width > page_width or y + sig_height > page_height:
            return False
            
        return True

    @staticmethod
    def validate_signature_config(config: Dict[str, Any]) -> bool:
        """
        Valida la estructura de configuración de una firma
        
        Args:
            config: Diccionario de configuración de firma
            
        Returns:
            bool: True si la configuración es válida
        """
        required_keys = {'position', 'size', 'rotation'}
        if not all(key in config for key in required_keys):
            return False
            
        # Validar tipos de datos
        try:
            position = config['position']
            size = config['size']
            rotation = float(config['rotation'])
            
            if not isinstance(position, dict) or not isinstance(size, dict):
                return False
                
            if not all(key in position for key in ['x', 'y']):
                return False
                
            if not all(key in size for key in ['width', 'height']):
                return False
                
            # Validar rangos
            if not (-360 <= rotation <= 360):
                return False
                
            return True
            
        except (ValueError, TypeError):
            return False 