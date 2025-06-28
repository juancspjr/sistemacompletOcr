"""
Extractor de Campos v3.0 - Lógica de Centro y Expansión
Basado en el algoritmo exitoso de direct_ocr_extractor_polished.py
"""

import cv2
import numpy as np
import pytesseract
import re
import json
import logging
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import config

logger = logging.getLogger(__name__)

# Definiciones de campos basadas en la lógica exitosa
FIELD_DEFINITIONS = {
    "monto": {
        "keywords": ["Bs", "Monto", "Total", "Pago", "Importe", "Valor", "Monto Total", "Bs.D"],
        "expected_value_dims": {"width": 150, "height": 30},
        "expansion_offset_x": 0, 
        "expansion_offset_y": -15, 
        "validation_regex": r"^\d{1,3}(?:[.,]\d{3})*,\d{2}$|^\d+[,.]\d{2}$|^\d+(\.\d+)?$"
    },
    "fecha": {
        "keywords": ["Fecha:", "Fecha", "Dia", "Día", "Date", "Fechas"],
        "expected_value_dims": {"width": 120, "height": 30},
        "expansion_offset_x": 0,
        "expansion_offset_y": -15,
        "validation_regex": r"^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}$|^\d{4}[/-]\d{1,2}[/-]\d{1,2}$"
    },
    "operacion": {
        "keywords": ["Operación:", "Operacion", "Nro Operación", "Número Operación", "Ref", "Referencia"],
        "expected_value_dims": {"width": 180, "height": 30},
        "expansion_offset_x": 0,
        "expansion_offset_y": -15,
        "validation_regex": r"^\d{8,20}$|^[A-Z0-9]{8,20}$"
    },
    "identificacion": {
        "keywords": ["Identificación:", "Identificacion", "C.I.", "CI", "Cédula", "Cedula", "V-", "E-", "J-"],
        "expected_value_dims": {"width": 120, "height": 30},
        "expansion_offset_x": 0,
        "expansion_offset_y": -15,
        "validation_regex": r"^[VEJ]-?\d{7,9}$|^\d{7,9}$"
    },
    "origen_numero": {
        "keywords": ["Origen:", "Origen", "Telefono Origen", "Cta Origen", "Cuenta Origen"],
        "expected_value_dims": {"width": 150, "height": 30},
        "expansion_offset_x": 0,
        "expansion_offset_y": -15,
        "validation_regex": r"^\d{10,}$|^[X*]{3,}\d{4}$"
    },
    "destino_numero": {
        "keywords": ["Destino:", "Destino", "Telefono Destino", "Cta Destino", "Cuenta Destino"],
        "expected_value_dims": {"width": 150, "height": 30},
        "expansion_offset_x": 0,
        "expansion_offset_y": -15,
        "validation_regex": r"^\d{10,}$"
    },
    "banco_completo": {
        "keywords": ["Banco:", "Banco", "Bco", "Banco Origen", "Banco Destino"],
        "expected_value_dims": {"width": 250, "height": 30},
        "expansion_offset_x": 0,
        "expansion_offset_y": -15,
        "validation_regex": r"^[A-Za-z\s]+$|^\d{4}\s*-\s*[A-Za-z\s]+$"
    },
    "concepto": {
        "keywords": ["Concepto:", "Concepto", "Desc", "Descripción", "Detalle"],
        "expected_value_dims": {"width": 200, "height": 30},
        "expansion_offset_x": 0,
        "expansion_offset_y": -15,
        "validation_regex": r"^.+$"
    }
}

