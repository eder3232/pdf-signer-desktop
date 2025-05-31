# Guía de Desarrollo para la Aplicación de Firmado de PDF

## 1. Filosofía de Desarrollo

### Paradigma:

- **Programación Modular y Orientada a Objetos**

  - Cada funcionalidad se encapsula en clases o funciones puramente responsables.
  - El sistema está diseñado para tener **baja acoplamiento y alta cohesión**.
  - Se favorece el uso de **inyección de dependencias** y **funciones puras** donde sea posible.

### Principios:

- **Separación de responsabilidades**
- **Testabilidad**: todo componente debe tener entrada/salida bien definida.
- **Evitar efectos colaterales**: módulos no deben afectar estados globales.
- **Independencia de interfaz gráfica y lógica de negocio**

---

## 2. Estructura de Carpetas del Proyecto

```
firmador_pdf/
├── app/                          # Lógica principal y componentes
│   ├── core/                     # Funciones de negocio
│   │   ├── pdf_handler.py        # Abrir, leer, modificar PDF
│   │   ├── signature_manager.py # Lógica de colocación de firmas
│   │   ├── preview_generator.py # Renderizar previsualizaciones
│   │   └── config_manager.py    # Manejo de configuración local JSON
│   ├── ui/                       # Interfaz gráfica (PyQt)
│   │   ├── main_window.py       # Ventana principal
│   │   ├── signature_panel.py   # Panel lateral de configuración
│   │   ├── canvas_view.py       # Vista de página PDF interactiva
│   │   └── dialogs.py           # Diálogos y popups
│   ├── models/                  # Clases de datos
│   │   ├── document_model.py    # Representación de documentos
│   │   ├── signature_model.py   # Representación de una firma
│   │   └── config_model.py      # Configuraciones persistentes
│   └── utils/                   # Utilidades genéricas
│       ├── units.py             # Conversión de cm a puntos PDF
│       └── validators.py        # Validaciones de coordenadas, tamaños
├── tests/                       # Pruebas unitarias y de integración
│   ├── test_pdf_handler.py
│   ├── test_signature_manager.py
│   └── ...
├── resources/                   # Imágenes, archivos de prueba, etc.
├── main.py                      # Punto de entrada de la aplicación
├── config.json                  # Configuración persistente
├── requirements.txt
└── README.md
```

---

## 3. Orden de Desarrollo de Módulos

### Etapa 1: Backend funcional aislado

1. `pdf_handler.py`

   - Apertura de PDF
   - Obtener número y dimensión de hojas
   - Extraer páginas específicas

2. `signature_manager.py`

   - Insertar imagen PNG en coordenadas dadas
   - Controlar tamaño y rotación en puntos

3. `config_manager.py`

   - Leer y escribir archivos JSON con configuraciones de usuario

4. `units.py` y `validators.py`

   - Validaciones de coordenadas y métricas imprimibles

### Etapa 2: Vista previa

5. `preview_generator.py`

   - Renderizar una hoja PDF como imagen con firmas superpuestas

### Etapa 3: Modelado de datos

6. `signature_model.py`, `document_model.py`, `config_model.py`

   - Usar `@dataclass` o `pydantic` para validación de modelos

### Etapa 4: Interfaz gráfica

7. `main_window.py`

   - Carga de documentos y firmas
   - Integración de los paneles

8. `canvas_view.py`

   - Vista interactiva para mover/redimensionar firmas

9. `signature_panel.py`

   - Configuración detallada de cada firma (inputs numéricos y visuales)

---

## 4. Estrategia de Pruebas

- Cada módulo principal tendrá su archivo `test_*.py` asociado
- Pruebas automatizadas en:

  - Inserción de firmas en PDFs de diferentes tamaños
  - Validación de coordenadas fuera de margen
  - Carga/lectura de configuración JSON

- Las funciones deben ser **testables de forma aislada**

---

## 5. Características Adicionales Clave

- **Modo Debug**: consola o log para verificar coordenadas y valores cargados.
- **Modo Demo/Test**: usar PDF de prueba con configuraciones preestablecidas.
- **Internacionalización** (i18n) con sistema de traducciones básico (si se proyecta crecimiento).
- **Licencia y versión del software** visible en la UI.

---

## 6. Criterios de Terminación por Módulo

- PDF exportado visualmente igual a la previsualización.
- Coordinadas de firma coinciden con configuración ingresada.
- Configuración persistente cargada correctamente al abrir.
- No se lanza excepción al cargar archivos válidos.
- Aplicación empaquetada correctamente como `.exe` portable.

---

## 7. Futuro: Simulador de escaneo (Post-firma)

- Se añadirá como módulo `scan_simulator.py`
- Se aplicará a la ruta del PDF final generada
- Debe estar desacoplado de la lógica de firma
- Permitido aplicar efectos tipo Pillow: ruido, blur, skew, etc.

---

## 8. Empaquetado

- El script `main.py` debe ser el entry point.
- Uso de `PyInstaller` para generar ejecutables:

  - `pyinstaller --onefile --windowed main.py`

- Icono, nombre del producto y versión configurables en el `.spec`

---

Esta estructura modular permite que cada programador pueda trabajar en un módulo sin afectar el resto, garantizando una mayor escalabilidad, mantenibilidad y facilidad para aplicar pruebas unitarias y de integración.
