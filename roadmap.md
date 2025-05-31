# Roadmap para la Aplicación de Firmado de PDF

A continuación encontrarás un roadmap organizado en fases, cada una con objetivos claros, tareas específicas y entregables. Este plan asume un equipo pequeño o un solo desarrollador; ajústalo según tu disponibilidad y ritmo de trabajo.

---

## Fase 0: Preparativos Iniciales

**Objetivo:** Sentar las bases del proyecto, configurar el repositorio, el entorno de desarrollo y la integración continua.

1. **Crear el repositorio y la estructura básica**

   - Inicia un nuevo repositorio (por ejemplo en GitHub, GitLab o Bitbucket) con el nombre `firmador_pdf`.
   - Agrega un `.gitignore` (Python, PyQt, PyInstaller) y un `README.md` con descripción general del proyecto.
   - Crear la estructura de carpetas vacía siguiendo el esquema:
     ```text
     firmador_pdf/
     ├── app/
     │   ├── core/
     │   ├── ui/
     │   ├── models/
     │   └── utils/
     ├── tests/
     ├── resources/
     ├── main.py
     ├── config.json
     └── requirements.txt
     ```
   - Empuja el commit inicial al repositorio con la estructura vacía y el README.

2. **Configurar entorno virtual y dependencias básicas**

   - Crea un entorno virtual:
     ```bash
     python -m venv venv
     ```
   - Activa el entorno:
     - Linux/macOS: `source venv/bin/activate`
     - Windows: `venv\Scripts\activate`
   - Crea un archivo `requirements.txt` con las dependencias mínimas:
     ```text
     PyPDF2>=2.0.0
     Pillow>=9.0.0
     PyQt5>=5.15.0
     pydantic>=1.10.0
     pytest>=7.0.0
     ```
   - Instala dependencias:
     ```bash
     pip install -r requirements.txt
     ```
   - Verifica que `python --version` y `pip list` estén correctos.

3. **Configurar integración continua (CI) y calidad de código**

   - Agrega un pipeline básico (GitHub Actions, GitLab CI, etc.) que ejecute:
     - `pip install -r requirements.txt`
     - `pytest --maxfail=1 --disable-warnings -q`
   - Incluye un linter (por ejemplo, Flake8 o pylint). En el archivo de CI (por ejemplo, `.github/workflows/ci.yml`), sumar:
     ```yaml
     - name: Lint with flake8
       run: |
         pip install flake8
         flake8 app/
     ```
   - Asegura que cada push ejecute pruebas y linter antes de fusionar al branch principal.

4. **Configurar el archivo de configuración general**

   - Crea un `config.json` con estructura mínima, por ejemplo:
     ```json
     {
       "default_signature_size_cm": 4.0,
       "default_rotation_deg": 0,
       "recent_files": []
     }
     ```
   - Este archivo servirá para guardar preferencias del usuario (tamaño de firma por defecto, rutas recientes, idioma UI, etc.).

---

## Fase 1: Módulos de Backend Aislado

**Objetivo:** Implementar la lógica de negocio para abrir, leer y modificar PDFs; manejar la inserción de firmas y la configuración sin UI.

### 1.1 `app/core/pdf_handler.py`

- **Tarea 1.1.1:** Creación de la clase `PDFHandler`

  - Método `open_pdf(path: str) -> PdfReader`
  - Método `get_page_count(reader: PdfReader) -> int`
  - Método `get_page_size(reader: PdfReader, page_number: int) -> Tuple[float, float]`
  - Método `extract_page(reader: PdfReader, page_number: int) -> PdfReader` (para procesar página individual si se requiere).

- **Tarea 1.1.2:** Función de guardado

  - Método `save_pdf(reader: PdfWriter, output_path: str)`.
  - Verificar que si `output_path` ya existe, se sobreescribe tras confirmación o según configuración en `config.json`.

