from PIL import Image, ImageDraw

def create_test_signature(output_path: str = "test_signature.png"):
    """Crea una imagen de firma de prueba"""
    # Crear imagen con fondo transparente
    img = Image.new('RGBA', (200, 100), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # Dibujar una firma simulada
    draw.line((50, 50, 150, 50), fill='black', width=2)
    draw.line((150, 50, 150, 70), fill='black', width=2)
    
    img.save(output_path)
    return output_path 