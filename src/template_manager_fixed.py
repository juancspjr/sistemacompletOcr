"""
Gestor de plantillas CORREGIDO - Solución para ROI en blanco
Corrección crítica del cálculo de ZOI dinámicas
"""

import cv2
import numpy as np
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging
import re
import config

logger = logging.getLogger(__name__)

class TemplateManager:
    """Gestor de plantillas y ZOI dinámicas - VERSIÓN CORREGIDA"""
    
    def __init__(self):
        self.templates = {}
        self.load_templates()
    
    def load_templates(self):
        """Carga todas las plantillas disponibles desde el directorio templates/"""
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
    
    def calculate_text_anchor_score(self, template_data: Dict, ocr_data: Dict) -> float:
        """Calcula puntuación basada en anclajes textuales"""
        try:
            text_anchors = template_data.get('huella_texto_clave', [])
            if not text_anchors:
                return 0.0
            
            full_text = ocr_data.get('full_text', '').upper()
            detected_words = [word.upper() for word in ocr_data.get('text', [])]
            
            matches = 0
            total_anchors = len(text_anchors)
            
            for anchor in text_anchors:
                anchor_upper = anchor.upper()
                if anchor_upper in full_text or any(anchor_upper in word for word in detected_words):
                    matches += 1
            
            score = matches / total_anchors if total_anchors > 0 else 0.0
            logger.debug(f"Puntuación anclajes textuales: {score:.2f} ({matches}/{total_anchors})")
            
            return score
            
        except Exception as e:
            logger.warning(f"Error calculando puntuación de anclajes textuales: {e}")
            return 0.0
    
    def calculate_structural_skeleton_score(self, template_data: Dict, 
                                          ocr_data: Dict, image_dimensions: Tuple[int, int]) -> float:
        """Calcula puntuación basada en esqueleto estructural"""
        try:
            skeleton_data = template_data.get('esqueleto_estructural', {})
            if not skeleton_data:
                return 0.0
            
            text_boxes = []
            for i, conf in enumerate(ocr_data.get('conf', [])):
                if int(conf) > 30:
                    box = {
                        'left': ocr_data['left'][i],
                        'top': ocr_data['top'][i],
                        'width': ocr_data['width'][i],
                        'height': ocr_data['height'][i]
                    }
                    text_boxes.append(box)
            
            if not text_boxes:
                return 0.0
            
            expected_regions = skeleton_data.get('regiones_esperadas', [])
            if not expected_regions:
                return 0.0
            
            img_width, img_height = image_dimensions
            matches = 0
            
            for expected_region in expected_regions:
                exp_left = expected_region.get('left_rel', 0) * img_width
                exp_top = expected_region.get('top_rel', 0) * img_height
                exp_width = expected_region.get('width_rel', 0) * img_width
                exp_height = expected_region.get('height_rel', 0) * img_height
                
                for box in text_boxes:
                    overlap_left = max(exp_left, box['left'])
                    overlap_top = max(exp_top, box['top'])
                    overlap_right = min(exp_left + exp_width, box['left'] + box['width'])
                    overlap_bottom = min(exp_top + exp_height, box['top'] + box['height'])
                    
                    if overlap_right > overlap_left and overlap_bottom > overlap_top:
                        overlap_area = (overlap_right - overlap_left) * (overlap_bottom - overlap_top)
                        expected_area = exp_width * exp_height
                        
                        if overlap_area / expected_area > 0.3:
                            matches += 1
                            break
            
            score = matches / len(expected_regions) if expected_regions else 0.0
            logger.debug(f"Puntuación esqueleto estructural: {score:.2f} ({matches}/{len(expected_regions)})")
            
            return score
            
        except Exception as e:
            logger.warning(f"Error calculando puntuación de esqueleto estructural: {e}")
            return 0.0
    
    def calculate_template_match_score(self, template_name: str, template_data: Dict,
                                     ocr_data: Dict, image_dimensions: Tuple[int, int]) -> float:
        """Calcula puntuación total de coincidencia para una plantilla"""
        try:
            text_weight = 0.6
            structural_weight = 0.4
            
            text_score = self.calculate_text_anchor_score(template_data, ocr_data)
            structural_score = self.calculate_structural_skeleton_score(
                template_data, ocr_data, image_dimensions
            )
            
            total_score = (text_score * text_weight) + (structural_score * structural_weight)
            
            logger.debug(f"Plantilla {template_name} - Puntuación total: {total_score:.2f} "
                        f"(Texto: {text_score:.2f}, Estructural: {structural_score:.2f})")
            
            return total_score
            
        except Exception as e:
            logger.warning(f"Error calculando puntuación total para plantilla {template_name}: {e}")
            return 0.0
    
    def identify_best_template(self, ocr_data: Dict, image_dimensions: Tuple[int, int]) -> Optional[Tuple[str, Dict, float]]:
        """Identifica la mejor plantilla coincidente"""
        if not self.templates:
            logger.warning("No hay plantillas cargadas")
            return None
        
        best_template = None
        best_score = 0.0
        best_data = None
        
        logger.info("Evaluando plantillas disponibles...")
        
        for template_name, template_data in self.templates.items():
            score = self.calculate_template_match_score(
                template_name, template_data, ocr_data, image_dimensions
            )
            
            if score > best_score:
                best_score = score
                best_template = template_name
                best_data = template_data
        
        min_threshold = 0.4
        
        if best_score >= min_threshold:
            logger.info(f"Plantilla identificada: {best_template} (puntuación: {best_score:.2f})")
            return best_template, best_data, best_score
        else:
            logger.info(f"Ninguna plantilla supera el umbral mínimo ({min_threshold}). "
                       f"Mejor puntuación: {best_score:.2f}")
            return None
    
    def find_text_boxes_by_keywords(self, ocr_data: Dict, keywords: List[str], 
                                   min_confidence: int = 20) -> List[Dict]:
        """
        NUEVA FUNCIÓN: Encuentra cajas de texto que contengan palabras clave específicas
        """
        matching_boxes = []
        
        try:
            for i, conf in enumerate(ocr_data.get('conf', [])):
                if int(conf) >= min_confidence and ocr_data['text'][i].strip():
                    text = ocr_data['text'][i].lower().strip()
                    
                    # Verificar si el texto contiene alguna palabra clave
                    for keyword in keywords:
                        if keyword.lower() in text:
                            box = {
                                'text': ocr_data['text'][i],
                                'left': ocr_data['left'][i],
                                'top': ocr_data['top'][i],
                                'width': ocr_data['width'][i],
                                'height': ocr_data['height'][i],
                                'confidence': int(conf),
                                'keyword_matched': keyword
                            }
                            matching_boxes.append(box)
                            logger.debug(f"Palabra clave '{keyword}' encontrada en: '{text}' "
                                       f"en posición ({box['left']}, {box['top']})")
                            break
            
            return matching_boxes
            
        except Exception as e:
            logger.error(f"Error buscando palabras clave: {e}")
            return []
    
    def find_value_boxes_near_keyword(self, ocr_data: Dict, keyword_box: Dict, 
                                     search_radius: int = 100) -> List[Dict]:
        """
        NUEVA FUNCIÓN: Encuentra cajas de texto con valores cerca de una palabra clave
        """
        value_boxes = []
        
        try:
            kw_center_x = keyword_box['left'] + keyword_box['width'] // 2
            kw_center_y = keyword_box['top'] + keyword_box['height'] // 2
            
            for i, conf in enumerate(ocr_data.get('conf', [])):
                if int(conf) >= 20 and ocr_data['text'][i].strip():
                    box_center_x = ocr_data['left'][i] + ocr_data['width'][i] // 2
                    box_center_y = ocr_data['top'][i] + ocr_data['height'][i] // 2
                    
                    # Calcular distancia
                    distance = ((box_center_x - kw_center_x) ** 2 + 
                               (box_center_y - kw_center_y) ** 2) ** 0.5
                    
                    if distance <= search_radius:
                        value_box = {
                            'text': ocr_data['text'][i],
                            'left': ocr_data['left'][i],
                            'top': ocr_data['top'][i],
                            'width': ocr_data['width'][i],
                            'height': ocr_data['height'][i],
                            'confidence': int(conf),
                            'distance_from_keyword': distance
                        }
                        value_boxes.append(value_box)
            
            # Ordenar por distancia (más cerca primero)
            value_boxes.sort(key=lambda x: x['distance_from_keyword'])
            
            return value_boxes
            
        except Exception as e:
            logger.error(f"Error buscando valores cerca de palabra clave: {e}")
            return []
    
    def calculate_dynamic_zoi(self, ocr_data: Dict, image_dimensions: Tuple[int, int]) -> Dict:
        """
        FUNCIÓN COMPLETAMENTE REDISEÑADA: Calcula ZOI dinámicas con lógica corregida
        """
        logger.info("Calculando ZOI dinámicas con lógica corregida...")
        
        dynamic_zoi = {
            'method': 'dynamic_zoi_fixed',
            'campos': {}
        }
        
        try:
            img_width, img_height = image_dimensions
            
            # Mapeo mejorado de palabras clave por campo
            field_keywords_map = {
                'monto': ['bs', 'bolivares', 'monto', 'total'],
                'referencia': ['operacion', 'operación', 'ref', 'referencia', 'numero'],
                'fecha': ['fecha'],
                'cedula_origen': ['origen', 'identificacion', 'identificación'],
                'cedula_destino': ['destino'],
                'banco_origen': ['banco'],
                'banco_destino': ['banco']
            }
            
            # Estrategia 1: Buscar usando palabras clave específicas
            for field_name, keywords in field_keywords_map.items():
                logger.debug(f"Procesando campo: {field_name}")
                
                # Encontrar cajas de texto que contengan las palabras clave
                keyword_boxes = self.find_text_boxes_by_keywords(ocr_data, keywords)
                
                if keyword_boxes:
                    logger.debug(f"Encontradas {len(keyword_boxes)} cajas con palabras clave para {field_name}")
                    
                    # Para cada caja de palabra clave, buscar valores cercanos
                    best_zoi = None
                    best_confidence = 0
                    
                    for keyword_box in keyword_boxes:
                        # Buscar valores cerca de esta palabra clave
                        nearby_values = self.find_value_boxes_near_keyword(
                            ocr_data, keyword_box, search_radius=150
                        )
                        
                        if nearby_values:
                            # Tomar el valor más cercano que no sea la palabra clave misma
                            for value_box in nearby_values:
                                if value_box['text'].lower() != keyword_box['text'].lower():
                                    # Crear ZOI basada en la caja del valor
                                    zoi = self.create_zoi_from_value_box(
                                        value_box, field_name, img_width, img_height
                                    )
                                    
                                    if zoi and value_box['confidence'] > best_confidence:
                                        best_zoi = zoi
                                        best_confidence = value_box['confidence']
                                        logger.debug(f"ZOI mejorada para {field_name}: "
                                                   f"texto='{value_box['text']}', "
                                                   f"confianza={value_box['confidence']}")
                                    break
                    
                    if best_zoi:
                        dynamic_zoi['campos'][field_name] = best_zoi
                        logger.info(f"ZOI dinámica exitosa para {field_name}")
                        continue
                
                # Estrategia 2: Fallback - buscar por posición relativa
                fallback_zoi = self.calculate_fallback_zoi(
                    field_name, ocr_data, img_width, img_height
                )
                
                if fallback_zoi:
                    dynamic_zoi['campos'][field_name] = fallback_zoi
                    logger.info(f"ZOI fallback aplicada para {field_name}")
            
            logger.info(f"ZOI dinámicas calculadas para {len(dynamic_zoi['campos'])} campos")
            
        except Exception as e:
            logger.error(f"Error calculando ZOI dinámicas: {e}", exc_info=True)
            dynamic_zoi['error'] = str(e)
        
        return dynamic_zoi
    
    def create_zoi_from_value_box(self, value_box: Dict, field_name: str, 
                                 img_width: int, img_height: int) -> Optional[Dict]:
        """
        NUEVA FUNCIÓN: Crea ZOI directamente desde la caja del valor detectado
        """
        try:
            # Usar directamente las coordenadas de la caja del valor
            left = value_box['left']
            top = value_box['top']
            width = value_box['width']
            height = value_box['height']
            
            # Añadir margen de seguridad
            margin = 5
            left = max(0, left - margin)
            top = max(0, top - margin)
            width = min(img_width - left, width + 2 * margin)
            height = min(img_height - top, height + 2 * margin)
            
            # Validar que la ZOI sea válida
            if width <= 0 or height <= 0:
                logger.warning(f"ZOI inválida para {field_name}: width={width}, height={height}")
                return None
            
            zoi = {
                'left': int(left),
                'top': int(top),
                'width': int(width),
                'height': int(height),
                'confidence': value_box['confidence'],
                'detected_text': value_box['text'],
                'method': 'value_box_direct',
                'psm_mode': config.TESSERACT_PSM_WORD_OCR  # Modo palabra para valores específicos
            }
            
            logger.debug(f"ZOI creada para {field_name}: {zoi}")
            return zoi
            
        except Exception as e:
            logger.error(f"Error creando ZOI desde caja de valor para {field_name}: {e}")
            return None
    
    def calculate_fallback_zoi(self, field_name: str, ocr_data: Dict, 
                              img_width: int, img_height: int) -> Optional[Dict]:
        """
        NUEVA FUNCIÓN: Calcula ZOI de fallback basada en posición relativa en la imagen
        """
        try:
            logger.debug(f"Calculando ZOI fallback para {field_name}")
            
            # Definir regiones aproximadas basadas en el layout típico del recibo
            fallback_regions = {
                'monto': {'x_rel': 0.3, 'y_rel': 0.25, 'w_rel': 0.4, 'h_rel': 0.1},
                'fecha': {'x_rel': 0.5, 'y_rel': 0.4, 'w_rel': 0.4, 'h_rel': 0.08},
                'referencia': {'x_rel': 0.4, 'y_rel': 0.5, 'w_rel': 0.5, 'h_rel': 0.08},
                'cedula_origen': {'x_rel': 0.4, 'y_rel': 0.65, 'w_rel': 0.4, 'h_rel': 0.08},
                'cedula_destino': {'x_rel': 0.4, 'y_rel': 0.75, 'w_rel': 0.4, 'h_rel': 0.08},
                'banco_origen': {'x_rel': 0.2, 'y_rel': 0.85, 'w_rel': 0.6, 'h_rel': 0.08},
                'banco_destino': {'x_rel': 0.2, 'y_rel': 0.85, 'w_rel': 0.6, 'h_rel': 0.08}
            }
            
            if field_name not in fallback_regions:
                return None
            
            region = fallback_regions[field_name]
            
            left = int(img_width * region['x_rel'])
            top = int(img_height * region['y_rel'])
            width = int(img_width * region['w_rel'])
            height = int(img_height * region['h_rel'])
            
            # Validar coordenadas
            left = max(0, min(left, img_width - 1))
            top = max(0, min(top, img_height - 1))
            width = min(width, img_width - left)
            height = min(height, img_height - top)
            
            if width <= 0 or height <= 0:
                return None
            
            zoi = {
                'left': left,
                'top': top,
                'width': width,
                'height': height,
                'confidence': 30,  # Confianza baja para fallback
                'method': 'fallback_relative_position',
                'psm_mode': config.TESSERACT_PSM_LINE_OCR
            }
            
            logger.debug(f"ZOI fallback para {field_name}: {zoi}")
            return zoi
            
        except Exception as e:
            logger.error(f"Error calculando ZOI fallback para {field_name}: {e}")
            return None

def identify_template_or_zoi(ocr_data_full_image: Dict, image_dimensions: Tuple[int, int]) -> Dict:
    """
    Función principal CORREGIDA para identificar plantilla o calcular ZOI dinámicas
    """
    logger.info("Iniciando identificación de plantilla o cálculo de ZOI dinámicas CORREGIDAS")
    
    template_manager = TemplateManager()
    
    # Intentar identificar plantilla
    template_result = template_manager.identify_best_template(ocr_data_full_image, image_dimensions)
    
    if template_result:
        template_name, template_data, score = template_result
        
        result = {
            'method': 'template_based',
            'template_name': template_name,
            'template_data': template_data,
            'confidence_score': score,
            'campos': template_data.get('campos', {})
        }
        
        logger.info(f"Usando plantilla: {template_name}")
        return result
    
    else:
        # Fallback a ZOI dinámicas CORREGIDAS
        logger.info("Fallback a ZOI dinámicas CORREGIDAS")
        dynamic_result = template_manager.calculate_dynamic_zoi(ocr_data_full_image, image_dimensions)
        return dynamic_result