- **Pruebas unitarias en `tests/test_pdf_handler.py`**
  - Crear PDFs de prueba en `resources/` (1, 2 y 3 páginas).
  - Verificar que:
    - `open_pdf` abra correctamente cada archivo.
    - `get_page_count` devuelve el número correcto de páginas.
    - `get_page_size` arroje dimensiones esperadas.
    - `save_pdf` genere un nuevo archivo con el mismo contenido básico.

**Entregable:** `app/core/pdf_handler.py` con pruebas que cubran apertura, conteo de páginas y guardado.

---

### 1.2 `app/core/signature_manager.py`

- **Tarea 1.2.1:** Definir la clase `SignatureManager`

  - Constructor que reciba una instancia de `PDFHandler` (inyección de dependencias).
  - Método:
    ```python
    place_signature(
      reader: PdfReader,
      image_path: str,
      page_number: int,
      x_pts: float,
      y_pts: float,
      width_pts: float,
      height_pts: float,
      rotation_deg: float
    ) -> PdfWriter
    ```
    - Usa `Pillow` y `PyPDF2` para insertar el PNG en las coordenadas dadas.
    - Control de transparencia (alpha) si el PNG la posee.
    - Rotación: gira la imagen antes de pegarla.

- **Tarea 1.2.2:** Función para procesar múltiples páginas

  - Método:
    ```python
    sign_multiple_pages(
      input_path: str,
      image_path: str,
      output_path: str,
      pages_to_skip: List[int],
      x_cm: float,
      y_cm: float,
      width_cm: float,
      height_cm: float,
      rotation_deg: float
    )
    ```
    - Flujo interno:
      1. Abrir PDF con `PDFHandler`.
      2. Iterar cada página:
         - Si el número está en `pages_to_skip`, copiar tal cual.
         - Si no, llamar a `place_signature`.
      3. Guardar PDF final con `save_pdf`.

- **Pruebas unitarias en `tests/test_signature_manager.py`**
  - Insertar firma en página 1 de un PDF de 2 páginas.
  - Verificar que la página 2 (skippeada) permanezca idéntica.
  - Comprobar que la dimensión de la firma en el PDF resultante coincida con la solicitada (utilizar inspección de bounding box, hash, u otra técnica).

**Entregable:** `app/core/signature_manager.py` con pruebas validadas.

---

### 1.3 `app/core/config_manager.py`

- **Tarea 1.3.1:** Crear la clase `ConfigManager`

  - Métodos:
    - `load_config() -> Dict[str, Any]`
    - `save_config(data: Dict[str, Any])`
    - `get(key: str, default: Any) -> Any`
    - `set(key: str, value: Any) -> None`
  - Validación básica de claves esperadas (puede usarse `pydantic` o validaciones manuales).

- **Tarea 1.3.2:** Integrar con `SignatureManager` y `PreviewGenerator`

  - Si el usuario no especifica tamaños/rotación, tomar valores por defecto de `config.json`.
  - Guardar “ultimas rutas usadas” en `recent_files`.

- **Pruebas unitarias en `tests/test_config_manager.py`**
  - Cargar un JSON de prueba en `resources/` y verificar lectura correcta.
  - Modificar un valor y guardarlo en un archivo temporal; leer luego para comprobar persistencia.

**Entregable:** `app/core/config_manager.py` interoperable con módulos anteriores.

---

### 1.4 `app/utils/units.py` y `app/utils/validators.py`

- **Tarea 1.4.1 (`units.py`):**

  - Función `cm_to_points(cm: float) -> float` (1 cm ≈ 28.3465 puntos PDF).
  - Función `points_to_cm(pts: float) -> float`.
  - (Opcional) Conversión de pulgadas a puntos u otras unidades.

- **Tarea 1.4.2 (`validators.py`):**

  - Función `validate_coordinates(
  x_pts: float,
  y_pts: float,
  page_width_pts: float,
  page_height_pts: float
) -> None`
    - Lanza excepción si las coordenadas están fuera del área imprimible.
  - Función `validate_size(
  width_pts: float,
  height_pts: float,
  page_width_pts: float,
  page_height_pts: float
) -> None`
    - Verificar que la firma no exceda márgenes. Permitir tolerancia mínima.

