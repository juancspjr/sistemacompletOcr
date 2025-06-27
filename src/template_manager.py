"""
Gestor de plantillas - Identificación de plantillas y cálculo de ZOI dinámicas
Maneja la selección de plantillas preestablecidas y fallback a zonas dinámicas
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
    """Gestor de plantillas y ZOI dinámicas"""
    
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
                # Buscar en texto completo y en palabras individuales
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
            
            # Obtener cajas delimitadoras del OCR
            text_boxes = []
            for i, conf in enumerate(ocr_data.get('conf', [])):
                if int(conf) > 30:  # Confianza mínima
                    box = {
                        'left': ocr_data['left'][i],
                        'top': ocr_data['top'][i],
                        'width': ocr_data['width'][i],
                        'height': ocr_data['height'][i]
                    }
                    text_boxes.append(box)
            
            if not text_boxes:
                return 0.0
            
            # Analizar distribución de bloques de texto
            expected_regions = skeleton_data.get('regiones_esperadas', [])
            if not expected_regions:
                return 0.0
            
            img_width, img_height = image_dimensions
            matches = 0
            
            for expected_region in expected_regions:
                # Convertir coordenadas relativas a absolutas
                exp_left = expected_region.get('left_rel', 0) * img_width
                exp_top = expected_region.get('top_rel', 0) * img_height
                exp_width = expected_region.get('width_rel', 0) * img_width
                exp_height = expected_region.get('height_rel', 0) * img_height
                
                # Buscar cajas de texto que coincidan con esta región
                for box in text_boxes:
                    # Calcular solapamiento
                    overlap_left = max(exp_left, box['left'])
                    overlap_top = max(exp_top, box['top'])
                    overlap_right = min(exp_left + exp_width, box['left'] + box['width'])
                    overlap_bottom = min(exp_top + exp_height, box['top'] + box['height'])
                    
                    if overlap_right > overlap_left and overlap_bottom > overlap_top:
                        overlap_area = (overlap_right - overlap_left) * (overlap_bottom - overlap_top)
                        expected_area = exp_width * exp_height
                        
                        if overlap_area / expected_area > 0.3:  # 30% de solapamiento mínimo
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
            # Pesos para diferentes tipos de puntuación
            text_weight = 0.6
            structural_weight = 0.4
            
            # Calcular puntuaciones individuales
            text_score = self.calculate_text_anchor_score(template_data, ocr_data)
            structural_score = self.calculate_structural_skeleton_score(
                template_data, ocr_data, image_dimensions
            )
            
            # Puntuación total ponderada
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
        
        # Umbral mínimo para considerar una plantilla válida
        min_threshold = 0.4
        
        if best_score >= min_threshold:
            logger.info(f"Plantilla identificada: {best_template} (puntuación: {best_score:.2f})")
            return best_template, best_data, best_score
        else:
            logger.info(f"Ninguna plantilla supera el umbral mínimo ({min_threshold}). "
                       f"Mejor puntuación: {best_score:.2f}")
            return None
    
    def calculate_dynamic_zoi(self, ocr_data: Dict, image_dimensions: Tuple[int, int]) -> Dict:
        """Calcula Zonas de Interés dinámicas basadas en palabras clave"""
        logger.info("Calculando ZOI dinámicas...")
        
        dynamic_zoi = {
            'method': 'dynamic_zoi',
            'campos': {}
        }
        
        try:
            # Definir palabras clave para cada campo
            field_keywords = {
                'monto': ['monto', 'bs', 'total', 'cantidad', 'bolivares'],
                'referencia': ['referencia', 'ref', 'numero', 'operacion'],
                'fecha': ['fecha', 'hora', 'timestamp'],
                'cedula_origen': ['cedula', 'c.i', 'ci', 'origen'],
                'cedula_destino': ['destino', 'beneficiario'],
                'banco_origen': ['banco', 'origen', 'emisor'],
                'banco_destino': ['banco', 'destino', 'receptor']
            }
            
            # Obtener cajas delimitadoras de texto
            text_boxes = []
            for i, conf in enumerate(ocr_data.get('conf', [])):
                if int(conf) > 20 and ocr_data['text'][i].strip():
                    text_boxes.append({
                        'text': ocr_data['text'][i].lower(),
                        'left': ocr_data['left'][i],
                        'top': ocr_data['top'][i],
                        'width': ocr_data['width'][i],
                        'height': ocr_data['height'][i],
                        'confidence': int(conf)
                    })
            
            # Para cada campo, buscar palabras clave cercanas
            for field_name, keywords in field_keywords.items():
                best_zoi = None
                best_confidence = 0
                
                for keyword in keywords:
                    # Buscar la palabra clave en las cajas de texto
                    for box in text_boxes:
                        if keyword in box['text']:
                            # Definir ZOI basada en la posición de la palabra clave
                            zoi = self.calculate_field_zoi_from_keyword(
                                box, field_name, image_dimensions
                            )
                            
                            if zoi and box['confidence'] > best_confidence:
                                best_zoi = zoi
                                best_confidence = box['confidence']
                
                if best_zoi:
                    dynamic_zoi['campos'][field_name] = best_zoi
                    logger.debug(f"ZOI dinámica calculada para {field_name}")
            
            logger.info(f"ZOI dinámicas calculadas para {len(dynamic_zoi['campos'])} campos")
            
        except Exception as e:
            logger.error(f"Error calculando ZOI dinámicas: {e}", exc_info=True)
            dynamic_zoi['error'] = str(e)
        
        return dynamic_zoi
    
    def calculate_field_zoi_from_keyword(self, keyword_box: Dict, field_name: str, 
                                       image_dimensions: Tuple[int, int]) -> Optional[Dict]:
        """Calcula ZOI específica para un campo basada en posición de palabra clave"""
        try:
            img_width, img_height = image_dimensions
            
            # Posición base de la palabra clave
            kw_left = keyword_box['left']
            kw_top = keyword_box['top']
            kw_width = keyword_box['width']
            kw_height = keyword_box['height']
            
            # Definir offsets específicos por tipo de campo
            field_offsets = {
                'monto': {'x_offset': kw_width + 10, 'y_offset': 0, 'width': 150, 'height': kw_height + 10},
                'referencia': {'x_offset': kw_width + 10, 'y_offset': 0, 'width': 200, 'height': kw_height + 10},
                'fecha': {'x_offset': kw_width + 10, 'y_offset': 0, 'width': 120, 'height': kw_height + 10},
                'cedula_origen': {'x_offset': kw_width + 10, 'y_offset': 0, 'width': 100, 'height': kw_height + 10},
                'cedula_destino': {'x_offset': kw_width + 10, 'y_offset': 0, 'width': 100, 'height': kw_height + 10},
                'banco_origen': {'x_offset': 0, 'y_offset': kw_height + 5, 'width': 200, 'height': 30},
                'banco_destino': {'x_offset': 0, 'y_offset': kw_height + 5, 'width': 200, 'height': 30}
            }
            
            offset = field_offsets.get(field_name, {'x_offset': 50, 'y_offset': 0, 'width': 100, 'height': 30})
            
            # Calcular coordenadas de la ZOI
            zoi_left = max(0, kw_left + offset['x_offset'])
            zoi_top = max(0, kw_top + offset['y_offset'])
            zoi_width = min(offset['width'], img_width - zoi_left)
            zoi_height = min(offset['height'], img_height - zoi_top)
            
            # Validar que la ZOI sea válida
            if zoi_width <= 0 or zoi_height <= 0:
                return None
            
            zoi = {
                'left': int(zoi_left),
                'top': int(zoi_top),
                'width': int(zoi_width),
                'height': int(zoi_height),
                'confidence': keyword_box['confidence'],
                'keyword_found': keyword_box['text'],
                'psm_mode': config.TESSERACT_PSM_LINE_OCR  # Modo por defecto para campos
            }
            
            return zoi
            
        except Exception as e:
            logger.warning(f"Error calculando ZOI para campo {field_name}: {e}")
            return None

def identify_template_or_zoi(ocr_data_full_image: Dict, image_dimensions: Tuple[int, int]) -> Dict:
    """
    Función principal para identificar plantilla o calcular ZOI dinámicas
    
    Args:
        ocr_data_full_image: Datos completos de OCR de la imagen
        image_dimensions: Dimensiones de la imagen (width, height)
        
    Returns:
        Dict: Datos de plantilla identificada o ZOI dinámicas calculadas
    """
    logger.info("Iniciando identificación de plantilla o cálculo de ZOI dinámicas")
    
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
        # Fallback a ZOI dinámicas
        logger.info("Fallback a ZOI dinámicas")
        dynamic_result = template_manager.calculate_dynamic_zoi(ocr_data_full_image, image_dimensions)
        return dynamic_result
