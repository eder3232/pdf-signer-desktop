from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, 
    QListWidget, QFileDialog, QMessageBox, QSlider,
    QHBoxLayout, QFrame
)
from PySide6.QtCore import Qt
from ..models.signature_model import SignatureModel, SignaturePosition, SignatureSize
from ..models.document_model import DocumentModel
import os
from PIL import Image

class SignatureWidget(QFrame):
    """Widget que representa una firma individual con sus controles"""
    def __init__(self, signature, index, parent=None):
        super().__init__(parent)
        self.signature = signature
        self.index = index
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Nombre de la firma
        name = os.path.basename(self.signature.image_path)
        title = QLabel(f"Firma {self.index + 1}: {name}")
        layout.addWidget(title)
        
        # Control de tamaño
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Tamaño:"))
        
        self.size_slider = QSlider(Qt.Horizontal)
        self.size_slider.setMinimum(5)
        self.size_slider.setMaximum(50)
        self.size_slider.setValue(15)
        self.size_slider.valueChanged.connect(self.update_size)
        size_layout.addWidget(self.size_slider)
        
        self.size_label = QLabel("15%")
        size_layout.addWidget(self.size_label)
        layout.addLayout(size_layout)
        
        # Estilo
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setLineWidth(1)
        
    def update_size(self, value):
        """Actualiza el tamaño de la firma cuando cambia el slider"""
        print(f"\n=== Actualizando tamaño de firma ===")
        print(f"Valor slider: {value}%")
        
        # Obtener dimensiones de la página actual
        main_window = self.window()
        canvas_view = main_window.canvas_view
        page_dims = canvas_view.document.page_dimensions[self.signature.page_number]
        page_width = float(page_dims.width)
        
        # Calcular nuevo tamaño en puntos PDF
        new_width = page_width * (value / 100.0)
        
        # Mantener proporción
        with Image.open(self.signature.image_path) as img:
            aspect_ratio = img.height / img.width
            new_height = new_width * aspect_ratio
        
        print(f"Nuevo tamaño en puntos PDF: {new_width:.2f}x{new_height:.2f}")
        
        # Actualizar modelo
        self.signature.size.width = new_width
        self.signature.size.height = new_height
        
        # Actualizar UI
        canvas_view.update_preview()

class SignaturePanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.document = None
        self.signature_widgets = {}  # Diccionario para mantener los widgets de firma
        self.init_ui()

    def init_ui(self):
        """Inicializa la interfaz del panel"""
        layout = QVBoxLayout(self)
        
        # Título
        title = QLabel("Firmas")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Contenedor de firmas
        self.signatures_container = QVBoxLayout()
        layout.addLayout(self.signatures_container)
        
        # Botones
        btn_add = QPushButton("Añadir Firma")
        btn_add.clicked.connect(self.add_signature)
        layout.addWidget(btn_add)
        
        btn_remove = QPushButton("Eliminar Firma")
        btn_remove.clicked.connect(self.remove_signature)
        layout.addWidget(btn_remove)
        
        layout.addStretch()
        self.setMaximumWidth(300)

    def add_signature(self):
        """Añade una nueva firma"""
        if not self.document:
            return
            
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar Imagen de Firma",
            "",
            "Imágenes (*.png *.jpg *.jpeg)"
        )
        
        if file_path:
            try:
                print(f"Añadiendo firma desde: {file_path}")
                
                # Verificar que la imagen existe y se puede abrir
                with Image.open(file_path) as img:
                    print(f"Imagen cargada: {img.size}, modo: {img.mode}")
                
                # Obtener la ventana principal
                main_window = self.window()
                current_page = 0
                
                if hasattr(main_window, 'canvas_view'):
                    current_page = main_window.canvas_view.current_page
                
                # Crear modelo de firma
                signature = SignatureModel(
                    image_path=file_path,
                    position=SignaturePosition(x=0, y=0),
                    size=SignatureSize(width=150, height=75),
                    page_number=current_page
                )
                
                # Añadir al documento
                self.document.add_signature(signature)
                print(f"Firma añadida al documento. Total firmas: {len(self.document.signatures)}")
                
                # Crear y añadir widget de firma
                self.add_signature_widget(signature, len(self.document.signatures) - 1)
                
                # Actualizar vista
                if hasattr(main_window, 'canvas_view'):
                    canvas_view = main_window.canvas_view
                    print("Actualizando vista previa desde add_signature")
                    canvas_view.scene.clear()
                    canvas_view.update_preview()
                    canvas_view.fit_to_view()
                    
            except Exception as e:
                print(f"Error al añadir firma: {e}")
                import traceback
                traceback.print_exc()
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Error al añadir firma: {str(e)}"
                )

    def add_signature_widget(self, signature, index):
        """Añade un widget de control para una firma"""
        widget = SignatureWidget(signature, index, self)
        self.signature_widgets[index] = widget
        self.signatures_container.addWidget(widget)

    def remove_signature(self):
        """Elimina la firma seleccionada"""
        if not self.document or not self.signature_widgets:
            return
            
        # Obtener el último widget de firma
        last_index = len(self.document.signatures) - 1
        if last_index >= 0:
            # Eliminar widget
            widget = self.signature_widgets.pop(last_index)
            self.signatures_container.removeWidget(widget)
            widget.deleteLater()
            
            # Eliminar firma del documento
            self.document.signatures.pop(last_index)
            
            # Actualizar vista
            main_window = self.window()
            if hasattr(main_window, 'canvas_view'):
                main_window.canvas_view.update_view()

    def update_document(self, document: DocumentModel):
        """Actualiza el documento actual"""
        self.document = document
        
        # Limpiar widgets existentes
        for widget in self.signature_widgets.values():
            widget.deleteLater()
        self.signature_widgets.clear()
        
        # Crear widgets para firmas existentes
        if document:
            for i, signature in enumerate(document.signatures):
                self.add_signature_widget(signature, i) 