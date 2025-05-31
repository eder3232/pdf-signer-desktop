import pytest
from app.core.pdf_handler import PDFHandler
import os
import tempfile

@pytest.fixture
def sample_pdf():
    """Crea un PDF de prueba temporal"""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as f:
        f.write(b"%PDF-1.7\n")  # PDF mínimo válido
        temp_path = f.name
    yield temp_path
    os.remove(temp_path)

def test_pdf_handler_initialization(sample_pdf):
    # Prueba de archivo existente
    handler = PDFHandler(sample_pdf)
    assert handler.pdf_path == sample_pdf
    
    # Prueba de archivo no existente
    with pytest.raises(FileNotFoundError):
        PDFHandler("archivo_no_existente.pdf")

def test_get_number_of_pages(sample_pdf):
    handler = PDFHandler(sample_pdf)
    assert handler.get_number_of_pages() >= 1

def test_get_page_dimensions(sample_pdf):
    handler = PDFHandler(sample_pdf)
    width, height = handler.get_page_dimensions(0)
    assert width > 0
    assert height > 0
    
    with pytest.raises(ValueError):
        handler.get_page_dimensions(999)  # Página inválida

def test_extract_page(sample_pdf):
    handler = PDFHandler(sample_pdf)
    extracted = handler.extract_page(0)
    assert len(extracted.pages) == 1 