- **Pruebas unitarias en `tests/test_units_validators.py`**
  - Probar conversiones cm ↔ pts con valores conocidos.
  - Comprobar que `validate_coordinates` valida correctamente para valores válidos e inválidos.

**Entregable:** `app/utils/units.py` y `validators.py` listos para usar.

---

## Fase 2: Generar Vista Previa

**Objetivo:** Ofrecer una representación visual de cómo quedará la página firmada antes de modificar el PDF original.

### 2.1 `app/core/preview_generator.py`

- **Tarea 2.1.1:** Implementar la clase `PreviewGenerator`

  - Constructor recibe instancias de `PDFHandler` y `SignatureManager`.
  - Método:
    ```python
    render_page_preview(
      input_path: str,
      page_number: int,
      image_path: str,
      x_cm: float,
      y_cm: float,
      width_cm: float,
      height_cm: float,
      rotation_deg: float
    ) -> PIL.Image
    ```
    - Flujo interno:
      1. Abrir el PDF y extraer la página con `PDFHandler`.
      2. Convertir la página a imagen:
         - Usar `pdf2image` o render integrado en PyQt (si se prefiere).
         - Obtener un objeto `PIL.Image`.
      3. Cargar el PNG de la firma con `Pillow`.
      4. Convertir `cm` a puntos, luego a píxeles (según resolución de la imagen de la página).
      5. Dibujar la firma sobre la imagen de la página (aplicar rotación y mantener transparencia).
      6. Devolver el `PIL.Image` resultante.

- **Tarea 2.1.2:** Opción para exportar la vista previa a un archivo temporal:

  - Ejemplo: `temp/preview_page_1.png`.

- **Pruebas unitarias en `tests/test_preview_generator.py`**
  - Usar un PDF de prueba de una página blanca.
  - Generar previsualización y verificar que:
    - El tamaño de la imagen coincide con la resolución de la página.
    - La firma aparece en la posición aproximada (uso de comparación de píxeles o histograma).
  - Validar que no falle con PDFs horizontales o de tamaño carta/oficio.

**Entregable:** `app/core/preview_generator.py` funcional con pruebas que aseguren la correcta renderización.

---

## Fase 3: Modelado de Datos

**Objetivo:** Definir estructuras claras para representar documentos, firmas y configuración; facilitar intercambio entre módulos y validaciones.

### 3.1 `app/models/signature_model.py`

- **Tarea 3.1.1:** Crear la clase `SignatureModel`

  - Atributos:
    - `image_path: str`
    - `page_number: int`
    - `x_cm: float`
    - `y_cm: float`
    - `width_cm: float`
    - `height_cm: float`
    - `rotation_deg: float`
  - Validación con `pydantic.BaseModel` o `@dataclass` + validadores manuales:
    - Página ≥ 1 y ≤ total de páginas.
    - Tamaños positivos.
    - Rotación entre 0 y 360.
  - Métodos auxiliares:
    - `to_points(units_converter: Callable) -> Dict[str, float]`  
      Convierte `cm` → `pts` y devuelve `{"x_pts": ..., "y_pts": ..., "width_pts": ..., "height_pts": ...}`.
    - `to_dict() -> Dict[str, Any]`  
      Para serializar/guardar en JSON.

- **Pruebas unitarias en `tests/test_signature_model.py`**
  - Crear un `SignatureModel` con valores inválidos (página negativa, tamaño cero) y verificar que lance excepción.
  - Verificar que `to_points()` funcione correctamente usando un conversor ficticio (`lambda cm: cm * 28.3465`).

---

### 3.2 `app/models/document_model.py`

- **Tarea 3.2.1:** Clase `DocumentModel`

  - Atributos:
    - `path: str`
    - `page_count: int`
    - `page_sizes: List[Tuple[float, float]]`
  - Método de fábrica:
    ```python
    @classmethod
    def load(cls, path: str, pdf_handler: PDFHandler) -> DocumentModel:
        reader = pdf_handler.open_pdf(path)
        page_count = pdf_handler.get_page_count(reader)
        page_sizes = [
            pdf_handler.get_page_size(reader, i)
            for i in range(page_count)
        ]
        return cls(path=path, page_count=page_count, page_sizes=page_sizes)
    ```

