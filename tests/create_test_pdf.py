from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

def create_test_pdf(output_path: str = "test_document.pdf"):
    """Crea un PDF de prueba con contenido básico"""
    c = canvas.Canvas(output_path, pagesize=A4)
    
    # Primera página
    c.drawString(100, 750, "Página 1 - Documento de prueba")
    c.drawString(100, 700, "Área para firma 1")
    c.rect(100, 600, 200, 100)  # Rectángulo para indicar área de firma
    
    # Segunda página
    c.showPage()
    c.drawString(100, 750, "Página 2 - Documento de prueba")
    c.drawString(100, 700, "Área para firma 2")
    c.rect(100, 600, 200, 100)
    
    c.save()
    return output_path 