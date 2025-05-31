import pytest
from PySide6.QtWidgets import QApplication
from app.ui.canvas_view import CanvasView, SignatureItem, PDFScene
from app.models.document_model import DocumentModel
from app.models.signature_model import SignatureModel, SignaturePosition, SignatureSize
import tempfile
import os
from PIL import Image

# Necesario para pruebas de Qt
@pytest.fixture(scope="session")
def qapp():
    app = QApplication([])
    yield app
    app.quit()

@pytest.fixture
def sample_pdf():
    """Crea un PDF de prueba"""
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        # Crear PDF mínimo válido
        f.write(b"%PDF-1.7\n")
        temp_path = f.name
    yield temp_path
    os.remove(temp_path)

@pytest.fixture
def sample_signature():
    """Crea una imagen de firma de prueba"""
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        image = Image.new('RGBA', (100, 50), (255, 255, 255, 0))
        image.save(f.name)
        temp_path = f.name
    yield temp_path
    os.remove(temp_path)

def test_canvas_view_initialization(qapp):
    view = CanvasView()
    assert view.current_page == 0
    assert view.document is None
    assert isinstance(view.scene, PDFScene)

def test_load_document(qapp, sample_pdf):
    view = CanvasView()
    document = DocumentModel(
        pdf_path=sample_pdf,
        total_pages=1,
        page_dimensions={0: {"width": 595, "height": 842}}
    )
    view.load_document(document)
    assert view.document == document
    assert view.page_selector.count() == 1

def test_signature_item_creation(qapp, sample_signature):
    from PySide6.QtGui import QPixmap
    pixmap = QPixmap(100, 50)
    item = SignatureItem(pixmap, 0)
    assert item.signature_index == 0
    assert item.flags() & item.GraphicsItemFlag.ItemIsMovable
    assert item.flags() & item.GraphicsItemFlag.ItemIsSelectable 