- **Pruebas unitarias en `tests/test_document_model.py`**
  - Cargar un PDF real y verificar que `page_count` coincide con el documento.
  - Verificar que `page_sizes` reflejen dimensiones en puntos correctas.

---

### 3.3 `app/models/config_model.py`

- **Tarea 3.3.1:** Clase `ConfigModel`

  - Atributos basados en `config.json`:
    - `default_signature_size_cm: float`
    - `default_rotation_deg: float`
    - `recent_files: List[str]`
    - `language: str`
  - Validación de valores (tamaños positivos, rotación entre 0–360).
  - Métodos:
    - `@classmethod load_from_file(cls, path: str) -> ConfigModel`
    - `save_to_file(self, path: str) -> None`

- **Pruebas unitarias en `tests/test_config_model.py`**
  - Intentar cargar un JSON mal formado y verificar que falle.
  - Cargar un JSON válido y comprobar que los atributos coincidan.

---

## Fase 4: Interfaz Gráfica (PyQt)

**Objetivo:** Construir la capa de presentación que permita la interacción del usuario sin acoplar lógica de negocio.

### 4.1 `app/ui/main_window.py`

- **Tarea 4.1.1:** Crear la ventana principal (`MainWindow`)

  - Hereda de `QMainWindow`.
  - Elementos:
    - Barra de menú con opciones:
      - **Archivo → Abrir PDF**
      - **Archivo → Guardar PDF firmado**
      - **Archivo → Preferencias**
      - **Archivo → Salir**
    - Panel lateral/dock para `SignaturePanel`.
    - Área central donde se incrusta `CanvasView` para presentar la página actual.
    - Barra de estado para mensajes de validación (e.g., “Firma posicionada fuera de rango”).

- **Tarea 4.1.2:** Conectar acciones de menú

  - **Abrir PDF**:
    - Mostrar `QFileDialog.getOpenFileName`.
    - Cargar `DocumentModel`.
    - Mostrar página 1 en `CanvasView`.
  - **Guardar PDF firmado**:
    - Recopilar todas las firmas definidas.
    - Llamar a `SignatureManager.sign_multiple_pages(...)`.
    - Mostrar un cuadro de diálogo de éxito o error.
  - **Preferencias**:
    - Mostrar un diálogo modal (`ConfigDialog`) para editar `config.json`.
  - **Salir**:
    - Cerrar la aplicación.

- **Pruebas manuales** (GUI):
  - Probar apertura de PDF, navegar entre páginas, definir y visualizar firmas, guardar PDF final.
  - Verificar mensajes de error en la barra de estado cuando las coordenadas de firma sean inválidas.

---

### 4.2 `app/ui/canvas_view.py`

- **Tarea 4.2.1:** Crear la clase `CanvasView`

  - Hereda de `QGraphicsView` o `QWidget` personalizado.
  - Funcionalidades:
    - Cargar página actual como imagen (usar `PreviewGenerator` o render en PyQt).
    - Mostrar cada firma como un `QGraphicsPixmapItem` dentro de un `QGraphicsScene`.
    - Permitir:
      - Arrastrar/mover firmas.
      - Redimensionar firmas (mostrar asas).
      - Rotar (opcional: con un controlador en el panel lateral).
    - Zoom y panorámica con la rueda del ratón.

- **Tarea 4.2.2:** Eventos clave

  - `mousePressEvent`: detectar clic en firma o en página.
  - `mouseMoveEvent`: mover firma seleccionada.
  - `mouseReleaseEvent`: guardar posición final en el `SignatureModel`.
  - Doble clic en página:
    - Abrir `NewSignatureDialog` para añadir nueva firma (pedir datos iniciales: ruta PNG, página, tamaño, rotación).

- **Pruebas manuales** (GUI):
  - Agregar varias firmas en la misma página y en páginas distintas.
  - Verificar que no se permita posicionar una firma fuera de los márgenes (usar `validators.py` para validación en tiempo real).

