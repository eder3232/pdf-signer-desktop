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

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = ApplicationConfig()
        self.document = None
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
                print("\n=== Iniciando guardado de PDF ===")
                print(f"Guardando en: {file_path}")
                print(f"Total firmas: {len(self.document.signatures)}")
                
                # Crear directorio temporal si no existe
                temp_dir = os.path.join(os.path.dirname(self.document.pdf_path), '.temp')
                os.makedirs(temp_dir, exist_ok=True)
                
                # Abrir PDF original
                reader = PdfReader(self.document.pdf_path)
                writer = PdfWriter()
                
                # Copiar todas las páginas
                for page_num in range(len(reader.pages)):
                    print(f"\nProcesando página {page_num + 1}")
                    page = reader.pages[page_num]
                    
                    # Obtener dimensiones de la página
                    page_width = float(page.mediabox.width)
                    page_height = float(page.mediabox.height)
                    print(f"Dimensiones de página: {page_width}x{page_height}")
                    
                    # Crear una nueva página que será la fusión
                    new_page = writer.add_page(page)
                    
                    # Buscar firmas para esta página
                    page_signatures = [
                        sig for sig in self.document.signatures 
                        if sig.page_number == page_num
                    ]
                    
                    if page_signatures:
                        print(f"Encontradas {len(page_signatures)} firmas para la página {page_num + 1}")
                        for sig in page_signatures:
                            try:
                                print(f"\nProcesando firma: {os.path.basename(sig.image_path)}")
                                print(f"Posición: ({sig.position.x}, {sig.position.y})")
                                print(f"Tamaño: {sig.size.width}x{sig.size.height}")
                                
                                # Cargar imagen de firma
                                with Image.open(sig.image_path) as img:
                                    # Asegurar modo RGBA y redimensionar
                                    img = img.convert('RGBA')
                                    
                                    # Redimensionar firma
                                    desired_width = int(sig.size.width)
                                    aspect_ratio = img.height / img.width
                                    desired_height = int(desired_width * aspect_ratio)
                                    print(f"Redimensionando a: {desired_width}x{desired_height}")
                                    
                                    img = img.resize((desired_width, desired_height), Image.Resampling.LANCZOS)
                                    
                                    # Guardar firma temporal en archivo
                                    temp_sig_path = os.path.join(temp_dir, f'temp_sig_{page_num}_{id(sig)}.pdf')
                                    print(f"Guardando firma temporal en: {temp_sig_path}")
                                    
                                    # Convertir a RGB para evitar problemas con transparencia
                                    img_rgb = Image.new('RGB', img.size, (255, 255, 255))
                                    img_rgb.paste(img, mask=img.split()[3])  # Usar canal alfa como máscara
                                    img_rgb.save(temp_sig_path, format='PDF', resolution=300.0)
                                    
                                    # Crear reader para la firma
                                    sig_reader = PdfReader(temp_sig_path)
                                    sig_page = sig_reader.pages[0]
                                    
                                    # Calcular posición correcta
                                    x = sig.position.x
                                    y = page_height - sig.position.y - desired_height
                                    print(f"Posición final en PDF: ({x}, {y})")
                                    
                                    # Crear una transformación para la firma
                                    operation = {
                                        '/Type': '/XObject',
                                        '/Subtype': '/Form',
                                        '/BBox': [0, 0, desired_width, desired_height],
                                        '/Matrix': [1, 0, 0, 1, x, y]
                                    }
                                    
                                    print("Aplicando transformación y fusionando...")
                                    new_page.merge_transformed_page(
                                        sig_page,
                                        operation,
                                        expand=False
                                    )
                                    
                                    # Limpiar archivo temporal
                                    os.remove(temp_sig_path)
                                    print("Firma procesada correctamente")
                                    
                            except Exception as e:
                                print(f"Error al procesar firma: {e}")
                                import traceback
                                traceback.print_exc()
                                continue
                    
                    print(f"Añadiendo página {page_num + 1} al documento final")
                
                print("\nGuardando documento final...")
                # Guardar el documento final
                with open(file_path, 'wb') as output_file:
                    writer.write(output_file)
                
                print("=== PDF guardado exitosamente ===\n")
                QMessageBox.information(self, "Éxito", "PDF guardado correctamente")
                
        except Exception as e:
            print(f"Error al guardar PDF: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(
                self,
                "Error",
                f"Error al guardar el PDF: {str(e)}"
            )

    def closeEvent(self, event):
        """Maneja el cierre de la ventana"""
        # TODO: Verificar cambios sin guardar
        event.accept() 