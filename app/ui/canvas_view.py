from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene,
    QGraphicsPixmapItem, QComboBox, QLabel, QHBoxLayout, QPushButton
)
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPixmap, QImage, QPainter
from PIL.ImageQt import ImageQt
from PIL import Image
from typing import Dict
from ..models.document_model import DocumentModel
from ..core.preview_generator import PreviewGenerator
from PyPDF2 import PdfReader
import fitz  # PyMuPDF
import io

class SignatureItem(QGraphicsPixmapItem):
    def __init__(self, pixmap, signature_index: int):
        super().__init__(pixmap)
        self.signature_index = signature_index
        self.setFlag(QGraphicsPixmapItem.ItemIsMovable)
        self.setFlag(QGraphicsPixmapItem.ItemIsSelectable)
        
    def mousePressEvent(self, event):
        """Selecciona el item al hacer clic"""
        super().mousePressEvent(event)
        self.setSelected(True)
        
    def mouseReleaseEvent(self, event):
        """Actualiza la posición en el modelo al soltar"""
        super().mouseReleaseEvent(event)
        scene = self.scene()
        if isinstance(scene, PDFScene):
            scene.update_signature_position(self)

class PDFScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.document = None
        self.signature_items: Dict[int, SignatureItem] = {}
        
    def update_signature_position(self, item: SignatureItem):
        """Actualiza la posición de la firma en el modelo"""
        if self.document and item.signature_index < len(self.document.signatures):
            pos = item.pos()
            signature = self.document.signatures[item.signature_index]
            
            # Factor de zoom usado en la vista previa
            zoom = 2.0
            
            # Obtener dimensiones de la página actual
            page_dims = self.document.page_dimensions[signature.page_number]
            page_height = float(page_dims.height)
            
            print("\n=== DEBUG: Actualización de posición ===")
            print(f"Posición UI (raw): ({pos.x()}, {pos.y()})")
            print(f"Dimensiones página: {page_dims.width}x{page_height}")
            print(f"Altura firma: {signature.size.height}")
            
            # Convertir coordenadas
            pdf_x = pos.x() / zoom
            # Convertir Y considerando:
            # 1. Quitar el zoom
            # 2. Invertir desde abajo (página PDF) a desde arriba (Qt)
            # 3. Considerar altura de la firma
            ui_y = pos.y() / zoom  # Quitar zoom
            pdf_y = ui_y  # Mantener Y como está en UI
            
            signature.position.x = pdf_x
            signature.position.y = pdf_y
            
            print(f"Posición convertida a PDF: ({pdf_x}, {pdf_y})")

    def wheelEvent(self, event):
        """Maneja el zoom con la rueda del mouse"""
        if event.modifiers() == Qt.ControlModifier:
            # Obtener la vista
            view = self.views()[0]
            
            # Calcular factor de zoom
            factor = 1.1 if event.delta() > 0 else 0.9
            
            # Aplicar zoom
            view.scale(factor, factor)
        else:
            super().wheelEvent(event)