---

### 4.3 `app/ui/signature_panel.py`

- **Tarea 4.3.1:** Crear la clase `SignaturePanel`

  - Hereda de `QWidget`.
  - Componentes:
    - `QListWidget` o `QTreeWidget` para mostrar todas las firmas definidas.
      - Cada ítem muestra: número de página, tamaño en cm y miniatura (opcional).
    - Botones:
      - **Añadir**
      - **Editar**
      - **Eliminar**
    - Formularios con campos numéricos (`QDoubleSpinBox`) para:
      - `x_cm`
      - `y_cm`
      - `width_cm`
      - `height_cm`
      - `rotation_deg`
    - Botón **Previsualizar** que genera y muestra la vista rápida en `CanvasView`.

- **Tarea 4.3.2:** Integración con el modelo

  - Al seleccionar un ítem en la lista:
    - Cargar sus valores en los `SpinBox`.
    - Emplear señales/slots para que, al modificar cualquier `SpinBox`, se emita una señal que haga que `CanvasView` re-renderice la firma en su nueva posición.
  - Botón **Añadir**:
    - Crea un nuevo `SignatureModel` con valores por defecto obtenidos de `ConfigManager`.
    - Lo agrega al listado y emite señal para render en `CanvasView`.

- **Pruebas manuales** (GUI):
  - Añadir/eliminar firmas mediante el panel y verificar que `CanvasView` actualice.
  - Editar valores numéricos y comprobar la actualización en tiempo real de la posición/tamaño de la firma.

---

### 4.4 `app/ui/dialogs.py`

- **Tarea 4.4.1:** Diálogo de “Configurar Preferencias” (`ConfigDialog`)

  - Hereda de `QDialog`.
  - Campos:
    - `default_signature_size_cm` (`QDoubleSpinBox`)
    - `default_rotation_deg` (`QDoubleSpinBox`)
    - `language` (`QComboBox` con opciones “es”/“en”)
  - Botones: **Guardar** y **Cancelar**.
    - Al presionar **Guardar**, invocar `ConfigManager.save_config(...)`.

- **Tarea 4.4.2:** Diálogo de “Nueva Firma” (`NewSignatureDialog`)

  - Hereda de `QDialog`.
  - Solicita:
    - Ruta del archivo PNG (`QFileDialog` para seleccionar).
    - Página de destino (`QSpinBox` con rango 1…N).
    - Tamaño inicial (`QDoubleSpinBox` para ancho y alto en cm; valores por defecto de `ConfigModel`).
    - Rotación inicial (`QDoubleSpinBox` en grados; valor por defecto de `ConfigModel`).
  - Botones: **Aceptar** y **Cancelar**.
    - Al presionar **Aceptar**, crea un `SignatureModel` y emite señal para que `SignaturePanel` lo agregue.

- **Pruebas manuales** (GUI):
  - Verificar que los diálogos abran y cierren correctamente.
  - Asegurar que al guardar preferencias, el archivo `config.json` se actualice.
  - Crear una nueva firma con el diálogo y ver que aparezca en la lista y en la vista previa.

---

## Fase 5: Estrategia de Pruebas (Unitarias y de Integración)

**Objetivo:** Garantizar que cada módulo funcione aisladamente y en conjunto; automatizar la mayor parte de las pruebas.

1. **Cobertura mínima por módulo (tests unitarios):**

   - `pdf_handler.py` → `tests/test_pdf_handler.py`
   - `signature_manager.py` → `tests/test_signature_manager.py`
   - `config_manager.py` → `tests/test_config_manager.py`
   - `units.py` y `validators.py` → `tests/test_units_validators.py`
   - `preview_generator.py` → `tests/test_preview_generator.py`
   - Modelos (`signature_model.py`, `document_model.py`, `config_model.py`) → cada uno en su respectivo test.

