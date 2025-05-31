from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene,
    QGraphicsPixmapItem, QComboBox, QLabel, QHBoxLayout, QPushButton
)
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPixmap, QImage, QPainter
from PIL.ImageQt import ImageQt
from PIL import Image
from typing import Dict, List
from .mode_selector import ModeSelector
from ..models.document_model import DocumentModel
from ..models.signature_mode_config import SignatureMode, SignatureModeConfig
from ..core.preview_generator import PreviewGenerator
from PyPDF2 import PdfReader
import fitz  # PyMuPDF
import io

class SignatureItem(QGraphicsPixmapItem):
    def __init__(self, pixmap, signature_index: int, original_size: tuple):
        super().__init__(pixmap)
        self.signature_index = signature_index
        self.original_pixmap = pixmap
        self.original_size = original_size  # (width, height)
        self.setFlag(QGraphicsPixmapItem.ItemIsMovable)
        self.setFlag(QGraphicsPixmapItem.ItemIsSelectable)
        
    def update_size(self, new_size: tuple):
        """Actualiza el tamaño de la firma manteniendo la proporción"""
        scaled_pixmap = self.original_pixmap.scaled(
            new_size[0], new_size[1],
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.setPixmap(scaled_pixmap)
        
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
        self.signature_items = {}  # Asegurar que siempre existe
        
    def update_signature_position(self, item: SignatureItem):
        """Actualiza la posición de la firma en el modelo"""
        if self.document and item.signature_index < len(self.document.signatures):
            pos = item.pos()
            signature = self.document.signatures[item.signature_index]
            
            # Factor de zoom usado en la vista previa
            zoom = 2.0
            
            # Obtener dimensiones de la página actual en cm
            page_dims = self.document.page_dimensions[signature.page_number]
            page_height_cm = DocumentModel.points_to_cm(float(page_dims.height))
            
            print("\n=== DEBUG: Actualización de posición ===")
            print(f"Posición UI (raw): ({pos.x()}, {pos.y()})")
            
            # Convertir a centímetros
            pos_x_cm = DocumentModel.points_to_cm(pos.x() / zoom)
            pos_y_cm = DocumentModel.points_to_cm(pos.y() / zoom)
            
            print(f"Posición en cm desde arriba: ({pos_x_cm:.2f}, {pos_y_cm:.2f})")
            print(f"Altura página en cm: {page_height_cm:.2f}")
            
            # Guardar posición en el modelo (en puntos PDF)
            signature.position.x = DocumentModel.cm_to_points(pos_x_cm)
            signature.position.y = DocumentModel.cm_to_points(pos_y_cm)
            
            print(f"Posición guardada en puntos PDF: ({signature.position.x:.2f}, {signature.position.y:.2f})")

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

    def clear(self):
        """Sobrescribir clear para limpiar también signature_items"""
        super().clear()
        self.signature_items.clear()
        self.document = None

class CanvasView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.document = None
        self.current_page = 0
        self.mode_indicator = QLabel()
        self.affected_pages_indicator = QLabel()
        self.init_ui()

    def init_ui(self):
        """Inicializa la interfaz"""
        layout = QVBoxLayout(self)
        
        # Selector de modo
        self.mode_selector = ModeSelector(self)
        self.mode_selector.mode_changed.connect(self.on_mode_changed)
        layout.addWidget(self.mode_selector)
        
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

        # Mode indicators
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Modo:"))
        mode_layout.addWidget(self.mode_indicator)
        layout.addLayout(mode_layout)
        
        affected_layout = QHBoxLayout()
        affected_layout.addWidget(QLabel("Páginas a firmar:"))
        affected_layout.addWidget(self.affected_pages_indicator)
        layout.addLayout(affected_layout)

    def load_document(self, document):
        """Carga un nuevo documento"""
        self.document = document
        self.scene.document = document
        
        # Actualizar selector de páginas
        self.page_selector.clear()
        for i in range(document.total_pages):
            self.page_selector.addItem(f"Página {i + 1}")
        
        # Actualizar selector de modo
        self.mode_selector.update_for_document(document.total_pages)
        
        # Establecer página inicial
        self.current_page = 0
        self.page_selector.setCurrentIndex(0)
        
        # Actualizar vista
        self.update_preview()
        self.fit_to_view()
        self.update_mode_indicators()
        
        self.debug_label.setText("Documento cargado")

    def on_mode_changed(self, mode_config: SignatureModeConfig):
        """Maneja cambios en el modo de firma"""
        if self.document:
            print(f"Actualizando modo a: {mode_config.mode.value}")
            self.document.signature_mode = mode_config
            
            # Actualizar selector de páginas según el modo
            self.page_selector.clear()
            if mode_config.mode == SignatureMode.MASIVO:
                self.page_selector.addItem("Primera Página (Plantilla)", 0)
                self.page_selector.addItem("Última Página", self.document.total_pages - 1)
                # Mostrar mensaje informativo
                self.debug_label.setText(
                    "Modo Masivo: La firma en la primera página se replicará en todas excepto la última"
                )
            else:
                for i in range(self.document.total_pages):
                    self.page_selector.addItem(f"Página {i + 1}", i)
                self.debug_label.setText("")
            
            # Actualizar vista
            self.current_page = self.page_selector.currentData()
            self.update_preview()
            self.update_mode_indicators()

    def update_preview(self):
        """Actualiza la vista previa del PDF"""
        if not self.document or not hasattr(self, 'scene'):
            print("No hay documento o escena para mostrar")
            return
        
        try:
            # Validar página actual
            if self.current_page is None:
                print("No hay página seleccionada")
                return
            
            if not (0 <= self.current_page < self.document.total_pages):
                print(f"Página inválida: {self.current_page}")
                return
            
            print(f"Actualizando vista previa de página {self.current_page + 1}")
            
            # Limpiar escena
            self.scene.clear()
            
            # Factor de zoom para la vista previa (2x por defecto)
            zoom = 2.0
            
            # Generar vista previa de la página actual
            preview = PreviewGenerator.generate_page_preview(
                self.document.pdf_path, 
                self.current_page
            )
            
            # Convertir a QPixmap y mostrar
            pixmap = QPixmap.fromImage(ImageQt(preview))
            page_item = self.scene.addPixmap(pixmap)
            
            # Añadir firmas si existen
            if self.document.signatures:
                for i, signature in enumerate(self.document.signatures):
                    if signature.page_number == self.current_page:
                        # Cargar imagen de firma
                        sig_image = Image.open(signature.image_path)
                        sig_pixmap = QPixmap.fromImage(ImageQt(sig_image))
                        
                        # Tamaño original en puntos PDF
                        original_size = (
                            signature.size.width * zoom,
                            signature.size.height * zoom
                        )
                        
                        # Crear y posicionar item de firma
                        sig_item = SignatureItem(sig_pixmap, i, original_size)
                        sig_item.setPos(
                            signature.position.x * zoom,
                            signature.position.y * zoom
                        )
                        sig_item.update_size(original_size)
                        self.scene.addItem(sig_item)
                        self.scene.signature_items[i] = sig_item
            
            # Actualizar indicadores
            self.update_mode_indicators()
            
        except Exception as e:
            print(f"Error en update_preview: {e}")
            import traceback
            traceback.print_exc()
            self.debug_label.setText(f"Error en vista previa: {str(e)}")

    def _get_preview_pages(self) -> List[int]:
        """Determina qué páginas mostrar según el modo actual"""
        if not self.document:
            return []
            
        mode = self.document.signature_mode.mode
        if mode == SignatureMode.MASIVO:
            # En modo masivo, mostrar primera y última página
            return [0, self.document.total_pages - 1]
        else:
            # En otros modos, mostrar la página actual
            return [self.current_page]

    def change_page(self, index):
        """Cambia la página actual"""
        if index >= 0 and self.document:
            page_number = self.page_selector.itemData(index)
            if page_number is not None:
                print(f"\n=== Cambiando a página {page_number + 1} ===")
                self.current_page = page_number
                self.update_preview()
            else:
                print(f"Error: Índice de página inválido: {index}")

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
            old_page = signature.page_number
            
            print("\n=== Actualizando posición de firma ===")
            print(f"Firma #{item.signature_index + 1} en página {self.current_page + 1}")
            
            # Actualizar página actual
            signature.page_number = self.current_page
            
            # En modo masivo, actualizar todas las firmas si movemos la primera
            if (self.document.signature_mode.mode == SignatureMode.MASIVO and 
                old_page == 0 and self.current_page == 0):
                pos = item.pos()
                print("Modo masivo: Actualizando todas las firmas")
                for sig in self.document.signatures[:-1]:  # Excluir última página
                    sig.position.x = pos.x() / 2.0  # Convertir coordenadas UI a PDF
                    sig.position.y = pos.y() / 2.0
                    print(f"Posición actualizada: ({sig.position.x:.2f}, {sig.position.y:.2f})")
            else:
                # Actualizar posición normal
                self.scene.update_signature_position(item)
            
            # Actualizar vista previa
            self.update_preview()

    def update_mode_indicators(self):
        """Actualiza indicadores visuales del modo de firma"""
        if not self.document:
            self.mode_indicator.setText("Sin documento")
            self.affected_pages_indicator.setText("")
            return
        
        try:
            mode = self.document.signature_mode
            pages_to_sign = self.document.get_pages_to_sign() or []
            
            # Actualizar etiqueta de modo
            mode_text = f"Modo: {mode.mode.value.title()}"
            if mode.mode == SignatureMode.PLANTILLA:
                mode_text += f" (cada {mode.pattern_interval} páginas)"
            elif mode.mode == SignatureMode.MASIVO:
                mode_text += " (Primera página define todas excepto la última)"
            self.mode_indicator.setText(mode_text)
            
            # Actualizar indicador de páginas afectadas
            affected = f"Páginas a firmar: {len(pages_to_sign)} de {self.document.total_pages}"
            if mode.mode == SignatureMode.SELECTIVO:
                excluded = len(mode.excluded_pages)
                affected += f" (excluidas: {excluded})"
            self.affected_pages_indicator.setText(affected)
            
        except Exception as e:
            print(f"Error actualizando indicadores: {e}")
            self.mode_indicator.setText("Error en modo")
            self.affected_pages_indicator.setText("")

    def update_signature_size(self, signature_index: int, new_size: tuple):
        """Actualiza el tamaño de una firma específica"""
        if signature_index in self.scene.signature_items:
            sig_item = self.scene.signature_items[signature_index]
            sig_item.update_size(new_size)
            
            # Actualizar tamaño en el modelo
            signature = self.document.signatures[signature_index]
            signature.size.width = new_size[0] / 2.0  # Convertir de UI a puntos PDF
            signature.size.height = new_size[1] / 2.0 

    def clear_view(self):
        """Limpia la vista del canvas"""
        if hasattr(self, 'scene'):
            # Limpiar escena
            self.scene.clear()
            if hasattr(self.scene, 'signature_items'):
                self.scene.signature_items.clear()
            self.scene.document = None
            
        # Resetear estado del canvas
        self.current_page = 0
        self.document = None
        self.page_selector.clear()
        self.debug_label.setText("")
        self.mode_indicator.setText("Sin documento")
        self.affected_pages_indicator.setText("") 