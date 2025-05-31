import pytest
from app.models.signature_model import SignatureModel, SignaturePosition, SignatureSize
from app.models.document_model import DocumentModel, PageDimensions
from app.models.config_model import ApplicationConfig
from PIL import Image
import tempfile
import os

@pytest.fixture
def sample_signature_image():
    """Crea una imagen temporal de firma"""
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        image = Image.new('RGBA', (100, 50), (255, 255, 255, 0))
        image.save(f.name)
        temp_path = f.name
    yield temp_path
    os.remove(temp_path)

def test_signature_model(sample_signature_image):
    # Crear modelo válido
    signature = SignatureModel(
        image_path=sample_signature_image,
        position=SignaturePosition(x=100, y=100),
        size=SignatureSize(width=200, height=100),
        rotation=45,
        page_number=0
    )
    assert signature.rotation == 45
    
    # Probar validaciones
    with pytest.raises(ValueError):
        SignatureModel(
            image_path="archivo_no_existente.png",
            position=SignaturePosition(x=100, y=100),
            size=SignatureSize(width=200, height=100)
        )

def test_document_model(sample_signature_image):
    # Crear PDF temporal
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        temp_pdf = f.name
    
    try:
        # Crear modelo de documento
        doc = DocumentModel(
            pdf_path=temp_pdf,
            total_pages=1,
            page_dimensions={0: PageDimensions(width=595, height=842)}
        )
        
        # Añadir firma
        signature = SignatureModel(
            image_path=sample_signature_image,
            position=SignaturePosition(x=100, y=100),
            size=SignatureSize(width=200, height=100),
            page_number=0
        )
        doc.add_signature(signature)
        
        assert len(doc.signatures) == 1
        
    finally:
        os.remove(temp_pdf)

def test_config_model():
    config = ApplicationConfig()
    
    # Probar valores por defecto
    assert config.auto_save == True
    assert config.preview_quality == "high"
    assert config.preview_dpi == 300
    
    # Probar actualización de valores
    config.preview_quality = "low"
    assert config.preview_dpi == 72 