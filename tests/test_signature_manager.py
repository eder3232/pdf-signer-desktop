import pytest
from app.core.signature_manager import SignatureManager
from PIL import Image
import tempfile
import os

@pytest.fixture
def sample_signature():
    """Crea una imagen PNG de prueba"""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as f:
        # Crear una imagen simple de 100x100 píxeles
        image = Image.new('RGBA', (100, 100), (255, 255, 255, 0))
        image.save(f.name, 'PNG')
        temp_path = f.name
    yield temp_path
    os.remove(temp_path)

def test_load_signature(sample_signature):
    manager = SignatureManager()
    
    # Prueba carga exitosa
    image = manager.load_signature(sample_signature)
    assert isinstance(image, Image.Image)
    assert image.mode == 'RGBA'
    
    # Prueba archivo no existente
    with pytest.raises(FileNotFoundError):
        manager.load_signature("firma_no_existente.png")

def test_prepare_signature(sample_signature):
    manager = SignatureManager()
    original = manager.load_signature(sample_signature)
    
    # Prueba redimensionamiento
    size = (200, 200)
    resized = manager.prepare_signature(original, size)
    assert resized.size == size
    
    # Prueba rotación
    rotation = 45
    rotated = manager.prepare_signature(original, size, rotation)
    assert rotated.size[0] >= size[0]  # La rotación puede aumentar el tamaño

def test_signature_cache(sample_signature):
    manager = SignatureManager()
    
    # Primera carga
    image1 = manager.load_signature(sample_signature)
    
    # Segunda carga (debería usar caché)
    image2 = manager.load_signature(sample_signature)
    
    assert image1 is image2  # Debería ser el mismo objeto en memoria 