"""
Extractor de datos v2.0 - Extracción directa desde OCR global
Sin reprocesamientos ni recortes individuales
"""

import cv2
import numpy as np
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging
import config

logger = logging.getLogger(__name__)

class DataExtractorV2:
    """Extractor de datos v2.0 - Basado en OCR global directo"""
    
    def __init__(self):
        self.validation_patterns = {
            'monto': [
                r'(\d{1,3}(?:\.\d{3})*,\d{2})',
                r'(\d{1,3}(?:,\d{3})*\.\d{2})',
                r'(\d+[,\.]\d{2})',
                r'(\d+)'
            ],
            'operacion': [
                r'(\d{8,15})',
                r'([A-Z0-9]{8,20})'
            ],
            'identificacion': [
                r'([VE]-?\d{7,9})',
                r'(\d{7,9})'
            ],
            'fecha': [
                r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'(\d{1,2}\s+de\s+\w+\s+de\s+\d{4})',
                r'(\d{4}-\d{2}-\d{2})'
            ]
        }
    
    def extract_field_value_direct(self, field_name: str, field_config: Dict, 
                                  ocr_data_global: Dict) -> Dict:
        """
        Extracción directa de valor desde OCR global
        NO realiza OCR adicional ni recortes
        """
        try:
            # Si el campo ya tiene valor extraído por template_manager_v2
            if 'value' in field_config and field_config['value']:
                logger.debug(f"Campo {field_name} ya extraído por template manager: '{field_config['value']}'")
                
                return {
                    'value': field_config['value'],
                    'confidence': field_config.get('confidence', 85),
                    'raw_ocr_output': field_config['value'],
                    'enhanced_output': field_config['value'],
                    'roi': field_config.get('roi', {}),
                    'extraction_method': field_config.get('extraction_method', 'direct_from_template_manager'),
                    'extraction_successful': True
                }
            
            # Fallback: Buscar en texto completo usando heurísticas
            logger.debug(f"Aplicando heurísticas de fallback para {field_name}")
            
            full_text = ocr_data_global.get('full_text', '')
            enhanced_text, enhanced_confidence = self.apply_contextual_heuristics(
                field_name, "", 0, ocr_data_global
            )
            
            return {
                'value': enhanced_text,
                'confidence': enhanced_confidence,
                'raw_ocr_output': 'HEURISTIC_FALLBACK',
                'enhanced_output': enhanced_text,
                'roi': {},
                'extraction_method': 'contextual_heuristics',
                'extraction_successful': bool(enhanced_text.strip())
            }
            
        except Exception as e:
            logger.error(f"Error en extracción directa para {field_name}: {e}")
            return {
                'value': '',
                'confidence': 0.0,
                'error': str(e),
                'extraction_successful': False
            }
    
    def apply_contextual_heuristics(self, field_name: str, extracted_text: str, 
                                  confidence: float, ocr_data_full: Dict) -> Tuple[str, float]:
        """Aplica heurísticas contextuales mejoradas"""
        try:
            full_text = ocr_data_full.get('full_text', '')
            patterns = self.validation_patterns.get(field_name, [])
            
            for pattern in patterns:
                matches = re.findall(pattern, full_text, re.IGNORECASE)
                if matches:
                    candidate = matches[0]
                    if self.validate_field_value(field_name, candidate):
                        logger.info(f"Heurística exitosa para {field_name}: '{candidate}'")
                        return candidate, min(confidence + 30, 95)
            
            # Heurísticas específicas por campo
            if field_name in ['monto', 'operacion', 'identificacion']:
                return self.find_field_by_type(field_name, full_text)
            
            return extracted_text, confidence
            
        except Exception as e:
            logger.error(f"Error en heurísticas contextuales para {field_name}: {e}")
            return extracted_text, confidence
    
    def find_field_by_type(self, field_name: str, full_text: str) -> Tuple[str, float]:
        """Busca campos por tipo específico"""
        try:
            if field_name == 'monto':
                # Buscar patrones de monto
                amount_patterns = [
                    r'\b\d{1,3}(?:\.\d{3})*,\d{2}\b',  # 1.234,56
                    r'\b\d+,\d{2}\b',                   # 1234,56
                    r'\b\d+\.\d{2}\b'                   # 1234.56
                ]
                
                for pattern in amount_patterns:
                    matches = re.findall(pattern, full_text)
                    if matches:
                        # Tomar el monto más grande (probablemente el principal)
                        amounts = []
                        for match in matches:
                            try:
                                # Normalizar formato
                                normalized = match.replace('.', '').replace(',', '.')
                                amounts.append((float(normalized), match))
                            except ValueError:
                                continue
                        
                        if amounts:
                            largest_amount = max(amounts, key=lambda x: x[0])
                            return largest_amount[1], 80.0
            
            elif field_name == 'operacion':
                # Buscar números largos (referencias de operación)
                ref_matches = re.findall(r'\b\d{8,15}\b', full_text)
                if ref_matches:
                    # Tomar el más largo
                    longest_ref = max(ref_matches, key=len)
                    return longest_ref, 75.0
            
            elif field_name == 'identificacion':
                # Buscar patrones de cédula
                cedula_patterns = [
                    r'\b[VE]-?\d{7,9}\b',
                    r'\bC\.?I\.?\s*:?\s*\d{7,9}\b'
                ]
                
                for pattern in cedula_patterns:
                    matches = re.findall(pattern, full_text, re.IGNORECASE)
                    if matches:
                        return matches[0], 70.0
            
            return "", 0.0
            
        except Exception as e:
            logger.warning(f"Error buscando campo por tipo {field_name}: {e}")
            return "", 0.0
    
    def validate_field_value(self, field_name: str, value: str) -> bool:
        """Valida que un valor extraído sea coherente"""
        try:
            if not value or not value.strip():
                return False
            
            value = value.strip()
            
            if field_name == 'monto':
                cleaned = re.sub(r'[^\d,\.]', '', value)
                if not cleaned:
                    return False
                
                try:
                    if ',' in cleaned and '.' in cleaned:
                        if cleaned.rfind(',') > cleaned.rfind('.'):
                            amount_str = cleaned.replace('.', '').replace(',', '.')
                        else:
                            amount_str = cleaned.replace(',', '')
                    elif ',' in cleaned:
                        if len(cleaned.split(',')[-1]) == 2:
                            amount_str = cleaned.replace(',', '.')
                        else:
                            amount_str = cleaned.replace(',', '')
                    else:
                        amount_str = cleaned
                    
                    amount = float(amount_str)
                    return 0.01 <= amount <= 999999999.99
                    
                except ValueError:
                    return False
            
            elif field_name == 'operacion':
                cleaned = re.sub(r'[^\w]', '', value)
                return 6 <= len(cleaned) <= 20
            
            elif field_name == 'identificacion':
                cleaned = re.sub(r'[^\d]', '', value)
                return 7 <= len(cleaned) <= 9
            
            elif field_name == 'fecha':
                return self.validate_date_format(value)
            
            return True
            
        except Exception as e:
            logger.warning(f"Error validando campo {field_name}: {e}")
            return False
    
    def validate_date_format(self, date_str: str) -> bool:
        """Valida formato de fecha"""
        try:
            date_patterns = [
                '%d/%m/%Y', '%d-%m-%Y', '%d/%m/%y', '%d-%m-%y',
                '%Y-%m-%d'
            ]
            
            for pattern in date_patterns:
                try:
                    parsed_date = datetime.strptime(date_str, pattern)
                    tomorrow = datetime.now() + timedelta(days=1)
                    return parsed_date <= tomorrow
                except ValueError:
                    continue
            
            return False
            
        except Exception as e:
            logger.warning(f"Error validando fecha: {e}")
            return False
    
    def perform_cross_field_validation(self, extracted_data: Dict) -> Dict:
        """Realiza validación cruzada entre campos extraídos"""
        try:
            validation_results = {}
            
            # Validar campos principales
            for field_name in ['monto', 'operacion', 'identificacion', 'fecha']:
                field_data = extracted_data.get(field_name, {})
                value = field_data.get('value', '')
                
                if value:
                    is_valid = self.validate_field_value(field_name, value)
                    validation_results[f'{field_name}_valid'] = is_valid
                    if not is_valid:
                        logger.warning(f"Campo {field_name} inválido: {value}")
            
            # Validación cruzada general
            validation_results['cross_validation_passed'] = all([
                validation_results.get('monto_valid', True),
                validation_results.get('operacion_valid', True),
                validation_results.get('identificacion_valid', True),
                validation_results.get('fecha_valid', True)
            ])
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Error en validación cruzada: {e}")
            return {'cross_validation_passed': False, 'error': str(e)}
    
    def create_debug_overlay_v2(self, image: np.ndarray, extracted_data: Dict, temp_dir: Path):
        """Crea overlay de debug v2.0 - Basado en bbox del OCR global"""
        try:
            debug_image = image.copy()
            
            colors = {
                'monto': (0, 255, 0),
                'operacion': (255, 0, 0),
                'fecha': (0, 0, 255),
                'identificacion': (255, 255, 0),
                'origen_numero': (255, 0, 255),
                'destino_numero': (0, 255, 255),
                'banco_completo': (128, 128, 128),
                'concepto': (255, 128, 0)
            }
            
            for field_name, field_data in extracted_data.items():
                if isinstance(field_data, dict) and 'roi' in field_data and field_data['roi']:
                    roi = field_data['roi']
                    value = field_data.get('value', '')
                    confidence = field_data.get('confidence', 0)
                    
                    # Usar bbox del OCR global si está disponible
                    if 'left' in roi and 'top' in roi:
                        color = colors.get(field_name, (255, 255, 255))
                        
                        cv2.rectangle(debug_image, 
                                    (roi['left'], roi['top']),
                                    (roi['left'] + roi.get('width', 50), roi['top'] + roi.get('height', 20)),
                                    color, 2)
                        
                        label = f"{field_name}: {value} ({confidence:.0f}%)"
                        cv2.putText(debug_image, label,
                                  (roi['left'], roi['top'] - 10),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            
            debug_path = temp_dir / "debug_overlay_v2.png"
            cv2.imwrite(str(debug_path), debug_image)
            logger.info(f"Debug overlay v2.0 guardado: {debug_path}")
            
        except Exception as e:
            logger.warning(f"Error creando debug overlay v2.0: {e}")

def extract_data_v2(preprocessed_image: np.ndarray, ocr_data_full: Dict, 
                   template_or_zoi_data: Dict, temp_output_dir: Path, 
                   learning_manager_instance) -> Dict:
    """
    FUNCIÓN PRINCIPAL v2.0: Extracción directa desde OCR global
    Sin reprocesamientos ni recortes individuales
    """
    logger.info("Iniciando extracción de datos v2.0 - Directa desde OCR global")
    
    extractor = DataExtractorV2()
    extraction_result = {
        'extraction_method': template_or_zoi_data.get('method', 'unknown'),
        'extraction_version': 'v2.0_direct_from_global_ocr',
        'timestamp': datetime.now().isoformat(),
        'campos_extraidos': {},
        'validation_results': {},
        'overall_confidence': 0.0
    }
    
    try:
        campos = template_or_zoi_data.get('campos', {})
        
        if not campos:
            logger.warning("No se encontraron campos para extraer")
            extraction_result['error'] = "no_fields_to_extract"
            return extraction_result
        
        total_confidence = 0.0
        successful_extractions = 0
        
        # Extraer cada campo directamente (sin OCR adicional)
        for field_name, field_config in campos.items():
            logger.debug(f"Extrayendo campo v2.0: {field_name}")
            
            try:
                # Extracción directa desde OCR global
                field_result = extractor.extract_field_value_direct(
                    field_name, field_config, ocr_data_full
                )
                
                # Aplicar corrección probabilística si está disponible
                if learning_manager_instance and field_result['extraction_successful']:
                    corrected_text, final_confidence = learning_manager_instance.get_probabilistic_correction(
                        field_name, field_result['value'], field_result['confidence']
                    )
                    
                    field_result['value'] = corrected_text
                    field_result['confidence'] = final_confidence
                    field_result['probabilistic_correction_applied'] = True
                
                extraction_result['campos_extraidos'][field_name] = field_result
                
                if field_result['extraction_successful']:
                    total_confidence += field_result['confidence']
                    successful_extractions += 1
                
                logger.debug(f"Campo {field_name} v2.0 extraído: '{field_result['value']}' "
                           f"(confianza: {field_result['confidence']:.1f})")
                
            except Exception as e:
                logger.error(f"Error extrayendo campo {field_name} v2.0: {e}")
                extraction_result['campos_extraidos'][field_name] = {
                    'value': '',
                    'confidence': 0.0,
                    'error': str(e),
                    'extraction_successful': False
                }
        
        # Calcular confianza general
        if successful_extractions > 0:
            extraction_result['overall_confidence'] = total_confidence / successful_extractions
        
        # Validación cruzada
        validation_results = extractor.perform_cross_field_validation(
            extraction_result['campos_extraidos']
        )
        extraction_result['validation_results'] = validation_results
        
        # Crear debug overlay v2.0 si está habilitado
        if not config.CLEAN_TEMP_FILES:
            extractor.create_debug_overlay_v2(
                preprocessed_image, 
                extraction_result['campos_extraidos'], 
                temp_output_dir
            )
        
        # Determinar estado general
        if successful_extractions == 0:
            extraction_result['status'] = 'no_data_extracted'
        elif not validation_results.get('cross_validation_passed', False):
            extraction_result['status'] = 'validation_failed'
        elif extraction_result['overall_confidence'] < 50:
            extraction_result['status'] = 'low_confidence'
        else:
            extraction_result['status'] = 'success'
        
        logger.info(f"Extracción v2.0 completada - Estado: {extraction_result['status']}, "
                   f"Campos extraídos: {successful_extractions}, "
                   f"Confianza general: {extraction_result['overall_confidence']:.1f}%")
        
        return extraction_result
        
    except Exception as e:
        logger.error(f"Error durante extracción de datos v2.0: {e}", exc_info=True)
        extraction_result['error'] = str(e)
        extraction_result['status'] = 'extraction_error'
        return extraction_result
