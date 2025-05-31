import fitz
import io
from PIL import Image
from typing import Dict, Any

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
        """Inserta las firmas en el PDF usando la lógica probada de sellador_carpetas_v3.py"""
        print("\n=== DEBUG: Firmas a insertar ===")
        for sig in signatures:
            print(f"""
Firma:
  - Página: {sig['page_number']}
  - Posición: ({sig['position']['x']}, {sig['position']['y']})
  - Tamaño: {sig['size']['width']}x{sig['size']['height']}
  - Ruta: {sig['image_path']}
""")
        
        print("\n=== Iniciando proceso de inserción de firmas ===")
        print(f"PDF origen: {pdf_path}")
        print(f"PDF destino: {output_path}")
        print(f"Total firmas a procesar: {len(signatures)}")
        
        doc = fitz.open(pdf_path)
        print(f"PDF abierto correctamente. Total páginas: {len(doc)}")
        
        for idx, signature in enumerate(signatures):
            print(f"\nProcesando firma {idx + 1}:")
            print(f"  Página objetivo: {signature['page_number'] + 1}")
            print(f"  Archivo de firma: {signature['image_path']}")
            print(f"  Posición solicitada: x={signature['position']['x']:.2f}, y={signature['position']['y']:.2f}")
            
            page = doc[signature['page_number']]
            rect = page.rect
            print(f"  Dimensiones de página: {rect.width:.2f}x{rect.height:.2f}")
            
            # Detectar escenario según dimensiones
            escenario = self._detectar_escenario(rect.width, rect.height)
            print(f"  Escenario detectado: {escenario['nombre']}")
            print(f"  Orientación: {escenario['orientacion']}")
            
            try:
                # Cargar y preparar imagen
                with Image.open(signature['image_path']) as img:
                    print(f"  Imagen cargada: {img.size}, modo={img.mode}")
                    img = img.convert('RGBA')
                    
                    # Aplicar transformaciones según escenario y parámetros
                    img_transformed = self._prepare_image(
                        img, 
                        signature['size'],
                        escenario
                    )
                    print(f"  Imagen transformada: {img_transformed.size}")
                    
                    # Convertir a bytes
                    buffer = io.BytesIO()
                    img_transformed.save(buffer, format="PNG", compress_level=0)
                    buffer.seek(0)
                    img_bytes = buffer.getvalue()
                    print(f"  Bytes de imagen generados: {len(img_bytes)} bytes")
                    
                    # Insertar en PDF
                    pix = fitz.Pixmap(img_bytes)
                    print(f"  Pixmap creado: {pix.width}x{pix.height}, alpha={pix.alpha}")
                    
                    signature_rect = self._calculate_position(
                        page.rect,
                        signature['position'],
                        img_transformed.size,
                        escenario
                    )
                    print(f"  Rectángulo calculado: {signature_rect}")
                    
                    # Insertar imagen con parámetros específicos
                    try:
                        page.insert_image(
                            signature_rect,
                            pixmap=pix,
                            overlay=True  # Asegurar que se superpone
                        )
                        print("  Imagen insertada correctamente")
                    except Exception as e:
                        print(f"  Error al insertar imagen: {e}")
                        raise
                    
            except Exception as e:
                print(f"Error procesando firma: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        print("\nGuardando PDF final...")
        try:
            doc.save(output_path, garbage=4, deflate=True)
            print("PDF guardado correctamente")
        except Exception as e:
            print(f"Error al guardar PDF: {e}")
            raise
        finally:
            doc.close()
            print("Documento cerrado")
        
        print("=== Proceso de inserción completado ===\n")

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
        
        print("\n=== DEBUG: Cálculo de posición PDF ===")
        print(f"Página: {page_rect.width}x{page_rect.height}")
        print(f"Imagen: {w_img}x{h_img}")
        print(f"Posición entrada: x={position['x']}, y={position['y']}")
        
        # Convertir coordenadas Y de Qt (desde arriba) a PDF (desde abajo)
        x0 = position['x']
        y0 = page_rect.height - position['y'] - h_img  # Convertir Y e incluir altura de imagen
        x1 = x0 + w_img
        y1 = y0 + h_img
        
        print(f"Rectángulo final PDF: ({x0}, {y0}) -> ({x1}, {y1})")
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