class CanvasView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.document = None
        self.current_page = 0
        self.init_ui()

    def init_ui(self):
        """Inicializa la interfaz"""
        layout = QVBoxLayout(self)
        
        # Selector de página
        page_layout = QHBoxLayout()
        self.page_selector = QComboBox()
        self.page_selector.currentIndexChanged.connect(self.change_page)
        page_layout.addWidget(QLabel("Página:"))
        page_layout.addWidget(self.page_selector)
        layout.addLayout(page_layout)
        
        # Controles de zoom
        zoom_layout = QHBoxLayout()
        zoom_in_btn = QPushButton("+")
        zoom_in_btn.clicked.connect(lambda: self.zoom(1.1))
        zoom_layout.addWidget(zoom_in_btn)
        
        zoom_out_btn = QPushButton("-")
        zoom_out_btn.clicked.connect(lambda: self.zoom(0.9))
        zoom_layout.addWidget(zoom_out_btn)
        
        fit_btn = QPushButton("Ajustar")
        fit_btn.clicked.connect(self.fit_to_view)
        zoom_layout.addWidget(fit_btn)
        layout.addLayout(zoom_layout)
        
        # Crear escena y vista
        self.scene = PDFScene(self)
        self.graphics_view = QGraphicsView(self.scene)
        self.graphics_view.setRenderHint(QPainter.Antialiasing)
        self.graphics_view.setRenderHint(QPainter.SmoothPixmapTransform)
        self.graphics_view.setDragMode(QGraphicsView.ScrollHandDrag)
        self.graphics_view.setBackgroundBrush(Qt.white)
        layout.addWidget(self.graphics_view)
        
        # Debug label
        self.debug_label = QLabel("")
        layout.addWidget(self.debug_label)

    def load_document(self, document):
        """Carga un nuevo documento"""
        self.document = document
        self.scene.document = document  # Importante: actualizar también la escena
        
        # Actualizar selector de páginas
        self.page_selector.clear()
        for i in range(document.total_pages):
            self.page_selector.addItem(f"Página {i + 1}")
        
        # Establecer página inicial
        self.current_page = 0
        self.page_selector.setCurrentIndex(0)
        
        # Actualizar vista
        self.update_preview()
        self.fit_to_view()
        
        self.debug_label.setText("Documento cargado")

    def update_preview(self):
        """Actualiza la vista previa"""
        if not self.document:
            return
        
        # Establecer fondo gris claro
        self.scene.setBackgroundBrush(Qt.GlobalColor.lightGray)
        
        try:
            self.scene.clear()  # Limpiar escena antes de actualizar
            print("\n=== Iniciando actualización de vista previa ===")
            print(f"Documento: {self.document.pdf_path}")
            print(f"Página actual: {self.current_page}")
            print(f"Total firmas: {len(self.document.signatures)}")
            
            # Abrir documento PDF
            pdf_document = fitz.open(self.document.pdf_path)
            page = pdf_document[self.current_page]
            
            # Renderizar página
            zoom = 2.0  # Factor de zoom para mejor calidad
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            print(f"Página renderizada: {pix.width}x{pix.height}")
            
            # Convertir a QPixmap
            img_data = pix.samples
            qimg = QImage(img_data, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qimg)
            
            # Añadir página a la escena
            page_item = self.scene.addPixmap(pixmap)
            page_item.setZValue(0)
            
            # Obtener dimensiones de la página actual
            page_dims = self.document.page_dimensions[self.current_page]
            page_width = float(page_dims.width)
            page_height = float(page_dims.height)
            print(f"Dimensiones de página: {page_width}x{page_height}")
            
            # Añadir firmas si existen
            for i, signature in enumerate(self.document.signatures):
                if signature.page_number == self.current_page:
                    try:
                        print(f"\nProcesando firma {i}:")
                        print(f"  Ruta: {signature.image_path}")
                        print(f"  Posición: ({signature.position.x}, {signature.position.y})")
                        
                        # Cargar imagen de firma
                        sig_img = Image.open(signature.image_path)
                        print(f"  Tamaño original: {sig_img.size}")
                        
                        # Redimensionar firma manteniendo proporción
                        desired_width = int(signature.size.width * zoom)  # Usar el tamaño del modelo
                        aspect_ratio = sig_img.height / sig_img.width
                        desired_height = int(desired_width * aspect_ratio)
                        print(f"  Tamaño a renderizar: {desired_width}x{desired_height}")
                        
                        # Convertir y redimensionar
                        sig_img = sig_img.convert('RGBA')
                        sig_img = sig_img.resize((desired_width, desired_height), Image.Resampling.LANCZOS)
                        
                        sig_qimg = ImageQt(sig_img)
                        sig_pixmap = QPixmap.fromImage(sig_qimg)
                        
                        # Crear y posicionar item
                        sig_item = SignatureItem(sig_pixmap, i)
                        sig_item.setZValue(1)
                        
                        # Calcular posición
                        if signature.position.x == 0 and signature.position.y == 0:
                            x = (page_width * zoom - desired_width) / 2
                            y = (page_height * zoom - desired_height) / 2
                        else:
                            x = signature.position.x * zoom
                            # Convertir de coordenadas PDF a Qt
                            y = (page_height - signature.position.y) * zoom - desired_height
                        
                        print(f"  Posicionando firma en: ({x}, {y})")
                        sig_item.setPos(x, y)
                        self.scene.addItem(sig_item)
                        
                    except Exception as e:
                        print(f"Error al procesar firma {i}: {e}")
                        import traceback
                        traceback.print_exc()
            
            # Ajustar vista
            self.graphics_view.setSceneRect(QRectF(0, 0, pixmap.width(), pixmap.height()))
            self.fit_to_view()
            
            pdf_document.close()
            print("=== Actualización de vista previa completada ===\n")
            self.debug_label.setText("Vista previa actualizada")
            
        except Exception as e:
            print(f"Error en update_preview: {e}")
            import traceback
            traceback.print_exc()
            self.debug_label.setText(f"Error en vista previa: {str(e)}")

    def change_page(self, index):
        """Cambia la página actual"""
        if 0 <= index < self.document.total_pages:
            self.current_page = index
            self.update_preview()

    def resizeEvent(self, event):
        """Ajusta la vista cuando se redimensiona el widget"""
        super().resizeEvent(event)
        if self.scene.items():
            self.graphics_view.fitInView(
                self.scene.sceneRect(),
                Qt.AspectRatioMode.KeepAspectRatio
            )

    def wheelEvent(self, event):
        """Redirige el evento de rueda al QGraphicsView"""
        self.graphics_view.wheelEvent(event)

    def zoom(self, factor):
        """Aplica zoom a la vista"""
        self.graphics_view.scale(factor, factor)

    def fit_to_view(self):
        """Ajusta el contenido a la vista"""
        if self.scene.items():
            self.graphics_view.fitInView(
                self.scene.sceneRect(),
                Qt.AspectRatioMode.KeepAspectRatio
            )

    def update_view(self):
        """Actualiza la vista completa"""
        if self.document:
            self.update_preview()
            self.fit_to_view()  # Asegurar que se ajusta a la vista 

    def update_signature_position(self, item):
        """Actualiza la posición de la firma en el modelo"""
        if self.document and item.signature_index < len(self.document.signatures):
            signature = self.document.signatures[item.signature_index]
            
            # Actualizar página actual
            signature.page_number = self.current_page
            
            # Actualizar posición en el modelo a través de la escena
            self.scene.update_signature_position(item)
            
            # Actualizar vista previa
            self.update_preview() 