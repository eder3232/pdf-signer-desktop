import sys
import os
from pathlib import Path

# Añadir el directorio raíz del proyecto al PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from create_test_pdf import create_test_pdf
from create_test_signature import create_test_signature

def setup_test_files():
    """Prepara archivos de prueba"""
    # Crear directorio de pruebas si no existe
    test_dir = Path("test_files")
    test_dir.mkdir(exist_ok=True)
    
    # Crear archivos de prueba
    pdf_path = test_dir / "test_document.pdf"
    sig_path = test_dir / "test_signature.png"
    
    create_test_pdf(str(pdf_path))
    create_test_signature(str(sig_path))
    
    return pdf_path, sig_path

if __name__ == "__main__":
    # Preparar archivos de prueba
    pdf_path, sig_path = setup_test_files()
    print(f"Archivos de prueba creados en:")
    print(f"PDF: {pdf_path}")
    print(f"Firma: {sig_path}")
    
    # Ejecutar aplicación
    from main import main
    main() 