"""
Gestor de plantillas v2.0 - Estrategia de extracción flexible basada en OCR global
Implementa lógica de dos fases: Anclada por palabras clave + Extracción generalizada
"""

import cv2
import numpy as np
import yaml
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging
import config

logger = logging.getLogger(__name__)

# Definiciones de campos con estrategias flexibles
FIELD_DEFINITIONS = {
    "monto": {
        "keywords": ["Bs", "Monto", "Total", "Importe", "Valor", "Monto Total", "Bs.D", "bolivares"],
        "validation_regex": r"^\d{1,3}(?:[.,]\d{3})*,\d{2}$|^\d+[,.]\d{2}$|^\d+(\.\d+)?$",
        "search_strategy": "after_keyword_on_same_line_or_below",
        "max_distance_from_keyword": {"x": 300, "y": 100},
        "expected_value_type": "currency"
    },
    "fecha": {
        "keywords": ["Fecha:", "Fecha", "Dia", "Día", "Date", "Fechas"],
        "validation_regex": r"^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}$|^\d{4}[/-]\d{1,2}[/-]\d{1,2}$",
        "search_strategy": "after_keyword_on_same_line",
        "max_distance_from_keyword": {"x": 200, "y": 50},
        "expected_value_type": "date"
    },
    "operacion": {
        "keywords": ["Operación:", "Operacion", "Nro Operación", "Número Operación", "Ref", "Referencia"],
        "validation_regex": r"^\d{8,20}$|^[A-Z0-9]{8,20}$",
        "search_strategy": "after_keyword_on_same_line",
        "max_distance_from_keyword": {"x": 350, "y": 50},
        "expected_value_type": "alphanumeric_id"
    },
    "identificacion": {
        "keywords": ["Identificación:", "Identificacion", "C.I.", "CI", "Cédula", "Cedula", "V-", "E-", "J-"],
        "validation_regex": r"^[VEJ]-?\d{7,9}$|^\d{7,9}$",
        "search_strategy": "after_keyword_on_same_line",
        "max_distance_from_keyword": {"x": 200, "y": 50},
        "expected_value_type": "id_number"
    },
    "origen_numero": {
        "keywords": ["Origen:", "Origen", "Telefono Origen", "Cta Origen", "Cuenta Origen"],
        "validation_regex": r"^\d{10,}$|^[X*]{3,}\d{4}$",
        "search_strategy": "after_keyword_on_same_line",
        "max_distance_from_keyword": {"x": 250, "y": 50},
        "expected_value_type": "phone_or_account"
    },
    "destino_numero": {
        "keywords": ["Destino:", "Destino", "Telefono Destino", "Cta Destino", "Cuenta Destino"],
        "validation_regex": r"^\d{10,}$",
        "search_strategy": "after_keyword_on_same_line",
        "max_distance_from_keyword": {"x": 250, "y": 50},
        "expected_value_type": "phone_or_account"
    },
    "banco_completo": {
        "keywords": ["Banco:", "Banco", "Bco", "Banco Origen", "Banco Destino"],
        "validation_regex": r"^[A-Za-z\s\d\-]+$|^\d{4}\s*-\s*[A-Za-z\s]+$",
        "search_strategy": "after_keyword_multiword",
        "max_distance_from_keyword": {"x": 500, "y": 50},
        "expected_value_type": "bank_name"
    },
    "concepto": {
        "keywords": ["Concepto:", "Concepto", "Desc", "Descripción", "Detalle"],
        "validation_regex": r"^.+$",
        "search_strategy": "after_keyword_multiword",
        "max_distance_from_keyword": {"x": 400, "y": 100},
        "expected_value_type": "free_text"
    },
    "nombre_o_info_completa": {
        "keywords": [],  # Sin palabra clave ancla - búsqueda generalizada
        "validation_regex": r"^[A-Za-zÀ-ÿ\s]{5,}$",
        "search_strategy": "general_document_scan",
        "min_words": 2,
        "expected_value_type": "person_name_or_full_info"
    }
}

