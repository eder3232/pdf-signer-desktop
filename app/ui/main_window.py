from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt
from ..models.document_model import DocumentModel
from ..models.config_model import ApplicationConfig
from .signature_panel import SignaturePanel
from .canvas_view import CanvasView
import os
from PyPDF2 import PdfWriter, PdfReader
from PIL import Image
import io
from ..core.pdf_signer import PDFSigner
import traceback

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = ApplicationConfig()
        self.document = None
        self.pdf_signer = PDFSigner()
        self.init_ui()

    def init_ui(self):
        """Inicializa la interfaz de usuario"""
        self.setWindowTitle('Firmador PDF')
        self.setMinimumSize(1024, 768)

        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QHBoxLayout(central_widget)
        
        # Panel izquierdo (firmas)
        self.signature_panel = SignaturePanel(self)
        main_layout.addWidget(self.signature_panel, stretch=1)
        
        # Layout central (vista previa y controles)
        central_layout = QVBoxLayout()
        main_layout.addLayout(central_layout, stretch=3)
        
        # Barra de herramientas
        toolbar_layout = QHBoxLayout()
        central_layout.addLayout(toolbar_layout)
        
        # Botones
        self.btn_open = QPushButton('Abrir PDF', self)
        self.btn_open.clicked.connect(self.open_pdf)
        toolbar_layout.addWidget(self.btn_open)
        
        self.btn_save = QPushButton('Guardar PDF', self)
        self.btn_save.clicked.connect(self.save_pdf)
        self.btn_save.setEnabled(False)
        toolbar_layout.addWidget(self.btn_save)
        
        toolbar_layout.addStretch()
        
        # Vista de canvas
        self.canvas_view = CanvasView(self)
        central_layout.addWidget(self.canvas_view, stretch=1)

    def open_pdf(self):
        """Abre un archivo PDF"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Abrir PDF",
            self.config.last_directory,
            "Archivos PDF (*.pdf)"
        )
        
        if file_path:
            try:
                self.config.last_directory = os.path.dirname(file_path)
                self.load_document(file_path)
                self.btn_save.setEnabled(True)
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Error al abrir el PDF: {str(e)}"
                )

    def load_document(self, pdf_path: str):
        """Carga un documento PDF"""
        # Crear manejador de PDF
        reader = PdfReader(pdf_path)
        
        # Obtener dimensiones de páginas
        page_dimensions = {}
        for i in range(len(reader.pages)):
            page = reader.pages[i]
            width = float(page.mediabox.width)
            height = float(page.mediabox.height)
            page_dimensions[i] = {"width": width, "height": height}
        
        # Crear modelo de documento
        self.document = DocumentModel(
            pdf_path=pdf_path,
            total_pages=len(reader.pages),
            page_dimensions=page_dimensions
        )
        
        # Actualizar vista
        self.canvas_view.load_document(self.document)
        self.signature_panel.update_document(self.document)

    def save_pdf(self):
        """Guarda el PDF con las firmas"""
        if not self.document:
            return
            
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Guardar PDF firmado",
                os.path.dirname(self.document.pdf_path),
                "Archivos PDF (*.pdf)"
            )
            
            if file_path:
                # Convertir firmas al formato esperado por PDFSigner
                signatures = [
                    {
                        'image_path': sig.image_path,
                        'page_number': sig.page_number,
                        'position': {'x': sig.position.x, 'y': sig.position.y},
                        'size': {'width': sig.size.width, 'height': sig.size.height}
                    }
                    for sig in self.document.signatures
                ]
                
                print("Firmas a insertar:", signatures)  # Debug
                self.pdf_signer.insert_signature(
                    self.document.pdf_path,
                    file_path,
                    signatures
                )
                
                QMessageBox.information(self, "Éxito", "PDF guardado correctamente")
                
        except Exception as e:
            print(f"Error al guardar PDF: {e}")
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Error al guardar el PDF: {str(e)}")

    def closeEvent(self, event):
        """Maneja el cierre de la ventana"""
        # TODO: Verificar cambios sin guardar
        event.accept() 