2. **Pruebas de integración (end-to-end para backend):**

   - Crear `tests/test_end_to_end_signing.py`.
     - Usar un PDF de prueba y un PNG de firma.
     - Llamar a `sign_multiple_pages(...)`.
     - Verificar:
       - Número de páginas intacto.
       - Páginas skippeadas idénticas (comparar hash o checksum).
       - Páginas firmadas contienen la imagen en la posición solicitada.
   - Incluir test para un PDF con páginas horizontales y verticales.

3. **Automatización en CI:**
   - Agregar badge de **coverage** en el `README.md`.
   - Configurar pipeline para:
     - `pytest --cov=app`
     - Linter (flake8/pylint).
     - Opcional: `mypy --strict` si se adopta tipado estático.

---

## Fase 6: Empaquetado y Distribución

**Objetivo:** Convertir la aplicación en un ejecutable independiente y documentar su uso.

1. **Crear script de entry point (`main.py`):**

   ```python
   import sys
   from PyQt5.QtWidgets import QApplication
   from app.ui.main_window import MainWindow
   from app.core.config_manager import ConfigManager

   def main():
       config = ConfigManager().load_config()
       app = QApplication(sys.argv)
       window = MainWindow(config)
       window.show()
       sys.exit(app.exec_())

   if __name__ == "__main__":
       main()
   ```

## Fase 6: Empaquetado y Distribución

**Objetivo:** Convertir la aplicación en un ejecutable independiente y documentar su uso.

1. **Crear script de entry point (`main.py`)**

   ```python
   import sys
   from PyQt5.QtWidgets import QApplication
   from app.ui.main_window import MainWindow
   from app.core.config_manager import ConfigManager

   def main():
       config = ConfigManager().load_config()
       app = QApplication(sys.argv)
       window = MainWindow(config)
       window.show()
       sys.exit(app.exec_())

   if __name__ == "__main__":
       main()
   Configuración de PyInstaller
   ```

Generar un archivo .spec o ejecutar directamente:

bash
Copiar
Editar
pyinstaller --onefile --windowed --name firmador_pdf main.py
En el .spec, incluir:

Icono del programa (resources/icon.ico o similar).

Carpeta resources/ como datos adicionales.

Metadata: nombre del producto y versión (tomar de config.json o de un setup.py si se crea).

Probar localmente el ejecutable resultante:

Verificar que no requiera Python instalado.

Abrir la ventana principal y comprobar funcionalidades básicas (carga de PDF, firma, guardado).

Documento de usuario final (docs/USER_GUIDE.md o sección en README.md)

Incluir capturas de pantalla de la UI.

Describir pasos para instalar (o ejecutar el .exe).

Explicar cómo:

Abrir un PDF.

Añadir una firma.

Moverla y redimensionarla.

Guardar el PDF firmado.

Añadir solución de problemas comunes (por ejemplo, “Si al abrir un PDF aparece error, verificar que el archivo no esté en uso por otro programa”).

Versionado Semántico y Lanzamiento

Cuando la funcionalidad básica esté completa y probada, taguear en Git con v1.0.0.

Adjuntar binarios (Windows, macOS, Linux si es posible) en la sección de Releases de la plataforma de hosting (GitHub/GitLab/Bitbucket).

Fase 7: Características Adicionales y Extensiones Futuras
Objetivo: Planificar funcionalidades que mejoren la experiencia y robustez del software.

Modo Debug / Logs Detallados

Configurar el módulo logging de Python:

Leer nivel de log (DEBUG, INFO, WARNING, ERROR) desde config.json.

Registrar en consola y/o archivo eventos clave: apertura de PDF, posición de firma, guardado, errores.

Mostrar mensajes de diagnóstico en la barra de estado de la UI cuando sea pertinente.

Modo Demo/Test

Incluir en resources/ un PDF y un PNG de firma predeterminados.

Añadir un botón en la UI “Cargar Demo” que:

Abra estos recursos incluidos.

Configure automáticamente una firma de ejemplo en la posición central de la primera página para que el usuario vea rápido cómo funciona.

Internacionalización (i18n)

Crear carpetas de recursos:

pgsql
Copiar
Editar
i18n/
├── en.json
└── es.json
Cada archivo JSON contendrá pares clave → texto traducido, por ejemplo:

