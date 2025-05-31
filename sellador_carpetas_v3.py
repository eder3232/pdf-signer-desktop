import os
import fitz  # PyMuPDF
import random
from PIL import Image
import io

# ==========================================================
#            CONFIGURACIÓN DE ESCENARIOS
# ==========================================================
# Escenario 1: A4 Vertical (aprox. 595×842 pt)
escenario_1 = {
    "nombre": "A4 Vertical",
    "orientacion": "vertical",  # Se usa la fórmula clásica
    "ancho_deseado": 120,
    "separacion_derecha": 100,
    "separacion_inferior": 50,
    "variabilidad_horizontal_pct": 80,
    "variabilidad_vertical_pct": 20,
    "variabilidad_giro": 5,
    "rotacion_base": 0,
}

# Escenario 2: A4 Horizontal (aprox. 842×595 pt)
escenario_2 = {
    "nombre": "A4 Horizontal",
    "orientacion": "horizontal",  # Usaremos fórmula con separaciones intercambiadas
    "ancho_deseado": 70,
    "separacion_derecha": 100,  # En este caso, actuará en el eje vertical
    "separacion_inferior": 250,  # Actúa en el eje horizontal
    "variabilidad_horizontal_pct": 80,
    "variabilidad_vertical_pct": 20,
    "variabilidad_giro": 5,
    "rotacion_base": 90,  # Para orientar el sello en la página horizontal
}

# Escenario 3: Hojas grandes (ej. planos o tamaños mayores a A4)
# Se ajustará la orientación según las dimensiones reales de la página.
escenario_3 = {
    "nombre": "Planos / Hojas Grandes",
    "orientacion": "vertical",  # Valor por defecto, se modificará según corresponda.
    "ancho_deseado": 180,
    "separacion_derecha": 90,
    "separacion_inferior": 100,
    "variabilidad_horizontal_pct": 50,
    "variabilidad_vertical_pct": 20,
    "variabilidad_giro": 5,
    "rotacion_base": 0,
}

# Umbrales para detección de cada escenario (en puntos, aproximación de A4)
UMBRAL_A4_ANCHO = 595
UMBRAL_A4_ALTO = 842
MARGEN_ERROR = 50  # Tolerancia para considerar la página como A4


def detectar_escenario(page_width, page_height):
    """
    Devuelve el escenario (diccionario) que corresponde
    según las dimensiones de la página.
    """
    # A4 Vertical: ancho aproximado 595, alto 842 y orientación vertical.
    if (
        abs(page_width - UMBRAL_A4_ANCHO) <= MARGEN_ERROR
        and abs(page_height - UMBRAL_A4_ALTO) <= MARGEN_ERROR
        and page_width < page_height
    ):
        return escenario_1

    # A4 Horizontal: ancho aproximado 842, alto 595 y orientación horizontal.
    if (
        abs(page_width - UMBRAL_A4_ALTO) <= MARGEN_ERROR
        and abs(page_height - UMBRAL_A4_ANCHO) <= MARGEN_ERROR
        and page_width > page_height
    ):
        return escenario_2

    # Caso de hojas grandes: usamos escenario_3 y ajustamos la orientación según dimensiones.
    escenario = escenario_3.copy()  # Hacemos una copia para no modificar el original.
    if page_width > page_height:
        escenario["orientacion"] = "horizontal"
    else:
        escenario["orientacion"] = "vertical"
    return escenario


# ==========================================================
#   FUNCIONES PARA CALCULAR LA POSICIÓN DEL SELLO
# ==========================================================
def colocar_sello_vertical(
    rect_pagina,
    nuevo_w,
    nuevo_h,
    separacion_derecha,
    separacion_inferior,
    offset_x,
    offset_y,
):
    """
    Posicionamiento clásico para páginas verticales:
    Se ubica el sello en la esquina inferior derecha (cerca de (rect.x1, rect.y1)).
    """
    x0 = rect_pagina.x1 - nuevo_w - separacion_derecha + offset_x
    y0 = rect_pagina.y1 - nuevo_h - separacion_inferior + offset_y
    x1 = rect_pagina.x1 - separacion_derecha + offset_x
    y1 = rect_pagina.y1 - separacion_inferior + offset_y
    return fitz.Rect(x0, y0, x1, y1)


def colocar_sello_horizontal(
    rect_pagina,
    nuevo_w,
    nuevo_h,
    separacion_derecha,
    separacion_inferior,
    offset_x,
    offset_y,
):
    """
    Para páginas horizontales se considera que la orientación de lectura
    tiene el 'abajo' en el borde inferior (y=rect.y0) y la 'derecha' en x=rect.x1.
    Se intercambian los valores:
      - Para desplazar horizontalmente se usa separacion_inferior.
      - Para desplazar verticalmente se usa separacion_derecha.
    """
    x0 = rect_pagina.x1 - nuevo_w - separacion_inferior + offset_x
    y0 = rect_pagina.y0 + separacion_derecha + offset_y
    x1 = x0 + nuevo_w
    y1 = y0 + nuevo_h
    return fitz.Rect(x0, y0, x1, y1)


