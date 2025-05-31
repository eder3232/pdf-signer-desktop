from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLabel, 
    QSpinBox, QStackedWidget, QListWidget, QPushButton
)
from PySide6.QtCore import Signal, Qt
from ..models.signature_mode_config import SignatureMode, SignatureModeConfig

class ModeSelector(QWidget):
    mode_changed = Signal(SignatureModeConfig)  # Señal cuando cambia el modo

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_config = SignatureModeConfig(SignatureMode.LIBRE)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Selector principal de modo
        mode_layout = QHBoxLayout()
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([mode.value.title() for mode in SignatureMode])
        self.mode_combo.currentIndexChanged.connect(self.on_mode_changed)
        
        mode_layout.addWidget(QLabel("Modo de firma:"))
        mode_layout.addWidget(self.mode_combo)
        layout.addLayout(mode_layout)
        
        # Widget apilado para configuraciones específicas
        self.config_stack = QStackedWidget()
        
        # Widget para modo libre (vacío)
        self.config_stack.addWidget(QWidget())
        
        # Widget para modo masivo
        masivo_widget = QWidget()
        masivo_layout = QVBoxLayout(masivo_widget)
        masivo_layout.addWidget(QLabel("Se aplicará la firma a todas las páginas excepto la última"))
        self.config_stack.addWidget(masivo_widget)
        
        # Widget para modo plantilla
        plantilla_widget = QWidget()
        plantilla_layout = QVBoxLayout(plantilla_widget)
        
        interval_layout = QHBoxLayout()
        self.interval_spin = QSpinBox()
        self.interval_spin.setMinimum(1)
        self.interval_spin.setMaximum(100)
        self.interval_spin.valueChanged.connect(self.on_interval_changed)
        interval_layout.addWidget(QLabel("Firmar cada:"))
        interval_layout.addWidget(self.interval_spin)
        interval_layout.addWidget(QLabel("páginas"))
        interval_layout.addStretch()
        
        plantilla_layout.addLayout(interval_layout)
        self.config_stack.addWidget(plantilla_widget)
        
        # Widget para modo selectivo
        selectivo_widget = QWidget()
        selectivo_layout = QVBoxLayout(selectivo_widget)
        
        self.pages_list = QListWidget()
        selectivo_layout.addWidget(QLabel("Seleccionar páginas:"))
        selectivo_layout.addWidget(self.pages_list)
        
        buttons_layout = QHBoxLayout()
        self.btn_select_all = QPushButton("Seleccionar Todo")
        self.btn_clear = QPushButton("Limpiar")
        buttons_layout.addWidget(self.btn_select_all)
        buttons_layout.addWidget(self.btn_clear)
        selectivo_layout.addLayout(buttons_layout)
        
        self.config_stack.addWidget(selectivo_widget)
        
        layout.addWidget(self.config_stack)
        
    def on_mode_changed(self, index):
        """Maneja cambios en el modo de firma"""
        # Obtener el modo directamente del índice
        mode = list(SignatureMode)[index]
        print(f"\n=== Cambiando a modo: {mode.value} ===")
        
        # Actualizar la configuración actual
        self.current_config = SignatureModeConfig(mode)
        self.config_stack.setCurrentIndex(index)
        
        # Configurar modo según selección
        if mode == SignatureMode.MASIVO:
            print("Configurando modo masivo")
            # No necesita configuración adicional
        elif mode == SignatureMode.PLANTILLA:
            print("Configurando modo plantilla")
            self.current_config.pattern_interval = self.interval_spin.value()
        elif mode == SignatureMode.SELECTIVO:
            print("Configurando modo selectivo")
            self.current_config.affected_pages = [i for i in range(self.pages_list.count())
                                           if self.pages_list.item(i).checkState() == Qt.Checked]
        
        print(f"Configuración completada. Modo: {self.current_config.mode.value}")
        
        # Obtener la ventana principal y resetear el estado
        main_window = self.window()
        if hasattr(main_window, 'reset_application_state'):
            main_window.reset_application_state()
        
        # Emitir el cambio de modo después del reset
        self.mode_changed.emit(self.current_config)
        
    def on_interval_changed(self, value):
        if self.current_config.mode == SignatureMode.PLANTILLA:
            self.current_config.pattern_interval = value
            self.mode_changed.emit(self.current_config)
            
    def update_for_document(self, total_pages: int):
        """Actualiza la UI según el número de páginas del documento"""
        # Actualizar lista de páginas para modo selectivo
        self.pages_list.clear()
        for i in range(total_pages):
            self.pages_list.addItem(f"Página {i + 1}")
        
        # Deshabilitar modos no aplicables
        masivo_index = list(SignatureMode).index(SignatureMode.MASIVO)
        self.mode_combo.setEnabled(total_pages >= 2)  # Habilitar solo si hay 2 o más páginas 