json
Copiar
Editar
{
"menu_file": "Archivo",
"menu_open": "Abrir PDF",
"menu_save": "Guardar PDF firmado",
"btn_add_signature": "Añadir Firma",
...
}
En MainWindow, al iniciar, cargar el idioma según el valor language de ConfigModel.

Usar QtCore.QTranslator de PyQt para aplicar las traducciones en tiempo de ejecución.

Escáner Simulado (Post-firma)

Crear app/core/scan_simulator.py:

python
Copiar
Editar
from PIL import Image, ImageFilter, ImageOps

class ScanSimulator:
@staticmethod
def simulate_scan(input_image_path: str, output_image_path: str, intensity: float) -> None:
img = Image.open(input_image_path)
blurred = img.filter(ImageFilter.GaussianBlur(radius=intensity))
final = ImageOps.colorize(blurred.convert("L"), black="black", white="white")
final.save(output_image_path)
Integrar una opción en el menú principal “Aplicar efecto de escaneo” que:

Genere una imagen temporal del PDF firmado (por ejemplo, usando PreviewGenerator para cada página y luego combinándolas, o simplificar aplicando a una sola página de demostración).

Llame a ScanSimulator.simulate_scan(...).

Permita ajustar parámetros (porcentaje de ruido, desenfoque, ligero sesgo).

(Opcional) Extender para producir un PDF escaneado: convertir las imágenes resultantes de cada página de vuelta a PDF y combinar.

Generar Informes Automáticos de Auditoría

Crear app/core/audit_report.py:

python
Copiar
Editar
import json
import hashlib
from datetime import datetime

class AuditReport:
@staticmethod
def generate(
input*pdf_path: str,
output_pdf_path: str,
signatures: list[dict],
audit_folder: str = "resources/audit"
) -> None:
timestamp = datetime.now().strftime("%Y%m%d*%H%M%S")
report = {
"timestamp": timestamp,
"input*hash": AuditReport.\_compute_file_hash(input_pdf_path),
"output_hash": AuditReport.\_compute_file_hash(output_pdf_path),
"signatures": signatures
}
filename = f"{audit_folder}/audit*{timestamp}.json"
with open(filename, "w", encoding="utf-8") as f:
json.dump(report, f, indent=4)

    @staticmethod
    def _compute_file_hash(path: str) -> str:
        hasher = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

Integrar en la UI: después de guardar el PDF final, ofrecer un botón o diálogo “Generar informe de auditoría”.

El informe contendrá:

Fecha y hora de la firma.

Hash SHA-256 del PDF original y del PDF firmado.

Lista de firmas aplicadas con coordenadas (en cm y pts) y ruta de la imagen de firma.

Plugin o Módulo para Firmar con Certificado Digital (Futuro)

Diseñar una interfaz abstracta en app/core/certificate_signer.py:

python
Copiar
Editar
from abc import ABC, abstractmethod

class CertificateSigner(ABC):
@abstractmethod
def sign_pdf_with_certificate(
self,
input_pdf_path: str,
cert_path: str,
output_pdf_path: str,
password: str
) -> None:
"""
Firma el PDF usando un certificado digital.
Debe implementarse en una subclase concreta que utilice bibliotecas como python-pkcs11
o PyKCS11 para realizar la firma criptográfica.
"""
pass
En futuras versiones:

Implementar una clase PKCS11Signer(CertificateSigner) que cargue el módulo PKCS#11 y firme el PDF con un certificado almacenado en un token.

Ofrecer en la UI una opción “Firmar con Certificado Digital” que solicite:

Ruta al certificado (archivo .p12 o similar).

Contraseña del certificado.

Aplicar firma criptográfica al PDF (no solo superponer imagen).

Soporte para Múltiples Formatos de Imagen de Firma

Extender SignatureManager y PreviewGenerator para aceptar:

SVG (convertir a PNG internamente usando CairoSVG).

Otros formatos vectoriales.

Ajustar validaciones en validators.py para verificar formatos compatibles.

Permitir al usuario escoger el formato deseado en el diálogo “Nueva Firma”.

