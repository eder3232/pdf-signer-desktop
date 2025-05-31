import pytest
from app.core.preview_generator import PreviewGenerator
from PIL import Image
from PyPDF2 import PdfReader
import io
import os

@pytest.fixture
def sample_pdf():
    """Crea un PDF de prueba"""
    from reportlab.pdfgen import canvas
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer)
    c.drawString(100, 750, "Test PDF")
    c.save()
    buffer.seek(0)
    return PdfReader(buffer)

@pytest.fixture
def sample_signature():
    """Crea una imagen de firma de prueba"""
    img = Image.new('RGBA', (100, 50), (255, 255, 255, 0))
    return img

def test_preview_generation(sample_pdf):
    generator = PreviewGenerator(dpi=150)  # DPI más bajo para pruebas
    preview = generator.generate_page_preview(sample_pdf)
    
    assert isinstance(preview, Image.Image)
    assert preview.mode == "RGB"
    assert preview.size[0] > 0
    assert preview.size[1] > 0

def test_signature_overlay(sample_pdf, sample_signature):
    generator = PreviewGenerator(dpi=150)
    
    signatures = [{
        "image": sample_signature,
        "position": (100, 100),
        "size": (200, 100),
        "rotation": 0
    }]
    
    preview = generator.generate_page_preview(sample_pdf, signatures)
    assert isinstance(preview, Image.Image)

def test_thumbnail_generation(sample_pdf):
    generator = PreviewGenerator()
    preview = generator.generate_page_preview(sample_pdf)
    
    max_size = (200, 200)
    thumbnail = generator.generate_thumbnail(preview, max_size)
    
    assert thumbnail.size[0] <= max_size[0]
    assert thumbnail.size[1] <= max_size[1]

def test_different_dpis():
    generator_low = PreviewGenerator(dpi=72)
    generator_high = PreviewGenerator(dpi=300)
    
    assert generator_low._scale_factor == 1.0
    assert generator_high._scale_factor == pytest.approx(4.167, rel=1e-3) 