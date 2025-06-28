# src/config.py
"""
Configuración del Sistema OCR v2.0.0
Todas las variables y constantes del sistema centralizadas
"""

import os
from pathlib import Path

# --- INFORMACIÓN DE VERSIÓN ---
VERSION = "2.0.0"
VERSION_NAME = "Extracción Flexible Optimizada"

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
OUTPUT_DIR = BASE_DIR / "output"
TEMP_DIR = BASE_DIR / "temp"
LOGS_DIR = BASE_DIR / "logs"

# Crear directorios si no existen al iniciar
for directory in [TEMPLATES_DIR, PROCESSED_RECEIPTS_DIR, PROCESSED_IMAGES_ARCHIVE_DIR,
                  FEEDBACK_LOOP_DIR, INPUT_DIR, OUTPUT_DIR, TEMP_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# --- CONFIGURACIÓN DE LOGGING ---
LOG_FILE_PATH = LOGS_DIR / "system.log"
LOG_FILE = LOG_FILE_PATH  # Alias para compatibilidad
LOG_LEVEL = "INFO"  # DEBUG para depuración exhaustiva, INFO para producción

# --- CONTROL DE ARCHIVOS TEMPORALES ---
CLEAN_TEMP_FILES = True  # Si es True, elimina la carpeta temp/<id_unico_imagen> al finalizar
                        # Establece a False para DEPURAR y revisar preprocesamientos y recortes

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
BRIGHTNESS_THRESHOLD_LOW = 70    # Promedio de píxeles &lt; LOW -> Imagen oscura
BRIGHTNESS_THRESHOLD_HIGH = 180  # Promedio de píxeles > HIGH -> Imagen muy brillante
NOISE_THRESHOLD_HIGH = 20   # Desviación estándar alta en áreas uniformes -> Mucho ruido

# --- CONFIGURACIÓN PARA EL AUTO-APRENDIZAJE ---
MANUAL_FEEDBACK_CSV_FILE = FEEDBACK_LOOP_DIR / "manual_feedback.csv"
PROCESSED_FEEDBACK_ARCHIVE_DIR = FEEDBACK_LOOP_DIR / "processed_feedback_archive"
PROCESSED_FEEDBACK_ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

# --- REGLAS DE CLASIFICACIÓN DE DOCUMENTOS ("No Recibo") ---
PAYMENT_KEYWORDS = [
    "Pago Móvil", "Transferencia", "Monto", "Fecha", "Referencia", 
    "C.I.", "RIF", "Bs", "Cédula", "Transf", "Movil", "Banco", "Cta", "Total",
    "Beneficiario", "Pagador", "Exitoso", "Aprobado", "Comprobante"
]
MIN_PAYMENT_KEYWORDS_MATCH = 2  # Cuántas palabras clave deben coincidir para considerarlo recibo
MIN_TEXT_AREA_RATIO_RECEIPT = 0.01  # Mínima proporción del área total cubierta por texto
MIN_IMAGE_DIMENSION = 200  # Mínima dimensión (ancho o alto) para una imagen válida

# --- CONFIGURACIÓN DE EXTRACCIÓN v2.0 ---
# Configuración para la estrategia de extracción flexible
EXTRACTION_CONFIDENCE_THRESHOLD = 70  # Umbral mínimo de confianza para considerar una extracción válida
FIELD_PROXIMITY_THRESHOLD = 100  # Distancia máxima en píxeles para asociar etiquetas con valores
TEXT_SIMILARITY_THRESHOLD = 0.8  # Umbral de similitud para coincidencias de texto

# --- CONFIGURACIÓN DE VALIDACIÓN CRUZADA ---
CROSS_VALIDATION_ENABLED = True  # Habilitar validación cruzada de resultados
VALIDATION_CONFIDENCE_BOOST = 10  # Incremento de confianza por validación exitosa

# --- CONFIGURACIÓN DE DEBUG ---
DEBUG_MODE = os.getenv('OCR_DEBUG', '0') == '1'
SAVE_DEBUG_IMAGES = DEBUG_MODE  # Guardar imágenes de debug si está en modo debug
DEBUG_OVERLAY_ENABLED = DEBUG_MODE  # Crear overlays de debug

# --- CONFIGURACIÓN DE RENDIMIENTO ---
MAX_IMAGE_SIZE = (2000, 2000)  # Tamaño máximo de imagen para procesamiento
RESIZE_LARGE_IMAGES = True  # Redimensionar imágenes grandes automáticamente
PARALLEL_PROCESSING = False  # Procesamiento paralelo (experimental)

# --- CONFIGURACIÓN DE CAMPOS DE EXTRACCIÓN ---
# Campos estándar que el sistema intentará extraer
STANDARD_FIELDS = [
    "monto",
    "fecha",
    "referencia", 
    "cedula_pagador",
    "telefono_pagador",
    "cedula_beneficiario",
    "telefono_beneficiario",
    "banco_emisor",
    "banco_receptor"
]

# --- CONFIGURACIÓN DE PATRONES REGEX ---
# Patrones para validación de campos extraídos
REGEX_PATTERNS = {
    "monto": r"(?:Bs\.?\s*)?(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)",
    "fecha": r"(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})",
    "referencia": r"(\d{8,15})",
    "cedula": r"([VEJ]?[-\s]?\d{1,2}\.?\d{3}\.?\d{3})",
    "telefono": r"(0?\d{3}[-\s]?\d{7})"
}

# --- MENSAJES DEL SISTEMA ---
SYSTEM_MESSAGES = {
    "processing_start": "Iniciando procesamiento OCR v2.0.0",
    "processing_complete": "Procesamiento completado exitosamente",
    "processing_error": "Error durante el procesamiento",
    "no_receipt_detected": "Documento no identificado como comprobante de pago",
    "low_confidence": "Extracción completada con baja confianza",
    "validation_failed": "Validación cruzada falló"
}

# --- CONFIGURACIÓN DE TIMEOUTS ---
PROCESSING_TIMEOUT = 300  # Timeout en segundos para procesamiento completo
OCR_TIMEOUT = 60  # Timeout para operaciones OCR individuales
IMAGE_PROCESSING_TIMEOUT = 30  # Timeout para preprocesamiento de imagen

# Función de validación de configuración
def validate_config():
    """
    Valida que la configuración sea correcta y todos los directorios existan
    """
    errors = []
    
    # Verificar directorios críticos
    critical_dirs = [BASE_DIR, SRC_DIR, LOGS_DIR, TEMP_DIR]
    for directory in critical_dirs:
        if not directory.exists():
            errors.append(f"Directorio crítico no existe: {directory}")
    
    # Verificar que LOG_FILE_PATH sea escribible
    try:
        LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        test_file = LOG_FILE_PATH.parent / "test_write.tmp"
        test_file.touch()
        test_file.unlink()
    except Exception as e:
        errors.append(f"No se puede escribir en directorio de logs: {e}")
    
    # Verificar configuración de Tesseract
    if not TESSERACT_LANG:
        errors.append("TESSERACT_LANG no puede estar vacío")
    
    if errors:
        raise ValueError(f"Errores de configuración: {'; '.join(errors)}")
    
    return True

# Ejecutar validación al importar
if __name__ != "__main__":
    try:
        validate_config()
    except ValueError as e:
        print(f"ADVERTENCIA: {e}")
