"""
Motor OCR - Encapsula todas las llamadas a Tesseract
Proporciona interfaces consistentes para diferentes modos de OCR
"""

import cv2
import numpy as np
import pytesseract
from PIL import Image
from typing import Dict, Tuple
import logging
import config

logger = logging.getLogger(__name__)

def perform_general_ocr(image: np.ndarray) -> Dict:
    """
    Realiza OCR general sobre toda la imagen para obtener texto y coordenadas
    
    Args:
        image: Imagen preprocesada como array numpy
        
    Returns:
        Dict: Datos completos de OCR con texto, coordenadas y confianza
    """
    logger.info("Realizando OCR general sobre imagen completa")
    
    try:
        # Convertir a PIL para Tesseract
        if len(image.shape) == 3:
            pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        else:
            pil_image = Image.fromarray(image)
        
        # Configuración de Tesseract para OCR general
        tesseract_config = (f'--psm {config.TESSERACT_PSM_GENERAL_OCR} '
                          f'--oem {config.TESSERACT_OEM} '
                          f'-l {config.TESSERACT_LANG}')
        
        # Obtener datos detallados de OCR
        ocr_data = pytesseract.image_to_data(
            pil_image,
            config=tesseract_config,
            output_type=pytesseract.Output.DICT
        )
        
        # Filtrar resultados con confianza > 0
        filtered_data = {
            'text': [],
            'left': [],
            'top': [],
            'width': [],
            'height': [],
            'conf': [],
            'word_num': [],
            'line_num': [],
            'par_num': []
        }
        
        for i, conf in enumerate(ocr_data['conf']):
            if int(conf) > 0 and ocr_data['text'][i].strip():
                for key in filtered_data.keys():
                    filtered_data[key].append(ocr_data[key][i])
        
        # Obtener también el texto completo
        full_text = pytesseract.image_to_string(pil_image, config=tesseract_config)
        filtered_data['full_text'] = full_text.strip()
        
        logger.info(f"OCR general completado - {len(filtered_data['text'])} palabras detectadas")
        
        return filtered_data
        
    except Exception as e:
        logger.error(f"Error durante OCR general: {e}", exc_info=True)
        return {
            'text': [],
            'left': [],
            'top': [],
            'width': [],
            'height': [],
            'conf': [],
            'word_num': [],
            'line_num': [],
            'par_num': [],
            'full_text': '',
            'error': str(e)
        }

def perform_directed_ocr(image_roi: np.ndarray, psm_mode: str) -> Tuple[str, float]:
    """
    Realiza OCR dirigido sobre una región específica de la imagen
    
    Args:
        image_roi: Región de interés como array numpy
        psm_mode: Modo PSM específico para el tipo de contenido esperado
        
    Returns:
        Tuple[str, float]: (texto_extraido, confianza_promedio)
    """
    logger.debug(f"Realizando OCR dirigido con PSM {psm_mode}")
    
    try:
        # Validar que la ROI no esté vacía
        if image_roi.size == 0:
            logger.warning("ROI vacía proporcionada para OCR dirigido")
            return "", 0.0
        
        # Convertir a PIL
        if len(image_roi.shape) == 3:
            pil_image = Image.fromarray(cv2.cvtColor(image_roi, cv2.COLOR_BGR2RGB))
        else:
            pil_image = Image.fromarray(image_roi)
        
        # Configuración específica para OCR dirigido
        tesseract_config = (f'--psm {psm_mode} '
                          f'--oem {config.TESSERACT_OEM} '
                          f'-l {config.TESSERACT_LANG}')
        
        # Obtener texto
        extracted_text = pytesseract.image_to_string(pil_image, config=tesseract_config).strip()
        
        # Obtener confianza promedio
        try:
            ocr_data = pytesseract.image_to_data(
                pil_image,
                config=tesseract_config,
                output_type=pytesseract.Output.DICT
            )
            
            # Calcular confianza promedio de palabras válidas
            valid_confidences = [int(conf) for conf in ocr_data['conf'] 
                               if int(conf) > 0]
            
            average_confidence = sum(valid_confidences) / len(valid_confidences) if valid_confidences else 0.0
            
        except Exception as conf_error:
            logger.warning(f"Error calculando confianza: {conf_error}")
            average_confidence = 50.0  # Confianza por defecto
        
        logger.debug(f"OCR dirigido completado - Texto: '{extracted_text}', Confianza: {average_confidence:.1f}")
        
        return extracted_text, average_confidence
        
    except Exception as e:
        logger.error(f"Error durante OCR dirigido: {e}", exc_info=True)
        return "", 0.0

def perform_sparse_ocr(image: np.ndarray) -> Dict:
    """
    Realiza OCR en modo sparse para detectar texto disperso
    Útil para ZOI dinámicas y detección de palabras clave
    
    Args:
        image: Imagen como array numpy
        
    Returns:
        Dict: Datos de OCR con énfasis en detección de palabras clave
    """
    logger.debug("Realizando OCR sparse para detección de palabras clave")
    
    try:
        # Convertir a PIL
        if len(image.shape) == 3:
            pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        else:
            pil_image = Image.fromarray(image)
        
        # Configuración para texto disperso
        tesseract_config = (f'--psm {config.TESSERACT_PSM_SPARSE_TEXT_NO_RECEIPT} '
                          f'--oem {config.TESSERACT_OEM} '
                          f'-l {config.TESSERACT_LANG}')
        
        # Obtener datos completos
        ocr_data = pytesseract.image_to_data(
            pil_image,
            config=tesseract_config,
            output_type=pytesseract.Output.DICT
        )
        
        # Obtener texto completo también
        full_text = pytesseract.image_to_string(pil_image, config=tesseract_config)
        ocr_data['full_text'] = full_text.strip()
        
        logger.debug(f"OCR sparse completado - Texto detectado: {len(full_text)} caracteres")
        
        return ocr_data
        
    except Exception as e:
        logger.error(f"Error durante OCR sparse: {e}", exc_info=True)
        return {
            'text': [],
            'left': [],
            'top': [],
            'width': [],
            'height': [],
            'conf': [],
            'full_text': '',
            'error': str(e)
        }

def get_text_bounding_boxes(ocr_data: Dict, min_confidence: int = 30) -> list:
    """
    Extrae cajas delimitadoras de texto con confianza mínima
    
    Args:
        ocr_data: Datos de OCR de Tesseract
        min_confidence: Confianza mínima para considerar una detección
        
    Returns:
        list: Lista de diccionarios con información de cajas delimitadoras
    """
    bounding_boxes = []
    
    try:
        for i, conf in enumerate(ocr_data.get('conf', [])):
            if int(conf) >= min_confidence and ocr_data['text'][i].strip():
                box = {
                    'text': ocr_data['text'][i],
                    'left': ocr_data['left'][i],
                    'top': ocr_data['top'][i],
                    'width': ocr_data['width'][i],
                    'height': ocr_data['height'][i],
                    'confidence': int(conf),
                    'right': ocr_data['left'][i] + ocr_data['width'][i],
                    'bottom': ocr_data['top'][i] + ocr_data['height'][i]
                }
                bounding_boxes.append(box)
        
        logger.debug(f"Extraídas {len(bounding_boxes)} cajas delimitadoras con confianza >= {min_confidence}")
        
    except Exception as e:
        logger.error(f"Error extrayendo cajas delimitadoras: {e}")
    
    return bounding_boxes
