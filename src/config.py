"""
Configuración del Sistema OCR v3.0
Parámetros optimizados para comprobantes de pago móvil
"""

import os
from pathlib import Path

# === DIRECTORIOS ===
BASE_DIR = Path(__file__).parent.parent
INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"
TEMP_DIR = BASE_DIR / "temp"
LOGS_DIR = BASE_DIR / "logs"

# === ARCHIVOS DE SALIDA ===
PREPROCESSED_IMAGE_NAME = "preprocessed_image.png"
DEBUG_IMAGE_NAME = "debug_extraction.png"
EXTRACTION_RESULT_FILE = "extraction_result.json"
OCR_DETAILS_FILE = "ocr_details.json"

# === CONFIGURACIÓN DE LOGGING ===
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# === PARÁMETROS DE CALIDAD DE IMAGEN ===
# Umbrales de nitidez (Varianza Laplaciana)
LAPLACIAN_VAR_HIGH = 500.0      # Imagen muy nítida
LAPLACIAN_VAR_MEDIUM = 100.0    # Imagen medianamente nítida
LAPLACIAN_VAR_LOW = 50.0        # Imagen borrosa

# Umbrales de brillo
BRIGHTNESS_THRESHOLD_HIGH = 180  # Imagen muy clara
BRIGHTNESS_THRESHOLD_LOW = 80    # Imagen muy oscura
BRIGHTNESS_THRESHOLD_DARK = 60   # Imagen extremadamente oscura (fondo negro)

# Umbrales de ruido
NOISE_THRESHOLD_HIGH = 15.0     # Mucho ruido
NOISE_THRESHOLD_MEDIUM = 8.0    # Ruido moderado

# === PARÁMETROS DE INVERSIÓN DE COLORES ===
# Para detectar fondos oscuros que necesitan inversión
DARK_BACKGROUND_THRESHOLD = 85   # Si el brillo promedio es menor, es fondo oscuro
INVERSION_CONFIDENCE_THRESHOLD = 0.7  # Confianza mínima para aplicar inversión

# === CONFIGURACIÓN DE TESSERACT ===
TESSERACT_OEM = 3               # OCR Engine Mode
TESSERACT_PSM_SINGLE_BLOCK = 6  # Page Segmentation Mode para bloques
TESSERACT_PSM_SINGLE_LINE = 7   # Para líneas individuales
TESSERACT_PSM_SINGLE_WORD = 8   # Para palabras individuales
TESSERACT_PSM_OSD_DETECTION = 0 # Para detección de orientación

# Configuraciones OCR optimizadas
TESSERACT_CONFIG_HIGH_QUALITY = "--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,:-/() "
TESSERACT_CONFIG_NUMBERS_ONLY = "--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789.,-"
TESSERACT_CONFIG_DATE = "--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789/-:"

# === CONFIGURACIÓN DE EXTRACCIÓN ===
# Estrategia de centro y expansión
CENTER_EXPANSION_RADIUS = 50    # Radio inicial de búsqueda
MAX_EXPANSION_RADIUS = 150      # Radio máximo de expansión
EXPANSION_STEP = 25             # Incremento en cada expansión

# Umbrales de confianza
MIN_CONFIDENCE_THRESHOLD = 60   # Confianza mínima para aceptar extracción
HIGH_CONFIDENCE_THRESHOLD = 85  # Confianza alta

# === CAMPOS A EXTRAER ===
EXTRACTION_FIELDS = {
    "monto": {
        "patterns": [r"\d+[.,]\d{2}", r"\d+\.\d{2}", r"\d+,\d{2}"],
        "keywords": ["monto", "total", "importe", "bs", "bolivares"],
        "required": True
    },
    "fecha": {
        "patterns": [r"\d{2}[/-]\d{2}[/-]\d{4}", r"\d{2}[/-]\d{2}[/-]\d{2}"],
        "keywords": ["fecha", "date"],
        "required": True
    },
    "operacion": {
        "patterns": [r"\d{10,15}", r"[A-Z0-9]{10,15}"],
        "keywords": ["operacion", "operación", "transaccion", "ref"],
        "required": True
    },
    "identificacion": {
        "patterns": [r"[VE]-?\d{7,9}", r"\d{7,9}"],
        "keywords": ["cedula", "cédula", "ci", "identificacion"],
        "required": False
    },
    "origen": {
        "patterns": [r"[A-Za-z\s]+"],
        "keywords": ["origen", "desde", "de"],
        "required": False
    },
    "destino": {
        "patterns": [r"[A-Za-z\s]+"],
        "keywords": ["destino", "hacia", "para"],
        "required": False
    },
    "banco": {
        "patterns": [r"[A-Za-z\s]+"],
        "keywords": ["banco", "bank", "entidad"],
        "required": False
    },
    "concepto": {
        "patterns": [r"[A-Za-z0-9\s]+"],
        "keywords": ["concepto", "descripcion", "motivo"],
        "required": False
    }
}

# === CONFIGURACIÓN DE GUARDADO ===
SAVE_PREPROCESSED_IMAGES = True
SAVE_DEBUG_IMAGES = True
SAVE_OCR_DETAILS = True

# === CONFIGURACIÓN DE RENDIMIENTO ===
MAX_IMAGE_SIZE = (2000, 2000)  # Tamaño máximo para procesamiento
PARALLEL_PROCESSING = False     # Procesamiento paralelo (experimental)