class TemplateManagerV2:
    """Gestor de plantillas v2.0 con estrategia de extracción flexible"""
    
    def __init__(self):
        self.templates = {}
        self.load_templates()
    
    def load_templates(self):
        """Carga plantillas tradicionales (compatibilidad)"""
        logger.info("Cargando plantillas desde directorio templates/")
        
        try:
            template_files = list(config.TEMPLATES_DIR.glob("*.yaml"))
            
            for yaml_file in template_files:
                try:
                    with open(yaml_file, 'r', encoding='utf-8') as f:
                        template_data = yaml.safe_load(f)
                    
                    template_name = yaml_file.stem
                    self.templates[template_name] = template_data
                    logger.info(f"Plantilla cargada: {template_name}")
                    
                except Exception as e:
                    logger.error(f"Error cargando plantilla {yaml_file}: {e}")
            
            logger.info(f"Total de plantillas cargadas: {len(self.templates)}")
            
        except Exception as e:
            logger.error(f"Error accediendo al directorio de plantillas: {e}")
    
    def convert_ocr_data_to_word_list(self, ocr_data: Dict) -> List[Dict]:
        """Convierte datos de OCR a lista de palabras con bbox"""
        word_list = []
        
        try:
            for i, text in enumerate(ocr_data.get('text', [])):
                if text.strip() and int(ocr_data.get('conf', [0])[i]) > 20:
                    word_data = {
                        'text': text.strip(),
                        'confidence': int(ocr_data.get('conf', [0])[i]),
                        'bbox': {
                            'left': ocr_data.get('left', [0])[i],
                            'top': ocr_data.get('top', [0])[i],
                            'width': ocr_data.get('width', [0])[i],
                            'height': ocr_data.get('height', [0])[i]
                        },
                        'center_point': {
                            'x': ocr_data.get('left', [0])[i] + ocr_data.get('width', [0])[i] // 2,
                            'y': ocr_data.get('top', [0])[i] + ocr_data.get('height', [0])[i] // 2
                        }
                    }
                    word_list.append(word_data)
            
            logger.debug(f"Convertidas {len(word_list)} palabras del OCR global")
            return word_list
            
        except Exception as e:
            logger.error(f"Error convirtiendo datos de OCR: {e}")
            return []
    
    def find_text_in_roi_flexible(self, all_ocr_words: List[Dict], roi_coords: Dict, 
                                 validation_regex: str, words_to_exclude: set = None,
                                 allow_multiword: bool = False) -> Tuple[str, float, Dict]:
        """Busca texto dentro de una ROI flexible, con soporte para múltiples palabras"""
        if words_to_exclude is None:
            words_to_exclude = set()
        
        best_match_text = ""
        best_match_conf = 0
        best_match_bbox = {}
        matched_word_indices = []
        
        try:
            # Primera pasada: Buscar match directo con regex
            for i, word_data in enumerate(all_ocr_words):
                if i in words_to_exclude:
                    continue
                
                text = word_data['text'].strip()
                conf = word_data['confidence']
                bbox = word_data['bbox']
                
                # Verificar intersección con ROI
                intersects = (bbox['left'] < (roi_coords['left'] + roi_coords['width']) and
                             (bbox['left'] + bbox['width']) > roi_coords['left'] and
                             bbox['top'] < (roi_coords['top'] + roi_coords['height']) and
                             (bbox['top'] + bbox['height']) > roi_coords['top'])
                
                if intersects and conf > 50:
                    if re.fullmatch(validation_regex, text) and conf > best_match_conf:
                        best_match_text = text
                        best_match_conf = conf
                        best_match_bbox = bbox
                        matched_word_indices = [i]
            
            # Segunda pasada: Si no hay match directo y se permite multiword
            if not best_match_text and allow_multiword:
                # Buscar palabras adyacentes que formen un valor válido
                words_in_roi = []
                for i, word_data in enumerate(all_ocr_words):
                    if i in words_to_exclude:
                        continue
                    
                    bbox = word_data['bbox']
                    intersects = (bbox['left'] < (roi_coords['left'] + roi_coords['width']) and
                                 (bbox['left'] + bbox['width']) > roi_coords['left'] and
                                 bbox['top'] < (roi_coords['top'] + roi_coords['height']) and
                                 (bbox['top'] + bbox['height']) > roi_coords['top'])
                    
                    if intersects and word_data['confidence'] > 50:
                        words_in_roi.append((i, word_data))
                
                # Ordenar por posición (izquierda a derecha, arriba a abajo)
                words_in_roi.sort(key=lambda x: (x[1]['bbox']['top'], x[1]['bbox']['left']))
                
                # Intentar combinaciones de palabras adyacentes
                for start_idx in range(len(words_in_roi)):
                    for end_idx in range(start_idx + 1, min(start_idx + 4, len(words_in_roi) + 1)):
                        combined_words = words_in_roi[start_idx:end_idx]
                        combined_text = " ".join([w[1]['text'] for w in combined_words])
                        
                        # Verificar si están en la misma línea (tolerancia de altura)
                        if len(combined_words) > 1:
                            y_positions = [w[1]['center_point']['y'] for w in combined_words]
                            if max(y_positions) - min(y_positions) > 30:  # No están en la misma línea
                                continue
                        
                        if re.fullmatch(validation_regex, combined_text):
                            avg_confidence = sum([w[1]['confidence'] for w in combined_words]) / len(combined_words)
                            if avg_confidence > best_match_conf:
                                best_match_text = combined_text
                                best_match_conf = avg_confidence
                                matched_word_indices = [w[0] for w in combined_words]
                                
                                # Calcular bbox combinado
                                left = min([w[1]['bbox']['left'] for w in combined_words])
                                top = min([w[1]['bbox']['top'] for w in combined_words])
                                right = max([w[1]['bbox']['left'] + w[1]['bbox']['width'] for w in combined_words])
                                bottom = max([w[1]['bbox']['top'] + w[1]['bbox']['height'] for w in combined_words])
                                
                                best_match_bbox = {
                                    'left': left,
                                    'top': top,
                                    'width': right - left,
                                    'height': bottom - top
                                }
            
            return best_match_text, best_match_conf, best_match_bbox
            
        except Exception as e:
            logger.error(f"Error en búsqueda flexible: {e}")
            return "", 0, {}
    
    def calculate_flexible_zoi(self, all_ocr_words: List[Dict]) -> Dict:
        """
        FUNCIÓN PRINCIPAL: Calcula ZOI usando estrategia de dos fases
        Fase A: Extracción anclada por palabras clave
        Fase B: Extracción generalizada sin ancla
        """
        logger.info("Iniciando cálculo de ZOI flexible (Estrategia v2.0)")
        
        extracted_fields_zoi = {}
        words_used = set()
        
        try:
            # FASE A: Extracción Anclada por Palabras Clave
            logger.info("FASE A: Extracción anclada por palabras clave")
            
            for field_name, field_def in FIELD_DEFINITIONS.items():
                if not field_def["keywords"]:  # Saltar campos sin palabra clave
                    continue
                
                logger.debug(f"Procesando campo anclado: {field_name}")
                
                best_keyword_match = None
                best_keyword_idx = -1
                
                # Buscar la mejor palabra clave ancla
                for word_idx, word_data in enumerate(all_ocr_words):
                    if word_idx in words_used:
                        continue
                    
                    if word_data['confidence'] > 70:
                        for keyword in field_def["keywords"]:
                            if keyword.lower() in word_data['text'].lower():
                                best_keyword_match = word_data
                                best_keyword_idx = word_idx
                                break
                    
                    if best_keyword_match:
                        break
                
                if best_keyword_match:
                    words_used.add(best_keyword_idx)
                    
                    # Definir zona de búsqueda flexible
                    search_zone = {
                        'left': best_keyword_match['bbox']['left'],
                        'top': best_keyword_match['bbox']['top'],
                        'width': field_def["max_distance_from_keyword"]["x"] + best_keyword_match['bbox']['width'],
                        'height': field_def["max_distance_from_keyword"]["y"] + best_keyword_match['bbox']['height']
                    }
                    
                    # Ajustar zona según estrategia
                    if "right" in field_def.get("search_strategy", "") or "after_keyword" in field_def.get("search_strategy", ""):
                        search_zone['left'] = best_keyword_match['bbox']['left'] + best_keyword_match['bbox']['width']
                        search_zone['width'] = field_def["max_distance_from_keyword"]["x"]
                    
                    # Determinar si permite múltiples palabras
                    allow_multiword = "multiword" in field_def.get("search_strategy", "")
                    
                    # Buscar valor en la zona flexible
                    found_value_text, found_value_conf, found_value_bbox = self.find_text_in_roi_flexible(
                        all_ocr_words, search_zone, field_def["validation_regex"], words_used, allow_multiword
                    )
                    
                    if found_value_text:
                        extracted_fields_zoi[field_name] = {
                            "value": found_value_text,
                            "confidence": found_value_conf,
                            "roi": found_value_bbox,
                            "keyword_ancla": best_keyword_match['text'],
                            "extraction_method": "keyword_anchored",
                            "psm_mode": config.TESSERACT_PSM_WORD_OCR
                        }
                        
                        # Marcar palabras del valor como usadas
                        for word_idx, word_data in enumerate(all_ocr_words):
                            if (word_data['bbox']['left'] >= found_value_bbox['left'] and
                                word_data['bbox']['left'] <= found_value_bbox['left'] + found_value_bbox['width'] and
                                word_data['bbox']['top'] >= found_value_bbox['top'] and
                                word_data['bbox']['top'] <= found_value_bbox['top'] + found_value_bbox['height']):
                                words_used.add(word_idx)
                        
                        logger.info(f"Campo {field_name} extraído por ancla: '{found_value_text}' "
                                   f"(confianza: {found_value_conf:.1f})")
            
            # FASE B: Extracción Generalizada
            logger.info("FASE B: Extracción generalizada sin ancla")
            
            for field_name, field_def in FIELD_DEFINITIONS.items():
                if field_name in extracted_fields_zoi or field_def["keywords"]:
                    continue  # Ya extraído o tiene palabra clave
                
                logger.debug(f"Procesando campo generalizado: {field_name}")
                
                # Buscar en palabras no usadas que coincidan con regex
                for word_idx, word_data in enumerate(all_ocr_words):
                    if word_idx in words_used or word_data['confidence'] < 60:
                        continue
                    
                    if re.fullmatch(field_def["validation_regex"], word_data['text'].strip()):
                        extracted_fields_zoi[field_name] = {
                            "value": word_data['text'].strip(),
                            "confidence": word_data['confidence'],
                            "roi": word_data['bbox'],
                            "extraction_method": "general_scan",
                            "psm_mode": config.TESSERACT_PSM_WORD_OCR
                        }
                        words_used.add(word_idx)
                        
                        logger.info(f"Campo {field_name} extraído por escaneo general: "
                                   f"'{word_data['text'].strip()}' (confianza: {word_data['confidence']})")
                        break
            
            # Preparar resultado final
            result = {
                'method': 'flexible_zoi_v2',
                'extraction_strategy': 'two_phase_anchored_and_general',
                'campos': extracted_fields_zoi,
                'words_processed': len(all_ocr_words),
                'words_used': len(words_used),
                'extraction_efficiency': len(words_used) / len(all_ocr_words) if all_ocr_words else 0
            }
            
            logger.info(f"ZOI flexible completada - {len(extracted_fields_zoi)} campos extraídos, "
                       f"eficiencia: {result['extraction_efficiency']:.2%}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error en cálculo de ZOI flexible: {e}", exc_info=True)
            return {
                'method': 'flexible_zoi_v2_error',
                'error': str(e),
                'campos': {}
            }
    
    def identify_best_template_traditional(self, ocr_data: Dict, image_dimensions: Tuple[int, int]) -> Optional[Tuple[str, Dict, float]]:
        """Método de compatibilidad para plantillas tradicionales"""
        logger.debug("Intentando identificación con plantillas tradicionales (fallback)")
        
        # Implementación simplificada para compatibilidad
        # En caso de que la estrategia flexible falle completamente
        
        if not self.templates:
            return None
        
        # Buscar plantilla con mayor coincidencia de palabras clave
        best_template = None
        best_score = 0
        
        full_text = ocr_data.get('full_text', '').lower()
        
        for template_name, template_data in self.templates.items():
            score = 0
            campos = template_data.get('campos', {})
            
            for field_name, field_config in campos.items():
                keywords = field_config.get('keywords', [])
                for keyword in keywords:
                    if keyword.lower() in full_text:
                        score += 1
            
            if score > best_score:
                best_score = score
                best_template = (template_name, template_data, score)
        
        return best_template

