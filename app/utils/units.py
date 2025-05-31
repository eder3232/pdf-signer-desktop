from typing import Tuple, Union
import math

class PDFUnits:
    # Constantes de conversión
    CM_TO_POINTS = 28.3465  # 1 cm = 28.3465 puntos
    POINTS_TO_CM = 1 / CM_TO_POINTS
    
    @staticmethod
    def cm_to_points(cm: Union[float, Tuple[float, float]]) -> Union[float, Tuple[float, float]]:
        """
        Convierte centímetros a puntos PDF
        
        Args:
            cm: Valor en centímetros (número o tupla de números)
            
        Returns:
            Valor convertido a puntos PDF
        """
        if isinstance(cm, tuple):
            return (cm[0] * PDFUnits.CM_TO_POINTS, cm[1] * PDFUnits.CM_TO_POINTS)
        return cm * PDFUnits.CM_TO_POINTS
    
    @staticmethod
    def points_to_cm(points: Union[float, Tuple[float, float]]) -> Union[float, Tuple[float, float]]:
        """
        Convierte puntos PDF a centímetros
        
        Args:
            points: Valor en puntos (número o tupla de números)
            
        Returns:
            Valor convertido a centímetros
        """
        if isinstance(points, tuple):
            return (points[0] * PDFUnits.POINTS_TO_CM, points[1] * PDFUnits.POINTS_TO_CM)
        return points * PDFUnits.POINTS_TO_CM

    @staticmethod
    def rotate_coordinates(
        x: float,
        y: float,
        angle: float,
        origin: Tuple[float, float] = (0, 0)
    ) -> Tuple[float, float]:
        """
        Rota un punto alrededor de un origen
        
        Args:
            x: Coordenada X
            y: Coordenada Y
            angle: Ángulo en grados
            origin: Punto de origen para la rotación
            
        Returns:
            Tuple[float, float]: Nuevas coordenadas (x, y)
        """
        angle_rad = math.radians(angle)
        ox, oy = origin
        
        # Trasladar al origen
        translated_x = x - ox
        translated_y = y - oy
        
        # Rotar
        rotated_x = translated_x * math.cos(angle_rad) - translated_y * math.sin(angle_rad)
        rotated_y = translated_x * math.sin(angle_rad) + translated_y * math.cos(angle_rad)
        
        # Trasladar de vuelta
        return (rotated_x + ox, rotated_y + oy) 