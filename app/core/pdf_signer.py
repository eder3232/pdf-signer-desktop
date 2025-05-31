import fitz
import io
from PIL import Image
from typing import Dict, Any
from app.models.document_model import DocumentModel

class PDFSigner:
    def __init__(self):
        # Constantes para detección de escenarios
        self.UMBRAL_A4_ANCHO = 595
        self.UMBRAL_A4_ALTO = 842
        self.MARGEN_ERROR = 50

        self.escenarios = {
            "A4_VERTICAL": {
                "nombre": "A4 Vertical",
                "orientacion": "vertical",
                "ancho_deseado": 120,
                "separacion_derecha": 100,
                "separacion_inferior": 50,
                "variabilidad_horizontal_pct": 80,
                "variabilidad_vertical_pct": 20,
                "variabilidad_giro": 5,
                "rotacion_base": 0,
            },
            "A4_HORIZONTAL": {
                "nombre": "A4 Horizontal",
                "orientacion": "horizontal",
                "ancho_deseado": 70,
                "separacion_derecha": 100,
                "separacion_inferior": 250,
                "variabilidad_horizontal_pct": 80,
                "variabilidad_vertical_pct": 20,
                "variabilidad_giro": 5,
                "rotacion_base": 90,
            },
            "PLANOS": {
                "nombre": "Planos / Hojas Grandes",
                "orientacion": "vertical",
                "ancho_deseado": 180,
                "separacion_derecha": 90,
                "separacion_inferior": 100,
                "variabilidad_horizontal_pct": 50,
                "variabilidad_vertical_pct": 20,
                "variabilidad_giro": 5,
                "rotacion_base": 0,
            }
        }

    def insert_signature(self, pdf_path: str, output_path: str, signatures: list[Dict[str, Any]]):
        """Inserta las firmas en el PDF usando la lógica probada"""
        print("\n=== INICIO DE PROCESO DE FIRMA ===")
        print(f"Total de firmas a procesar: {len(signatures)}")
        
        # Abrir documento original
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        print(f"PDF abierto: {pdf_path}")
        print(f"Total páginas en documento: {total_pages}")
        
        # Crear documento temporal para el resultado
        result_doc = fitz.open()
        
        try:
            # Procesar cada página
            for page_num in range(total_pages):
                print(f"\n=== Procesando página {page_num + 1} ===")
                
                # Copiar página original
                page = doc[page_num]
                result_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
                result_page = result_doc[page_num]
                
                # Buscar firmas para esta página
                page_signatures = [sig for sig in signatures if sig['page_number'] == page_num]
                
                if page_signatures:
                    print(f"Encontradas {len(page_signatures)} firmas para esta página")
                    
                    for idx, signature in enumerate(page_signatures, 1):
                        try:
                            print(f"\nProcesando firma #{idx} en página {page_num + 1}")
                            
                            # Cargar y preparar imagen de firma
                            with Image.open(signature['image_path']) as img:
                                print(f"Firma cargada: {img.size}, modo={img.mode}")
                                img = img.convert('RGBA')
                                
                                # Convertir a bytes
                                buffer = io.BytesIO()
                                img.save(buffer, format="PNG")
                                img_bytes = buffer.getvalue()
                                
                                # Crear Pixmap y rectángulo de inserción
                                pix = fitz.Pixmap(img_bytes)
                                x0 = signature['position']['x']
                                y0 = signature['position']['y']
                                x1 = x0 + signature['size']['width']
                                y1 = y0 + signature['size']['height']
                                
                                print(f"""
Insertando firma:
  - Posición inicial: ({x0:.2f}, {y0:.2f})
  - Posición final: ({x1:.2f}, {y1:.2f})
  - Tamaño final: {signature['size']['width']:.2f}x{signature['size']['height']:.2f}
""")
                                
                                # Insertar firma
                                signature_rect = fitz.Rect(x0, y0, x1, y1)
                                result_page.insert_image(signature_rect, pixmap=pix)
                                print(f"Firma insertada correctamente")
                                
                        except Exception as e:
                            print(f"ERROR al procesar firma #{idx} en página {page_num + 1}: {str(e)}")
                            import traceback
                            traceback.print_exc()
                else:
                    print("No hay firmas para esta página")
            
            # Guardar resultado
            print("\n=== Guardando documento final ===")
            print(f"Ruta destino: {output_path}")
            result_doc.save(output_path)
            print("Documento guardado exitosamente")
            
        except Exception as e:
            print(f"ERROR en el proceso: {str(e)}")
            traceback.print_exc()
            raise
        finally:
            doc.close()
            result_doc.close()
            print("\n=== PROCESO DE FIRMA COMPLETADO ===")

    def _detectar_escenario(self, width: float, height: float) -> Dict:
        """Detecta el escenario basado en las dimensiones de la página"""
        # A4 Vertical
        if (abs(width - self.UMBRAL_A4_ANCHO) <= self.MARGEN_ERROR and 
            abs(height - self.UMBRAL_A4_ALTO) <= self.MARGEN_ERROR and 
            width < height):
            return self.escenarios["A4_VERTICAL"]
        
        # A4 Horizontal
        if (abs(width - self.UMBRAL_A4_ALTO) <= self.MARGEN_ERROR and 
            abs(height - self.UMBRAL_A4_ANCHO) <= self.MARGEN_ERROR and 
            width > height):
            return self.escenarios["A4_HORIZONTAL"]
        
        # Planos u otros
        escenario = self.escenarios["PLANOS"].copy()
        escenario["orientacion"] = "horizontal" if width > height else "vertical"
        return escenario

    def _prepare_image(self, img: Image, size: Dict, escenario: Dict) -> Image:
        """Prepara la imagen según el escenario"""
        print("\nPreparando imagen:")
        print(f"Tamaño original: {img.size}")
        print(f"Tamaño solicitado: {size}")
        
        # Usar exactamente el tamaño especificado
        nuevo_w = int(size['width'])
        nuevo_h = int(size['height'])  # Usar height directamente del modelo
        
        print(f"Nuevo tamaño calculado: {nuevo_w}x{nuevo_h}")
        
        # Redimensionar imagen manteniendo calidad
        img_resized = img.resize((nuevo_w, nuevo_h), Image.Resampling.LANCZOS)
        return img_resized

    def _calculate_position(self, page_rect: fitz.Rect, position: Dict, 
                          img_size: tuple, escenario: Dict) -> fitz.Rect:
        """Calcula la posición final de la firma"""
        w_img, h_img = img_size
        
        # Convertir todo a centímetros
        page_height_cm = DocumentModel.points_to_cm(page_rect.height)
        pos_x_cm = DocumentModel.points_to_cm(position['x'])
        pos_y_cm = DocumentModel.points_to_cm(position['y'])
        h_img_cm = DocumentModel.points_to_cm(h_img)
        w_img_cm = DocumentModel.points_to_cm(w_img)
        
        print("\n=== DEBUG: Cálculo de posición PDF ===")
        print(f"Dimensiones página (cm): {DocumentModel.points_to_cm(page_rect.width):.2f}x{page_height_cm:.2f}")
        print(f"Tamaño imagen (cm): {w_img_cm:.2f}x{h_img_cm:.2f}")
        print(f"Posición solicitada (cm desde arriba): ({pos_x_cm:.2f}, {pos_y_cm:.2f})")
        
        # CAMBIO: Ya no invertimos Y, asumimos mismo sistema que Qt
        y_final_cm = pos_y_cm
        
        print(f"""
Cálculo de Y:
  - Altura página: {page_height_cm:.2f} cm
  - Posición Y desde arriba: {pos_y_cm:.2f} cm
  - Altura imagen: {h_img_cm:.2f} cm
  - Y final = {y_final_cm:.2f} cm (mantenemos Y desde arriba)
""")
        
        # Convertir a puntos PDF manteniendo el sistema de coordenadas
        x0 = position['x']
        y0 = position['y']  # Usamos Y directamente
        x1 = x0 + w_img
        y1 = y0 + h_img
        
        print(f"""
Rectángulo final:
  - En centímetros: ({pos_x_cm:.2f}, {y_final_cm:.2f}) -> ({pos_x_cm + w_img_cm:.2f}, {y_final_cm + h_img_cm:.2f})
  - En puntos PDF: ({x0:.2f}, {y0:.2f}) -> ({x1:.2f}, {y1:.2f})
""")
        
        return fitz.Rect(x0, y0, x1, y1)

    def test_simple_insertion(self, pdf_path: str, output_path: str, signature_path: str):
        """Método de prueba para inserción simple"""
        print("\n=== Test de inserción simple ===")
        doc = fitz.open(pdf_path)
        page = doc[0]  # Primera página
        
        # Cargar imagen directamente
        img = Image.open(signature_path)
        img = img.convert('RGBA')
        
        # Convertir a bytes
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        img_bytes = buffer.getvalue()
        
        # Insertar en el centro de la página
        pix = fitz.Pixmap(img_bytes)
        rect = page.rect
        x0 = (rect.width - pix.width) / 2
        y0 = (rect.height - pix.height) / 2
        signature_rect = fitz.Rect(x0, y0, x0 + pix.width, y0 + pix.height)
        
        page.insert_image(signature_rect, pixmap=pix)
        
        # Guardar
        doc.save(output_path)
        doc.close()
        print("=== Test completado ===\n")

    def apply_signatures(self, output_path: str) -> None:
        """Aplica las firmas al PDF y guarda el resultado"""
        if self.document.signature_mode.mode == SignatureMode.MASIVO:
            # Verificar que tenemos al menos una firma
            if not self.document.signatures:
                raise ValueError("No hay firmas para aplicar")
            
            # Verificar que la primera firma está en la página 0
            if not any(sig.page_number == 0 for sig in self.document.signatures):
                raise ValueError("En modo masivo, debe haber una firma en la primera página")
        
        # Resto del código de aplicación de firmas... 