def identify_template_or_zoi_v2(ocr_data_full_image: Dict, image_dimensions: Tuple[int, int]) -> Dict:
    """
    FUNCIÓN PRINCIPAL v2.0: Estrategia de extracción flexible basada en OCR global
    Prioriza la nueva estrategia sobre plantillas tradicionales
    """
    logger.info("Iniciando identificación v2.0 - Estrategia flexible basada en OCR global")
    
    template_manager = TemplateManagerV2()
    
    try:
        # Convertir datos de OCR a formato de lista de palabras
        all_ocr_words = template_manager.convert_ocr_data_to_word_list(ocr_data_full_image)
        
        if not all_ocr_words:
            logger.warning("No se encontraron palabras válidas en OCR global")
            return {
                'method': 'flexible_zoi_v2_no_words',
                'error': 'no_valid_words_found',
                'campos': {}
            }
        
        # Aplicar estrategia flexible v2.0
        logger.info("Aplicando estrategia de extracción flexible v2.0...")
        flexible_result = template_manager.calculate_flexible_zoi(all_ocr_words)
        
        # Verificar si la extracción fue exitosa
        campos_extraidos = len(flexible_result.get('campos', {}))
        
        if campos_extraidos > 0:
            logger.info(f"Estrategia flexible v2.0 exitosa - {campos_extraidos} campos extraídos")
            return flexible_result
        else:
            logger.warning("Estrategia flexible v2.0 no extrajo campos - Intentando plantillas tradicionales")
            
            # Fallback a plantillas tradicionales (compatibilidad)
            template_result = template_manager.identify_best_template_traditional(
                ocr_data_full_image, image_dimensions
            )
            
            if template_result:
                template_name, template_data, score = template_result
                return {
                    'method': 'template_based_fallback',
                    'template_name': template_name,
                    'confidence_score': score,
                    'campos': template_data.get('campos', {})
                }
            else:
                logger.warning("Todas las estrategias fallaron - Retornando resultado vacío")
                return {
                    'method': 'all_strategies_failed',
                    'error': 'no_extraction_possible',
                    'campos': {}
                }
        
    except Exception as e:
        logger.error(f"Error en identificación v2.0: {e}", exc_info=True)
        return {
            'method': 'flexible_zoi_v2_error',
            'error': str(e),
            'campos': {}
        }
