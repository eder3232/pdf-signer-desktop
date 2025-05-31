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
from ..models.signature_mode_config import SignatureMode

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
        
        # Obtener el modo actual si existe
        current_mode = None
        if hasattr(self, 'canvas_view') and hasattr(self.canvas_view, 'mode_selector'):
            current_mode = self.canvas_view.mode_selector.current_config
        
        # Crear modelo de documento
        self.document = DocumentModel(
            pdf_path=pdf_path,
            total_pages=len(reader.pages),
            page_dimensions=page_dimensions
        )
        
        # Restaurar el modo si existía
        if current_mode:
            print(f"Restaurando modo: {current_mode.mode.value}")
            self.document.signature_mode = current_mode
        
        # Actualizar vista
        self.canvas_view.load_document(self.document)
        self.signature_panel.update_document(self.document)

    def save_pdf(self):
        """Guarda el PDF con las firmas"""
        try:
            if not self.document or not self.document.signatures:
                QMessageBox.warning(self, "Advertencia", "No hay firmas para guardar")
                return
            
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Guardar PDF firmado",
                os.path.dirname(self.document.pdf_path),
                "Archivos PDF (*.pdf)"
            )
            
            if file_path:
                print("\n=== Preparando firmas para inserción ===")
                print(f"Modo actual: {self.document.signature_mode.mode.value}")
                print(f"Total de firmas en documento: {len(self.document.signatures)}")
                print("\nFirmas actuales:")
                for idx, sig in enumerate(self.document.signatures):
                    print(f"Firma #{idx + 1}:")
                    print(f"  - Página: {sig.page_number + 1}")
                    print(f"  - Posición: ({sig.position.x:.2f}, {sig.position.y:.2f})")
                    print(f"  - Tamaño: {sig.size.width}x{sig.size.height}")
                    print(f"  - Archivo: {sig.image_path}")
                
                # Convertir firmas al formato esperado por PDFSigner
                signatures = []
                
                # En modo masivo, replicar la firma de la primera página
                if self.document.signature_mode.mode == SignatureMode.MASIVO:
                    print("\n=== Procesando modo masivo ===")
                    
                    # Buscar firma en la primera página
                    first_page_sig = None
                    last_page_sig = None
                    
                    for sig in self.document.signatures:
                        if sig.page_number == 0:
                            first_page_sig = sig
                            print("Encontrada firma de primera página")
                        elif sig.page_number == self.document.total_pages - 1:
                            last_page_sig = sig
                            print("Encontrada firma de última página")
                    
                    print(f"Firma de primera página encontrada: {first_page_sig is not None}")
                    
                    if first_page_sig:
                        print(f"Replicando firma en {self.document.total_pages - 1} páginas")
                        # Replicar en todas las páginas excepto la última
                        for page in range(self.document.total_pages - 1):
                            signatures.append({
                                'image_path': first_page_sig.image_path,
                                'page_number': page,
                                'position': {
                                    'x': first_page_sig.position.x,
                                    'y': first_page_sig.position.y
                                },
                                'size': {
                                    'width': first_page_sig.size.width,
                                    'height': first_page_sig.size.height
                                }
                            })
                            print(f"Firma replicada en página {page + 1}")
                else:
                    print("\nProcesando modo normal")
                    # Modo normal: usar firmas tal cual están
                    for sig in self.document.signatures:
                        signatures.append({
                            'image_path': sig.image_path,
                            'page_number': sig.page_number,
                            'position': {'x': sig.position.x, 'y': sig.position.y},
                            'size': {'width': sig.size.width, 'height': sig.size.height}
                        })
                
                print(f"\nTotal de firmas preparadas: {len(signatures)}")
                print("Detalle de firmas a insertar:")
                for idx, sig in enumerate(signatures, 1):
                    print(f"""
Firma preparada #{idx}:
  - Página: {sig['page_number'] + 1}
  - Posición: ({sig['position']['x']:.2f}, {sig['position']['y']:.2f})
  - Tamaño: {sig['size']['width']}x{sig['size']['height']}
  - Archivo: {sig['image_path']}
""")
                
                # Insertar firmas
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

    def reset_application_state(self):
        """Resetea el estado de la aplicación al cambiar de modo"""
        print("\n=== Reseteando estado de la aplicación ===")
        
        # Limpiar documento actual
        self.document = None
        
        # Resetear canvas
        if hasattr(self, 'canvas_view'):
            self.canvas_view.clear_view()
            self.canvas_view.update_preview()
        
        # Resetear panel de firmas
        if hasattr(self, 'signature_panel'):
            self.signature_panel.clear_signatures()
        
        # Deshabilitar botones que requieren documento
        self.btn_save.setEnabled(False)
        
        print("Estado de la aplicación reseteado")
        
        # Mostrar mensaje al usuario
        QMessageBox.information(
            self,
            "Cambio de Modo",
            "Se ha cambiado el modo de firma.\nPor favor, vuelva a cargar el documento PDF."
        ) 