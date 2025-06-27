# src/config.py

import os
from pathlib import Path

# --- RUTAS DE CARPETAS BASE ---
BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__))).parent
SRC_DIR = BASE_DIR / "src"
TEMPLATES_DIR = BASE_DIR / "templates"
DATA_DIR = BASE_DIR / "data"
PROCESSED_RECEIPTS_DIR = DATA_DIR / "processed_receipts"
PROCESSED_IMAGES_ARCHIVE_DIR = PROCESSED_RECEIPTS_DIR / "images_archive"
FEEDBACK_LOOP_DIR = DATA_DIR / "feedback_loop"
PROBABILISTIC_MODEL_PATH = DATA_DIR / "probabilistic_model.json"
INPUT_DIR = BASE_DIR / "input"
TEMP_DIR = BASE_DIR / "temp"
LOGS_DIR = BASE_DIR / "logs"

# Crear directorios si no existen al iniciar
for d in [TEMPLATES_DIR, PROCESSED_RECEIPTS_DIR, PROCESSED_IMAGES_ARCHIVE_DIR,
          FEEDBACK_LOOP_DIR, INPUT_DIR, TEMP_DIR, LOGS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# --- CONFIGURACIÓN DE LOGGING ---
LOG_FILE_PATH = LOGS_DIR / "system.log"
LOG_LEVEL = "INFO"  # DEBUG para depuración exhaustiva, INFO para producción.

# --- CONTROL DE ARCHIVOS TEMPORALES ---
CLEAN_TEMP_FILES = True  # Si es True, elimina la carpeta temp/<id_unico_imagen> al finalizar.
                        # Establece a False para DEPURAR y revisar preprocesamientos y recortes.

# --- CONFIGURACIÓN DE TESSERACT ---
TESSERACT_LANG = "spa"  # Idioma(s), ej. "spa", "eng", "spa+eng"
# PSM: Page Segmentation Mode (cómo Tesseract interpreta un bloque de texto)
TESSERACT_PSM_GENERAL_OCR = "3"
TESSERACT_PSM_LINE_OCR = "7"
TESSERACT_PSM_WORD_OCR = "8"
TESSERACT_PSM_SPARSE_TEXT_NO_RECEIPT = "11"  # Para la detección rápida de "no recibo" y ZOI dinámicas
TESSERACT_PSM_OSD_DETECTION = "12"  # Para detección de orientación (skew)
TESSERACT_OEM = "3"  # Default, basado en lo disponible (Tesseract + LSTM)

# --- UMBRALES PARA DIAGNÓSTICO DE IMAGEN ---
LAPLACIAN_VAR_HIGH = 1500   # Varianza Laplaciana > HIGH_VAR -> ALTA Nitidez
LAPLACIAN_VAR_MEDIUM = 800  # Varianza Laplaciana > MEDIUM_VAR -> MEDIA Nitidez
BRIGHTNESS_THRESHOLD_LOW = 70    # Promedio de píxeles < LOW -> Imagen oscura
BRIGHTNESS_THRESHOLD_HIGH = 180  # Promedio de píxeles > HIGH -> Imagen muy brillante
NOISE_THRESHOLD_HIGH = 20   # Desviación estándar alta en áreas uniformes -> Mucho ruido

# --- CONFIGURACIÓN PARA EL AUTO-APRENDIZAJE ---
MANUAL_FEEDBACK_CSV_FILE = FEEDBACK_LOOP_DIR / "manual_feedback.csv"
PROCESSED_FEEDBACK_ARCHIVE_DIR = FEEDBACK_LOOP_DIR / "processed_feedback_archive"
PROCESSED_FEEDBACK_ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

# --- REGLAS DE CLASIFICACIÓN DE DOCUMENTOS ("No Recibo") ---
PAYMENT_KEYWORDS = ["Pago Móvil", "Transferencia", "Monto", "Fecha", "Referencia", 
                   "C.I.", "RIF", "Bs", "Cédula", "Transf", "Movil", "Banco", "Cta", "Total"]
MIN_PAYMENT_KEYWORDS_MATCH = 2  # Cuántas palabras clave deben coincidir para considerarlo recibo
MIN_TEXT_AREA_RATIO_RECEIPT = 0.01  # Mínima proporción del área total cubierta por texto
MIN_IMAGE_DIMENSION = 200  # Mínima dimensión (ancho o alto) para una imagen válida
