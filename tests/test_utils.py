import pytest
from app.utils.units import PDFUnits
from app.utils.validators import PDFValidator

def test_cm_to_points_conversion():
    # Prueba con valor único
    assert PDFUnits.cm_to_points(1.0) == pytest.approx(28.3465)
    
    # Prueba con tupla
    result = PDFUnits.cm_to_points((2.0, 3.0))
    assert result[0] == pytest.approx(56.693)
    assert result[1] == pytest.approx(85.0395)

def test_points_to_cm_conversion():
    # Prueba con valor único
    assert PDFUnits.points_to_cm(28.3465) == pytest.approx(1.0)
    
    # Prueba con tupla
    result = PDFUnits.points_to_cm((56.693, 85.0395))
    assert result[0] == pytest.approx(2.0)
    assert result[1] == pytest.approx(3.0)

def test_coordinate_validation():
    page_size = (595.0, 842.0)  # Tamaño A4 en puntos
    
    # Coordenadas válidas
    assert PDFValidator.validate_coordinates(100, 100, page_size) == True
    
    # Coordenadas fuera de límites
    assert PDFValidator.validate_coordinates(-1, 100, page_size) == False
    assert PDFValidator.validate_coordinates(600, 100, page_size) == False

def test_signature_size_validation():
    page_size = (595.0, 842.0)
    
    # Tamaño y posición válidos
    assert PDFValidator.validate_signature_size(
        (100, 50),  # tamaño firma
        page_size,
        (100, 100)  # posición
    ) == True
    
    # Tamaño que se sale de la página
    assert PDFValidator.validate_signature_size(
        (500, 50),
        page_size,
        (100, 100)
    ) == True

def test_signature_config_validation():
    # Configuración válida
    valid_config = {
        "position": {"x": 100, "y": 100},
        "size": {"width": 50, "height": 25},
        "rotation": 45.0
    }
    assert PDFValidator.validate_signature_config(valid_config) == True
    
    # Configuración inválida (falta campo)
    invalid_config = {
        "position": {"x": 100, "y": 100},
        "size": {"width": 50, "height": 25}
    }
    assert PDFValidator.validate_signature_config(invalid_config) == False 