class FieldExtractor:
    """Extractor de campos con lógica de centro y expansión"""
    
    def __init__(self):
        self.ocr_cache = {}
        self.extraction_stats = {
            "total_attempts": 0,
            "successful_extractions": 0,
            "failed_extractions": 0
        }
    
    def perform_ocr_on_region(self, image: np.ndarray, region: Tuple[int, int, int, int], 
                             field_name: str) -> Dict:
        """
        Realiza OCR en una región específica de la imagen
        """
        try:
            x, y, w, h = region
            
            # Extraer región
            roi = image[y:y+h, x:x+w]
            
            if roi.size == 0:
                return {"text": "", "confidence": 0, "error": "ROI vacía"}
            
            # Configurar Tesseract según el tipo de campo
            if field_name in ["monto"]:
                config_str = config.TESSERACT_CONFIG_NUMBERS_ONLY
            elif field_name in ["fecha"]:
                config_str = config.TESSERACT_CONFIG_DATE
            else:
                config_str = config.TESSERACT_CONFIG_HIGH_QUALITY
            
            # Realizar OCR
            ocr_data = pytesseract.image_to_data(roi, config=config_str, output_type=pytesseract.Output.DICT)
            
            # Filtrar texto con confianza mínima
            valid_texts = []
            confidences = []
            
            for i, conf in enumerate(ocr_data['conf']):
                if conf > config.MIN_CONFIDENCE_THRESHOLD:
                    text = ocr_data['text'][i].strip()
                    if text:
                        valid_texts.append(text)
                        confidences.append(conf)
            
            if valid_texts:
                combined_text = " ".join(valid_texts)
                avg_confidence = sum(confidences) / len(confidences)
                
                return {
                    "text": combined_text,
                    "confidence": avg_confidence,
                    "region": region,
                    "word_count": len(valid_texts)
                }
            else:
                return {"text": "", "confidence": 0, "error": "No se encontró texto válido"}
                
        except Exception as e:
            logger.error(f"Error en OCR de región {region}: {e}")
            return {"text": "", "confidence": 0, "error": str(e)}
    
    def find_anchor_points(self, image: np.ndarray, keywords: List[str]) -> List[Tuple[int, int]]:
        """
        Encuentra puntos de anclaje basados en palabras clave
        """
        anchor_points = []
        
        try:
            # OCR completo de la imagen
            ocr_data = pytesseract.image_to_data(
                image, 
                config=config.TESSERACT_CONFIG_HIGH_QUALITY,
                output_type=pytesseract.Output.DICT
            )
            
            # Buscar palabras clave
            for i, text in enumerate(ocr_data['text']):
                if not text.strip():
                    continue
                
                text_lower = text.lower().strip()
                
                for keyword in keywords:
                    if keyword.lower() in text_lower:
                        x = ocr_data['left'][i]
                        y = ocr_data['top'][i]
                        w = ocr_data['width'][i]
                        h = ocr_data['height'][i]
                        
                        # Centro del texto encontrado
                        center_x = x + w // 2
                        center_y = y + h // 2
                        
                        anchor_points.append((center_x, center_y))
                        logger.debug(f"Anclaje encontrado para '{keyword}' en ({center_x}, {center_y})")
            
            return anchor_points
            
        except Exception as e:
            logger.error(f"Error buscando puntos de anclaje: {e}")
            return []
    
    def expand_search_from_center(self, image: np.ndarray, center: Tuple[int, int], 
                                 field_name: str) -> Optional[Dict]:
        """
        Expande la búsqueda desde un punto central usando círculos concéntricos
        """
        center_x, center_y = center
        img_height, img_width = image.shape[:2]
        
        # Radios de expansión
        radii = list(range(config.CENTER_EXPANSION_RADIUS, 
                          config.MAX_EXPANSION_RADIUS + 1, 
                          config.EXPANSION_STEP))
        
        best_result = None
        best_confidence = 0
        
        for radius in radii:
            # Definir región de búsqueda
            x1 = max(0, center_x - radius)
            y1 = max(0, center_y - radius)
            x2 = min(img_width, center_x + radius)
            y2 = min(img_height, center_y + radius)
            
            region = (x1, y1, x2 - x1, y2 - y1)
            
            # Realizar OCR en la región
            ocr_result = self.perform_ocr_on_region(image, region, field_name)
            
            if ocr_result.get("confidence", 0) > best_confidence:
                # Validar el texto extraído
                extracted_value = self.validate_and_extract_field(
                    ocr_result.get("text", ""), field_name
                )
                
                if extracted_value:
                    best_result = {
                        "value": extracted_value,
                        "confidence": ocr_result["confidence"],
                        "region": region,
                        "radius": radius,
                        "raw_text": ocr_result.get("text", "")
                    }
                    best_confidence = ocr_result["confidence"]
                    
                    # Si encontramos alta confianza, no seguir expandiendo
                    if best_confidence > config.HIGH_CONFIDENCE_THRESHOLD:
                        break
            
            logger.debug(f"Radio {radius}: confianza {ocr_result.get('confidence', 0):.1f}")
        
        return best_result
    
    def validate_and_extract_field(self, text: str, field_name: str) -> Optional[str]:
        """
        Valida y extrae el valor de un campo específico
        """
        if not text or field_name not in FIELD_DEFINITIONS:
            return None
        
        field_config = FIELD_DEFINITIONS[field_name]
        patterns = field_config.get("validation_regex", [])
        
        # Limpiar texto
        cleaned_text = re.sub(r'\s+', ' ', text.strip())
        
        # Probar patrones específicos
        for pattern in patterns:
            matches = re.findall(pattern, cleaned_text, re.IGNORECASE)
            if matches:
                # Tomar la primera coincidencia válida
                match = matches[0]
                
                # Validaciones específicas por campo
                if field_name == "monto":
                    # Normalizar formato de monto
                    normalized = re.sub(r'[^\d.,]', '', match)
                    if ',' in normalized and '.' in normalized:
                        # Formato: 1,234.56
                        normalized = normalized.replace(',', '')
                    elif ',' in normalized:
                        # Formato: 123,45 (europeo)
                        normalized = normalized.replace(',', '.')
                    
                    try:
                        float(normalized)
                        return normalized
                    except ValueError:
                        continue
                
                elif field_name == "fecha":
                    # Validar formato de fecha
                    if re.match(r'\d{2}[/-]\d{2}[/-]\d{2,4}', match):
                        return match
                
                elif field_name == "operacion":
                    # Validar número de operación
                    if len(re.sub(r'[^\d]', '', match)) >= 10:
                        return match
                
                else:
                    # Para otros campos, devolver la coincidencia
                    return match.strip()
        
        return None
    
    def extract_field_with_center_expansion(self, image: np.ndarray, field_name: str) -> Dict:
        """
        Extrae un campo específico usando la estrategia de centro y expansión
        """
        logger.info(f"Extrayendo campo: {field_name}")
        
        self.extraction_stats["total_attempts"] += 1
        
        if field_name not in FIELD_DEFINITIONS:
            return {
                "field_name": field_name,
                "extraction_successful": False,
                "reason": "Campo no configurado",
                "value": None,
                "confidence": 0
            }
        
        field_config = FIELD_DEFINITIONS[field_name]
        keywords = field_config.get("keywords", [])
        
        try:
            # 1. Buscar puntos de anclaje
            anchor_points = self.find_anchor_points(image, keywords)
            
            if not anchor_points:
                # Fallback: buscar en toda la imagen
                logger.warning(f"No se encontraron anclajes para {field_name}, buscando en toda la imagen")
                img_height, img_width = image.shape[:2]
                anchor_points = [(img_width // 2, img_height // 2)]
            
            best_extraction = None
            best_confidence = 0
            
            # 2. Expandir búsqueda desde cada punto de anclaje
            for anchor in anchor_points:
                extraction_result = self.expand_search_from_center(image, anchor, field_name)
                
                if extraction_result and extraction_result["confidence"] > best_confidence:
                    best_extraction = extraction_result
                    best_confidence = extraction_result["confidence"]
            
            # 3. Evaluar resultado
            if best_extraction and best_confidence >= config.MIN_CONFIDENCE_THRESHOLD:
                self.extraction_stats["successful_extractions"] += 1
                
                result = {
                    "field_name": field_name,
                    "extraction_successful": True,
                    "value": best_extraction["value"],
                    "confidence": best_confidence,
                    "region": best_extraction["region"],
                    "radius": best_extraction["radius"],
                    "raw_text": best_extraction["raw_text"],
                    "anchor_points_found": len(anchor_points)
                }
                
                logger.info(f"✅ {field_name}: '{best_extraction['value']}' ({best_confidence:.1f}%)")
                return result
            else:
                self.extraction_stats["failed_extractions"] += 1
                
                result = {
                    "field_name": field_name,
                    "extraction_successful": False,
                    "reason": "Confianza insuficiente" if best_extraction else "No se encontró valor válido",
                    "value": None,
                    "confidence": best_confidence,
                    "anchor_points_found": len(anchor_points)
                }
                
                logger.warning(f"❌ {field_name}: {result['reason']}")
                return result
                
        except Exception as e:
            self.extraction_stats["failed_extractions"] += 1
            logger.error(f"Error extrayendo {field_name}: {e}")
            
            return {
                "field_name": field_name,
                "extraction_successful": False,
                "reason": f"Error: {str(e)}",
                "value": None,
                "confidence": 0,
                "error": str(e)
            }
    
    def create_debug_image(self, image: np.ndarray, extraction_results: Dict, output_path: str):
        """
        Crea imagen de debug con las regiones extraídas marcadas
        """
        try:
            debug_image = image.copy()
            
            for field_name, result in extraction_results.items():
                if result.get("extraction_successful", False) and "region" in result:
                    x, y, w, h = result["region"]
                    
                    # Dibujar rectángulo
                    cv2.rectangle(debug_image, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    
                    # Agregar etiqueta
                    label = f"{field_name}: {result.get('confidence', 0):.0f}%"
                    cv2.putText(debug_image, label, (x, y - 10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
            cv2.imwrite(output_path, debug_image)
            logger.info(f"Imagen de debug guardada: {output_path}")
            
        except Exception as e:
            logger.error(f"Error creando imagen de debug: {e}")

def extract_fields(image: np.ndarray, output_dir: str) -> Dict:
    """
    Función principal de extracción de campos
    """
    logger.info("Iniciando extracción de campos con lógica de centro y expansión")
    
    extractor = FieldExtractor()
    extraction_results = {}
    
    # Extraer cada campo configurado
    for field_name in FIELD_DEFINITIONS.keys():
        result = extractor.extract_field_with_center_expansion(image, field_name)
        extraction_results[field_name] = result
    
    # Crear imagen de debug
    if config.SAVE_DEBUG_IMAGES:
        debug_path = f"{output_dir}/{config.DEBUG_IMAGE_NAME}"
        extractor.create_debug_image(image, extraction_results, debug_path)
    
    # Guardar detalles OCR
    if config.SAVE_OCR_DETAILS:
        ocr_details = {
            "extraction_stats": extractor.extraction_stats,
            "extraction_results": extraction_results,
            "total_fields": len(FIELD_DEFINITIONS),
            "successful_extractions": extractor.extraction_stats["successful_extractions"],
            "extraction_rate": (extractor.extraction_stats["successful_extractions"] / 
                              len(FIELD_DEFINITIONS)) * 100
        }
        
        ocr_details_path = f"{output_dir}/{config.OCR_DETAILS_FILE}"
        with open(ocr_details_path, 'w', encoding='utf-8') as f:
            json.dump(ocr_details, f, indent=2, ensure_ascii=False)
    
    # Estadísticas finales
    successful = extractor.extraction_stats["successful_extractions"]
    total = len(FIELD_DEFINITIONS)
    rate = (successful / total) * 100 if total > 0 else 0
    
    logger.info(f"Extracción completada: {successful}/{total} campos ({rate:.1f}%)")
    
    return extraction_results