Fase 8: Mantenimiento y Mejora Continua
Objetivo: Asegurar que la aplicación se mantenga estable y se adapte a nuevas necesidades o correcciones de bugs.

Gestión de Issues y Branching

Definir un flujo Git estándar:

main o master: rama estable para lanzamientos.

develop: rama para integración de nuevas funcionalidades y fixes.

Branches de feature: feature/<nombre-feature>.

Branches de bugfix: bugfix/<descripcion-corta>.

Checklist para Pull Requests:

Código cubierto por pruebas unitarias.

Linter (flake8/pylint) sin errores.

Documentación actualizada (si aplica).

No se rompen funcionalidades existentes.

Monitoreo de Dependencias

Cada 3 meses (o antes de cada versión mayor), revisar actualizaciones de:

PyPDF2

Pillow

PyQt5

pydantic

pytest

Actualizar requirements.txt y corregir posibles breaking changes.

Recopilación de Feedback de Usuarios

Configurar un formulario (Google Forms, Typeform) o un issue template en el repositorio para:

Reportes de bugs.

Sugerencias de mejora.

Priorizar correcciones críticas (errores que impidan la firma) antes de incorporar nuevas funcionalidades.

Implementar Telemetría Opcional (Futuro)

Ofrecer al usuario la opción de “Enviar reporte de error” que:

Recopile logs y stack traces (respetando la privacidad; anonimizar información sensible).

Envíe la información a un servidor propio o a un servicio como Sentry.

Mostrar al usuario un diálogo que detalle la información que se enviará y solicite consentimiento.

Cronograma Sugerido (Ejemplo de 8 Semanas)
Semana Actividad Principal Entregable Esperado
1 Fase 0 (Repos y entorno, CI, README inicial) Repositorio con estructura, CI configurada, entorno virtual listo
2 Fase 1.1 (pdf_handler) + pruebas unitarias Módulo pdf_handler.py con tests exitosos
3 Fase 1.2 (signature_manager) + pruebas unitarias Módulo signature_manager.py con pruebas de inserción de firma
4 Fase 1.3 (config_manager) y Fase 1.4 (units/validators) config_manager.py, units.py, validators.py con tests
5 Fase 2 (preview_generator) + pruebas unitarias preview_generator.py funcional con pruebas
6 Fase 3 (modelos de datos) + pruebas unitarias Clases en app/models/ y pruebas correspondientes
7 Fase 4.1–4.3 (PyQt: main_window.py, canvas_view.py, signature_panel.py) UI básica operativa: carga PDF, agrega firma, previsualiza y guarda
8 Fase 6 (Empaquetado con PyInstaller + documentación) Ejecutable distribuible, guía de instalación y uso en README

Nota:

La Fase 5 (Pruebas de integración) debe alimentarse conforme se completen los módulos backend (desde la semana 3 en adelante).

Las funcionalidades de la Fase 7 se pueden planificar a partir de la semana 9 en adelante, según prioridades de usuario y disponibilidad de recursos.

Consejos Finales
Itera frecuentemente. Comienza con prototipos simples (por ejemplo, una PyQt window que solo cargue un PDF sin firma) para validar la arquitectura desde el inicio.

Documenta y comenta tu código. Usa docstrings en cada clase y método; facilitará el mantenimiento a futuro.

Mantén alta cohesión y bajo acoplamiento. Si un módulo crece demasiado, extráelo a un submódulo o crea servicios independientes.

Simplifica las primeras versiones. Por ejemplo, en la iteración inicial de UI, bastará con botones “Insertar firma” sin arrastrar ni redimensionar; luego agrega interactividad avanzada.

Organiza tareas en el repositorio (issues, milestones) para asignar cada fase o feature como una tarea con estados (“To Do”, “In Progress”, “Done”). Esto ayudará a visualizar el avance y priorizar el trabajo.

Con estos apartados desde la Fase 6 en adelante, podrás empaquetar, distribuir y mantener tu aplicación de firmado de PDF de manera profesional y escalable. ¡Adelante!
