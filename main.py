import sys
from PySide6.QtWidgets import QApplication
from app.ui.main_window import MainWindow
import logging

def setup_logging():
    """Configura el sistema de logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('firmador.log'),
            logging.StreamHandler()
        ]
    )

def main():
    """Punto de entrada principal de la aplicación"""
    try:
        # Configurar logging
        setup_logging()
        logger = logging.getLogger(__name__)
        logger.info("Iniciando aplicación")
        
        # Crear aplicación Qt
        app = QApplication(sys.argv)
        app.setApplicationName("Firmador PDF")
        app.setApplicationVersion("1.0.0")
        
        # Crear y mostrar ventana principal
        window = MainWindow()
        window.show()
        
        # Ejecutar loop principal
        sys.exit(app.exec())
        
    except Exception as e:
        logger.error(f"Error fatal: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main() 