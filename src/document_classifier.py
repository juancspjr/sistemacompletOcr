"""
Clasificador de documentos - Detección rápida de recibos vs contenido irrelevante
Optimizado para minimizar recursos en imágenes que no son recibos de pago
"""

import cv2
import numpy as np
import pytesseract
from PIL import Image
from pathlib import Path
from typing import Tuple, Dict
import logging
import config

logger = logging.getLogger(__name__)

def calculate_text_area_ratio(ocr_data: dict, image_dimensions: Tuple[int, int]) -> float:
    """Calcula la proporción del área total cubierta por texto detectado"""
    try:
        total_image_area = image_dimensions[0] * image_dimensions[1]
        text_area = 0
        
        # Sumar áreas de todas las cajas de texto detectadas
        for i, conf in enumerate(ocr_data['conf']):
            if int(conf) > 0:  # Solo considerar detecciones con confianza > 0
                width = ocr_data['width'][i]
                height = ocr_data['height'][i]
                text_area += width * height
        
        return text_area / total_image_area if total_image_area > 0 else 0
    except Exception as e:
        logger.warning(f"Error calculando proporción de área de texto: {e}")
        return 0

def count_payment_keywords(text: str) -> Tuple[int, list]:
    """Cuenta palabras clave de pago en el texto detectado"""
    text_upper = text.upper()
    found_keywords = []
    
    for keyword in config.PAYMENT_KEYWORDS:
        if keyword.upper() in text_upper:
            found_keywords.append(keyword)
    
    return len(found_keywords), found_keywords

def validate_image_dimensions(image_path: Path) -> bool:
    """Valida que la imagen tenga dimensiones mínimas válidas"""
    try:
        image = cv2.imread(str(image_path))
        if image is None:
            return False
        
        height, width = image.shape[:2]
        return (width >= config.MIN_IMAGE_DIMENSION and 
                height >= config.MIN_IMAGE_DIMENSION)
    except Exception as e:
        logger.error(f"Error validando dimensiones de imagen: {e}")
        return False

def is_payment_receipt(image_path: Path) -> Tuple[bool, Dict]:
    """
    Determina si una imagen es un recibo de pago legítimo
    
    Args:
        image_path: Ruta a la imagen a clasificar
        
    Returns:
        Tuple[bool, Dict]: (es_recibo, datos_clasificacion)
    """
    logger.info(f"Clasificando documento: {image_path}")
    
    classification_data = {
        "image_valid": False,
        "text_detected": "",
        "keywords_found": [],
        "keywords_count": 0,
        "text_area_ratio": 0.0,
        "classification_reason": ""
    }
    
    try:
        # Validar dimensiones de imagen
        if not validate_image_dimensions(image_path):
            classification_data["classification_reason"] = "invalid_image_dimensions"
            logger.info("Imagen rechazada: dimensiones inválidas")
            return False, classification_data
        
        classification_data["image_valid"] = True
        
        # Cargar imagen para OCR
        image = cv2.imread(str(image_path))
        pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        
        # OCR rápido con modo sparse text
        tesseract_config = f'--psm {config.TESSERACT_PSM_SPARSE_TEXT_NO_RECEIPT} --oem {config.TESSERACT_OEM} -l {config.TESSERACT_LANG}'
        
        # Obtener texto completo
        detected_text = pytesseract.image_to_string(pil_image, config=tesseract_config)
        classification_data["text_detected"] = detected_text.strip()
        
        # Obtener datos detallados para cálculo de área
        ocr_data = pytesseract.image_to_data(
            pil_image, 
            config=tesseract_config,
            output_type=pytesseract.Output.DICT
        )
        
        # Contar palabras clave de pago
        keywords_count, found_keywords = count_payment_keywords(detected_text)
        classification_data["keywords_found"] = found_keywords
        classification_data["keywords_count"] = keywords_count
        
        # Calcular proporción de área de texto
        image_dimensions = (image.shape[1], image.shape[0])  # (width, height)
        text_area_ratio = calculate_text_area_ratio(ocr_data, image_dimensions)
        classification_data["text_area_ratio"] = text_area_ratio
        
        # Aplicar criterios de clasificación
        is_receipt = (
            keywords_count >= config.MIN_PAYMENT_KEYWORDS_MATCH and
            text_area_ratio >= config.MIN_TEXT_AREA_RATIO_RECEIPT
        )
        
        if is_receipt:
            classification_data["classification_reason"] = "payment_receipt_detected"
            logger.info(f"Recibo detectado - Palabras clave: {keywords_count}, Área texto: {text_area_ratio:.3f}")
        else:
            if keywords_count < config.MIN_PAYMENT_KEYWORDS_MATCH:
                classification_data["classification_reason"] = "insufficient_payment_keywords"
            elif text_area_ratio < config.MIN_TEXT_AREA_RATIO_RECEIPT:
                classification_data["classification_reason"] = "insufficient_text_density"
            else:
                classification_data["classification_reason"] = "unknown_classification_failure"
            
            logger.info(f"No es recibo - Palabras clave: {keywords_count}, Área texto: {text_area_ratio:.3f}")
        
        return is_receipt, classification_data
        
    except Exception as e:
        logger.error(f"Error durante clasificación de documento: {e}", exc_info=True)
        classification_data["classification_reason"] = f"classification_error: {str(e)}"
        return False, classification_data
