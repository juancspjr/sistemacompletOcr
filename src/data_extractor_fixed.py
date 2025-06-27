"""
Extractor de datos CORREGIDO - Validación de ROI antes de OCR
Añade verificación de ROI válidas antes de enviar a Tesseract
"""

import cv2
import numpy as np
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging
import config
from ocr_engine import perform_directed_ocr

logger = logging.getLogger(__name__)

class DataExtractor:
    """Extractor de datos con validación de ROI mejorada"""
    
    def __init__(self):
        self.validation_patterns = {
            'monto': [
                r'(\d{1,3}(?:\.\d{3})*,\d{2})',
                r'(\d{1,3}(?:,\d{3})*\.\d{2})',
                r'(\d+[,\.]\d{2})',
                r'(\d+)'
            ],
            'referencia': [
                r'(\d{8,15})',
                r'([A-Z0-9]{8,20})'
            ],
            'cedula': [
                r'([VE]-?\d{7,9})',
                r'(\d{7,9})'
            ],
            'fecha': [
                r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'(\d{1,2}\s+de\s+\w+\s+de\s+\d{4})',
                r'(\d{4}-\d{2}-\d{2})'
            ]
        }
    
    def validate_roi_content(self, roi: np.ndarray, field_name: str) -> Tuple[bool, Dict]:
        """
        NUEVA FUNCIÓN: Valida que la ROI contenga contenido útil antes del OCR
        """
        validation_info = {
            "is_valid": False,
            "reason": "unknown",
            "content_metrics": {}
        }
        
        try:
            if roi.size == 0:
                validation_info["reason"] = "empty_roi"
                return False, validation_info
            
            # Convertir a escala de grises si es necesario
            if len(roi.shape) == 3:
                gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            else:
                gray_roi = roi.copy()
            
            height, width = gray_roi.shape
            total_pixels = height * width
            
            # Métricas de contenido
            unique_values = len(np.unique(gray_roi))
            mean_intensity = np.mean(gray_roi)
            std_intensity = np.std(gray_roi)
            
            # Contar píxeles no blancos (asumiendo que el texto es oscuro)
            non_white_pixels = np.sum(gray_roi < 240)
            non_white_ratio = non_white_pixels / total_pixels
            
            validation_info["content_metrics"] = {
                "dimensions": (width, height),
                "total_pixels": total_pixels,
                "unique_values": unique_values,
                "mean_intensity": float(mean_intensity),
                "std_intensity": float(std_intensity),
                "non_white_pixels": int(non_white_pixels),
                "non_white_ratio": float(non_white_ratio)
            }
            
            # Criterios de validación
            min_dimension = 10
            min_non_white_ratio = 0.05  # Al menos 5% de píxeles no blancos
            min_std = 10  # Mínima variación de intensidad
            min_unique_values = 3  # Al menos 3 valores únicos de intensidad
            
            # Validaciones
            if width < min_dimension or height < min_dimension:
                validation_info["reason"] = f"roi_too_small_{width}x{height}"
                return False, validation_info
            
            if non_white_ratio < min_non_white_ratio:
                validation_info["reason"] = f"insufficient_content_{non_white_ratio:.3f}"
                return False, validation_info
            
            if std_intensity < min_std:
                validation_info["reason"] = f"low_contrast_{std_intensity:.1f}"
                return False, validation_info
            
            if unique_values < min_unique_values:
                validation_info["reason"] = f"low_variation_{unique_values}"
                return False, validation_info
            
            # ROI válida
            validation_info["is_valid"] = True
            validation_info["reason"] = "valid_content"
            
            logger.debug(f"ROI válida para {field_name}: {width}x{height}, "
                        f"contenido: {non_white_ratio:.3f}, contraste: {std_intensity:.1f}")
            
            return True, validation_info
            
        except Exception as e:
            logger.error(f"Error validando ROI para {field_name}: {e}")
            validation_info["reason"] = f"validation_error_{str(e)}"
            return False, validation_info
    
    def extract_roi_from_image(self, image: np.ndarray, roi_data: Dict) -> np.ndarray:
        """Extrae región de interés de la imagen con validación mejorada"""
        try:
            left = roi_data['left']
            top = roi_data['top']
            width = roi_data['width']
            height = roi_data['height']
            
            # Validar coordenadas
            img_height, img_width = image.shape[:2]
            left = max(0, min(left, img_width - 1))
            top = max(0, min(top, img_height - 1))
            right = min(left + width, img_width)
            bottom = min(top + height, img_height)
            
            if right <= left or bottom <= top:
                logger.warning(f"ROI inválida: left={left}, top={top}, right={right}, bottom={bottom}")
                return np.array([])
            
            roi = image[top:bottom, left:right]
            
            # Log de información de extracción
            logger.debug(f"ROI extraída: {roi.shape} desde ({left},{top}) hasta ({right},{bottom})")
            
            return roi
            
        except Exception as e:
            logger.error(f"Error extrayendo ROI: {e}")
            return np.array([])
    
    def save_roi_debug_image(self, roi: np.ndarray, field_name: str, temp_dir: Path, 
                           validation_info: Dict = None):
        """Guarda imagen de ROI para depuración con información de validación"""
        try:
            if roi.size > 0:
                debug_path = temp_dir / f"{field_name}_recorte.png"
                cv2.imwrite(str(debug_path), roi)
                
                # Guardar información de validación
                if validation_info:
                    info_path = temp_dir / f"{field_name}_validation_info.txt"
                    with open(info_path, 'w') as f:
                        f.write(f"Campo: {field_name}\n")
                        f.write(f"Válido: {validation_info.get('is_valid', False)}\n")
                        f.write(f"Razón: {validation_info.get('reason', 'unknown')}\n")
                        f.write(f"Métricas: {validation_info.get('content_metrics', {})}\n")
                
                logger.debug(f"ROI guardada para depuración: {debug_path}")
            else:
                # Crear imagen en blanco para indicar ROI vacía
                blank_image = np.ones((50, 200, 3), dtype=np.uint8) * 255
                debug_path = temp_dir / f"{field_name}_recorte_VACIO.png"
                cv2.imwrite(str(debug_path), blank_image)
                logger.warning(f"ROI vacía guardada: {debug_path}")
                
        except Exception as e:
            logger.warning(f"Error guardando ROI de depuración para {field_name}: {e}")
    
    def apply_contextual_heuristics(self, field_name: str, extracted_text: str, 
                                  confidence: float, ocr_data_full: Dict) -> Tuple[str, float]:
        """Aplica heurísticas contextuales para mejorar extracción"""
        try:
            if not extracted_text.strip() or confidence < 50:
                logger.debug(f"Aplicando heurísticas contextuales para {field_name}")
                
                full_text = ocr_data_full.get('full_text', '')
                patterns = self.validation_patterns.get(field_name, [])
                
                for pattern in patterns:
                    matches = re.findall(pattern, full_text, re.IGNORECASE)
                    if matches:
                        candidate = matches[0]
                        if self.validate_field_value(field_name, candidate):
                            logger.info(f"Heurística exitosa para {field_name}: '{candidate}'")
                            return candidate, min(confidence + 20, 95)
                
                if field_name == 'monto':
                    return self.find_amount_near_keywords(full_text, ocr_data_full)
                elif field_name == 'referencia':
                    return self.find_reference_number(full_text)
                elif field_name in ['cedula_origen', 'cedula_destino']:
                    return self.find_cedula_number(full_text, field_name)
            
            return extracted_text, confidence
            
        except Exception as e:
            logger.error(f"Error en heurísticas contextuales para {field_name}: {e}")
            return extracted_text, confidence
    
    def find_amount_near_keywords(self, full_text: str, ocr_data_full: Dict) -> Tuple[str, float]:
        """Busca montos cerca de palabras clave como 'Bs', 'Monto', 'Total'"""
        try:
            amount_keywords = ['bs', 'monto', 'total', 'cantidad', 'bolivares']
            words = full_text.split()
            
            for i, word in enumerate(words):
                if any(keyword in word.lower() for keyword in amount_keywords):
                    for j in range(i + 1, min(i + 4, len(words))):
                        candidate = words[j]
                        cleaned = re.sub(r'[^\d,\.]', '', candidate)
                        if self.validate_field_value('monto', cleaned):
                            return cleaned, 75.0
            
            return "", 0.0
            
        except Exception as e:
            logger.warning(f"Error buscando monto cerca de palabras clave: {e}")
            return "", 0.0
    
    def find_reference_number(self, full_text: str) -> Tuple[str, float]:
        """Busca números de referencia largos en el texto"""
        try:
            number_sequences = re.findall(r'\d{8,15}', full_text)
            if number_sequences:
                longest = max(number_sequences, key=len)
                return longest, 70.0
            return "", 0.0
            
        except Exception as e:
            logger.warning(f"Error buscando número de referencia: {e}")
            return "", 0.0
    
    def find_cedula_number(self, full_text: str, field_name: str) -> Tuple[str, float]:
        """Busca números de cédula en el texto"""
        try:
            cedula_patterns = [
                r'[VE]-?\d{7,9}',
                r'C\.?I\.?\s*:?\s*\d{7,9}',
                r'\d{7,9}'
            ]
            
            for pattern in cedula_patterns:
                matches = re.findall(pattern, full_text, re.IGNORECASE)
                if matches:
                    return matches[0], 65.0
            
            return "", 0.0
            
        except Exception as e:
            logger.warning(f"Error buscando cédula: {e}")
            return "", 0.0
    
    def validate_field_value(self, field_name: str, value: str) -> bool:
        """Valida que un valor extraído sea coherente para el tipo de campo"""
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
            
            elif field_name == 'referencia':
                cleaned = re.sub(r'[^\w]', '', value)
                return 6 <= len(cleaned) <= 20
            
            elif field_name in ['cedula_origen', 'cedula_destino']:
                cleaned = re.sub(r'[^\d]', '', value)
                return 7 <= len(cleaned) <= 9
            
            elif field_name == 'fecha':
                return self.validate_date_format(value)
            
            return True
            
        except Exception as e:
            logger.warning(f"Error validando campo {field_name}: {e}")
            return False
    
    def validate_date_format(self, date_str: str) -> bool:
        """Valida formato de fecha y que no sea futura"""
        try:
            date_patterns = [
                '%d/%m/%Y', '%d-%m-%Y', '%d/%m/%y', '%d-%m-%y',
                '%Y-%m-%d', '%d de %B de %Y'
            ]
            
            parsed_date = None
            
            for pattern in date_patterns:
                try:
                    parsed_date = datetime.strptime(date_str, pattern)
                    break
                except ValueError:
                    continue
            
            if not parsed_date:
                return False
            
            tomorrow = datetime.now() + timedelta(days=1)
            return parsed_date <= tomorrow
            
        except Exception as e:
            logger.warning(f"Error validando fecha: {e}")
            return False
    
    def perform_cross_field_validation(self, extracted_data: Dict) -> Dict:
        """Realiza validación cruzada entre campos extraídos"""
        try:
            validation_results = {}
            
            monto = extracted_data.get('monto', {}).get('value', '')
            referencia = extracted_data.get('referencia', {}).get('value', '')
            fecha = extracted_data.get('fecha', {}).get('value', '')
            
            if monto:
                monto_valid = self.validate_field_value('monto', monto)
                validation_results['monto_valid'] = monto_valid
                if not monto_valid:
                    logger.warning(f"Monto inválido detectado: {monto}")
            
            if referencia:
                ref_valid = self.validate_field_value('referencia', referencia)
                validation_results['referencia_valid'] = ref_valid
                if not ref_valid:
                    logger.warning(f"Referencia inválida detectada: {referencia}")
            
            if fecha:
                fecha_valid = self.validate_field_value('fecha', fecha)
                validation_results['fecha_valid'] = fecha_valid
                if not fecha_valid:
                    logger.warning(f"Fecha inválida detectada: {fecha}")
            
            validation_results['cross_validation_passed'] = all([
                validation_results.get('monto_valid', True),
                validation_results.get('referencia_valid', True),
                validation_results.get('fecha_valid', True)
            ])
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Error en validación cruzada: {e}")
            return {'cross_validation_passed': False, 'error': str(e)}
    
    def create_debug_overlay(self, image: np.ndarray, extracted_data: Dict, temp_dir: Path):
        """Crea imagen con overlay de debug mostrando campos detectados"""
        try:
            debug_image = image.copy()
            
            colors = {
                'monto': (0, 255, 0),
                'referencia': (255, 0, 0),
                'fecha': (0, 0, 255),
                'cedula_origen': (255, 255, 0),
                'cedula_destino': (255, 0, 255),
                'banco_origen': (0, 255, 255),
                'banco_destino': (128, 128, 128)
            }
            
            for field_name, field_data in extracted_data.items():
                if isinstance(field_data, dict) and 'roi' in field_data:
                    roi = field_data['roi']
                    value = field_data.get('value', '')
                    confidence = field_data.get('confidence', 0)
                    
                    color = colors.get(field_name, (255, 255, 255))
                    cv2.rectangle(debug_image, 
                                (roi['left'], roi['top']),
                                (roi['left'] + roi['width'], roi['top'] + roi['height']),
                                color, 2)
                    
                    label = f"{field_name}: {value} ({confidence:.0f}%)"
                    cv2.putText(debug_image, label,
                              (roi['left'], roi['top'] - 10),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            
            debug_path = temp_dir / "debug_overlay.png"
            cv2.imwrite(str(debug_path), debug_image)
            logger.info(f"Debug overlay guardado: {debug_path}")
            
        except Exception as e:
            logger.warning(f"Error creando debug overlay: {e}")

def extract_data(preprocessed_image: np.ndarray, ocr_data_full: Dict, 
                template_or_zoi_data: Dict, temp_output_dir: Path, 
                learning_manager_instance) -> Dict:
    """
    Función principal de extracción de datos CORREGIDA con validación de ROI
    """
    logger.info("Iniciando extracción dirigida de datos con validación de ROI")
    
    extractor = DataExtractor()
    extraction_result = {
        'extraction_method': template_or_zoi_data.get('method', 'unknown'),
        'timestamp': datetime.now().isoformat(),
        'campos_extraidos': {},
        'validation_results': {},
        'roi_validation_summary': {},
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
        roi_validation_stats = {'valid': 0, 'invalid': 0, 'reasons': {}}
        
        for field_name, field_config in campos.items():
            logger.debug(f"Extrayendo campo: {field_name}")
            
            try:
                # Extraer ROI
                roi = extractor.extract_roi_from_image(preprocessed_image, field_config)
                
                # VALIDAR ROI ANTES DE OCR
                roi_valid, validation_info = extractor.validate_roi_content(roi, field_name)
                
                # Actualizar estadísticas de validación
                if roi_valid:
                    roi_validation_stats['valid'] += 1
                else:
                    roi_validation_stats['invalid'] += 1
                    reason = validation_info.get('reason', 'unknown')
                    roi_validation_stats['reasons'][reason] = roi_validation_stats['reasons'].get(reason, 0) + 1
                
                # Guardar ROI para debug con información de validación
                extractor.save_roi_debug_image(roi, field_name, temp_output_dir, validation_info)
                
                if not roi_valid:
                    logger.warning(f"ROI inválida para campo {field_name}: {validation_info.get('reason')}")
                    
                    # Intentar heurísticas directamente sin OCR
                    enhanced_text, enhanced_confidence = extractor.apply_contextual_heuristics(
                        field_name, "", 0, ocr_data_full
                    )
                    
                    extraction_result['campos_extraidos'][field_name] = {
                        'value': enhanced_text,
                        'confidence': enhanced_confidence,
                        'raw_ocr_output': 'ROI_INVALID',
                        'enhanced_output': enhanced_text,
                        'roi': field_config,
                        'roi_validation': validation_info,
                        'extraction_successful': bool(enhanced_text.strip())
                    }
                    
                    if enhanced_text.strip():
                        total_confidence += enhanced_confidence
                        successful_extractions += 1
                        logger.info(f"Campo {field_name} extraído por heurísticas: '{enhanced_text}'")
                    
                    continue
                
                # ROI válida - proceder con OCR
                psm_mode = field_config.get('psm_mode', config.TESSERACT_PSM_LINE_OCR)
                extracted_text, confidence = perform_directed_ocr(roi, psm_mode)
                
                # Aplicar heurísticas contextuales
                enhanced_text, enhanced_confidence = extractor.apply_contextual_heuristics(
                    field_name, extracted_text, confidence, ocr_data_full
                )
                
                # Consultar modelo probabilístico
                corrected_text, final_confidence = learning_manager_instance.get_probabilistic_correction(
                    field_name, enhanced_text, enhanced_confidence
                )
                
                # Almacenar resultado
                extraction_result['campos_extraidos'][field_name] = {
                    'value': corrected_text,
                    'confidence': final_confidence,
                    'raw_ocr_output': extracted_text,
                    'enhanced_output': enhanced_text,
                    'roi': field_config,
                    'roi_validation': validation_info,
                    'extraction_successful': bool(corrected_text.strip())
                }
                
                if corrected_text.strip():
                    total_confidence += final_confidence
                    successful_extractions += 1
                
                logger.debug(f"Campo {field_name} extraído: '{corrected_text}' (confianza: {final_confidence:.1f})")
                
            except Exception as e:
                logger.error(f"Error extrayendo campo {field_name}: {e}")
                extraction_result['campos_extraidos'][field_name] = {
                    'value': '',
                    'confidence': 0.0,
                    'error': str(e),
                    'extraction_successful': False
                }
        
        # Guardar estadísticas de validación de ROI
        extraction_result['roi_validation_summary'] = roi_validation_stats
        
        # Calcular confianza general
        if successful_extractions > 0:
            extraction_result['overall_confidence'] = total_confidence / successful_extractions
        
        # Validación cruzada
        validation_results = extractor.perform_cross_field_validation(
            extraction_result['campos_extraidos']
        )
        extraction_result['validation_results'] = validation_results
        
        # Crear debug overlay si no se van a limpiar archivos temporales
        if not config.CLEAN_TEMP_FILES:
            extractor.create_debug_overlay(
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
        
        logger.info(f"Extracción completada - Estado: {extraction_result['status']}, "
                   f"Campos extraídos: {successful_extractions}, "
                   f"ROI válidas: {roi_validation_stats['valid']}/{roi_validation_stats['valid'] + roi_validation_stats['invalid']}, "
                   f"Confianza general: {extraction_result['overall_confidence']:.1f}%")
        
        return extraction_result
        
    except Exception as e:
        logger.error(f"Error durante extracción de datos: {e}", exc_info=True)
        extraction_result['error'] = str(e)
        extraction_result['status'] = 'extraction_error'
        return extraction_result