# ==========================================================
#            CÓDIGO PRINCIPAL
# ==========================================================
def sellar_pdfs():
    # Parámetros de entrada
    carpeta_pdfs = "docs/"  # Carpeta que contiene los PDFs a procesar
    sello_path = "sello.png"  # Ruta de la imagen del sello

    # Parámetros de salida
    carpeta_salida = "sellados/"  # Carpeta donde se guardarán los PDFs sellados
    os.makedirs(carpeta_salida, exist_ok=True)

    # Obtener la lista de archivos PDF en la carpeta
    pdf_files = [f for f in os.listdir(carpeta_pdfs) if f.lower().endswith(".pdf")]

    for pdf_file in pdf_files:
        pdf_path = os.path.join(carpeta_pdfs, pdf_file)
        print(f"\nProcesando {pdf_path}...")

        # Abrir el documento PDF
        doc = fitz.open(pdf_path)

        for num_pagina, pagina in enumerate(doc, start=1):
            rect_pagina = pagina.rect
            page_width, page_height = rect_pagina.width, rect_pagina.height

            # Detectar el escenario según dimensiones/orientación
            escenario = detectar_escenario(page_width, page_height)
            print(
                f"  Página {num_pagina}: {escenario['nombre']} "
                f"(w={page_width:.0f}, h={page_height:.0f}, orientacion={escenario['orientacion']})"
            )

            # Extraer parámetros del escenario
            orientacion = escenario["orientacion"]
            ancho_deseado = escenario["ancho_deseado"]
            separacion_derecha = escenario["separacion_derecha"]
            separacion_inferior = escenario["separacion_inferior"]
            variabilidad_horizontal_pct = escenario["variabilidad_horizontal_pct"]
            variabilidad_vertical_pct = escenario["variabilidad_vertical_pct"]
            variabilidad_giro = escenario["variabilidad_giro"]
            rotacion_base = escenario["rotacion_base"]

            # Abrir la imagen del sello
            img = Image.open(sello_path).convert("RGBA")

            # Calcular la rotación total: rotación_base + rotación aleatoria
            angulo_aleatorio = random.uniform(-variabilidad_giro, variabilidad_giro)
            angulo_total = rotacion_base + angulo_aleatorio
            print(
                f"    Rotación base: {rotacion_base}°, aleatoria: {angulo_aleatorio:.2f}°, total: {angulo_total:.2f}°"
            )

            # Rotar la imagen
            sello_rotado = img.rotate(angulo_total, resample=Image.BICUBIC, expand=True)
            w_img, h_img = sello_rotado.size

            # Escalar la imagen para ajustar el ancho deseado
            factor = ancho_deseado / w_img
            nuevo_w = int(w_img * factor)
            nuevo_h = int(h_img * factor)
            sello_redimensionado = sello_rotado.resize(
                (nuevo_w, nuevo_h), resample=Image.LANCZOS
            )

            # Calcular offsets aleatorios
            offset_x = random.uniform(-variabilidad_horizontal_pct / 100 * nuevo_w, 0)
            offset_y = random.uniform(-variabilidad_vertical_pct / 100 * nuevo_h, 0)

            # Seleccionar la fórmula de colocación según la orientación
            if orientacion == "horizontal":
                sello_rect = colocar_sello_horizontal(
                    rect_pagina,
                    nuevo_w,
                    nuevo_h,
                    separacion_derecha,
                    separacion_inferior,
                    offset_x,
                    offset_y,
                )
            else:
                sello_rect = colocar_sello_vertical(
                    rect_pagina,
                    nuevo_w,
                    nuevo_h,
                    separacion_derecha,
                    separacion_inferior,
                    offset_x,
                    offset_y,
                )

            # Convertir la imagen a bytes en PNG sin compresión adicional
            buffer = io.BytesIO()
            sello_redimensionado.save(
                buffer, format="PNG", compress_level=0, optimize=False
            )
            buffer.seek(0)
            img_bytes = buffer.getvalue()

            # Crear el objeto Pixmap e insertarlo en la página
            pix = fitz.Pixmap(img_bytes)
            pagina.insert_image(sello_rect, pixmap=pix)

        # Guardar el PDF sellado
        salida_pdf = os.path.join(
            carpeta_salida, f"{os.path.splitext(pdf_file)[0]}.pdf"
        )
        doc.save(salida_pdf)
        doc.close()
        print(f"Guardado: {salida_pdf}")


if __name__ == "__main__":
    sellar_pdfs()
