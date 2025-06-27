"""
Extractor de datos - Extracción dirigida, validación cruzada y heurísticas contextuales
Coordina la extracción precisa de campos usando plantillas o ZOI dinámicas
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
    """Extractor de datos con validación y heurísticas contextuales"""
    
    def __init__(self):
        self.validation_patterns = {
            'monto': [
                r'(\d{1,3}(?:\.\d{3})*,\d{2})',  # Formato venezolano: 1.234.567,89
                r'(\d{1,3}(?:,\d{3})*\.\d{2})',  # Formato internacional: 1,234,567.89
                r'(\d+[,\.]\d{2})',              # Formato simple: 1234,56 o 1234.56
                r'(\d+)'                         # Solo números
            ],
            'referencia': [
                r'(\d{8,15})',                   # 8-15 dígitos
                r'([A-Z0-9]{8,20})'              # Alfanumérico 8-20 caracteres
            ],
            'cedula': [
                r'([VE]-?\d{7,9})',              # V-12345678 o E-12345678
                r'(\d{7,9})'                     # Solo números 7-9 dígitos
            ],
            'fecha': [
                r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',  # DD/MM/YYYY o DD-MM-YYYY
                r'(\d{1,2}\s+de\s+\w+\s+de\s+\d{4})', # DD de Mes de YYYY
                r'(\d{4}-\d{2}-\d{2})'                 # YYYY-MM-DD
            ]
        }
    
    def extract_roi_from_image(self, image: np.ndarray, roi_data: Dict) -> np.ndarray:
        """Extrae región de interés de la imagen"""
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
            return roi
            
        except Exception as e:
            logger.error(f"Error extrayendo ROI: {e}")
            return np.array([])
    
    def save_roi_debug_image(self, roi: np.ndarray, field_name: str, temp_dir: Path):
        """Guarda imagen de ROI para depuración"""
        try:
            if roi.size > 0:
                debug_path = temp_dir / f"{field_name}_recorte.png"
                cv2.imwrite(str(debug_path), roi)
                logger.debug(f"ROI guardada para depuración: {debug_path}")
        except Exception as e:
            logger.warning(f"Error guardando ROI de depuración para {field_name}: {e}")
    
    def apply_contextual_heuristics(self, field_name: str, extracted_text: str, 
                                  confidence: float, ocr_data_full: Dict) -> Tuple[str, float]:
        """Aplica heurísticas contextuales para mejorar extracción"""
        try:
            # Si la extracción directa falló o tiene baja confianza, buscar en texto completo
            if not extracted_text.strip() or confidence < 50:
                logger.debug(f"Aplicando heurísticas contextuales para {field_name}")
                
                full_text = ocr_data_full.get('full_text', '')
                
                # Buscar patrones específicos según el tipo de campo
                patterns = self.validation_patterns.get(field_name, [])
                
                for pattern in patterns:
                    matches = re.findall(pattern, full_text, re.IGNORECASE)
                    if matches:
                        # Tomar la primera coincidencia válida
                        candidate = matches[0]
                        
                        # Validar el candidato
                        if self.validate_field_value(field_name, candidate):
                            logger.info(f"Heurística exitosa para {field_name}: '{candidate}'")
                            return candidate, min(confidence + 20, 95)  # Boost de confianza
                
                # Heurísticas específicas por campo
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
            
            # Buscar números cerca de palabras clave
            words = full_text.split()
            
            for i, word in enumerate(words):
                if any(keyword in word.lower() for keyword in amount_keywords):
                    # Buscar números en las siguientes 3 palabras
                    for j in range(i + 1, min(i + 4, len(words))):
                        candidate = words[j]
                        
                        # Limpiar y validar formato de monto
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
            # Buscar secuencias largas de números
            number_sequences = re.findall(r'\d{8,15}', full_text)
            
            if number_sequences:
                # Tomar la secuencia más larga
                longest = max(number_sequences, key=len)
                return longest, 70.0
            
            return "", 0.0
            
        except Exception as e:
            logger.warning(f"Error buscando número de referencia: {e}")
            return "", 0.0
    
    def find_cedula_number(self, full_text: str, field_name: str) -> Tuple[str, float]:
        """Busca números de cédula en el texto"""
        try:
            # Buscar patrones de cédula
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
                # Validar formato de monto
                cleaned = re.sub(r'[^\d,\.]', '', value)
                if not cleaned:
                    return False
                
                # Intentar convertir a float
                try:
                    # Normalizar formato
                    if ',' in cleaned and '.' in cleaned:
                        # Determinar cuál es el separador decimal
                        if cleaned.rfind(',') > cleaned.rfind('.'):
                            # Coma es decimal
                            amount_str = cleaned.replace('.', '').replace(',', '.')
                        else:
                            # Punto es decimal
                            amount_str = cleaned.replace(',', '')
                    elif ',' in cleaned:
                        # Solo coma - asumir decimal si hay 2 dígitos después
                        if len(cleaned.split(',')[-1]) == 2:
                            amount_str = cleaned.replace(',', '.')
                        else:
                            amount_str = cleaned.replace(',', '')
                    else:
                        amount_str = cleaned
                    
                    amount = float(amount_str)
                    return 0.01 <= amount <= 999999999.99  # Rango razonable
                    
                except ValueError:
                    return False
            
            elif field_name == 'referencia':
                # Validar longitud y formato de referencia
                cleaned = re.sub(r'[^\w]', '', value)
                return 6 <= len(cleaned) <= 20
            
            elif field_name in ['cedula_origen', 'cedula_destino']:
                # Validar formato de cédula
                cleaned = re.sub(r'[^\d]', '', value)
                return 7 <= len(cleaned) <= 9
            
            elif field_name == 'fecha':
                # Validar formato de fecha
                return self.validate_date_format(value)
            
            return True  # Para otros campos, aceptar cualquier valor no vacío
            
        except Exception as e:
            logger.warning(f"Error validando campo {field_name}: {e}")
            return False
    
    def validate_date_format(self, date_str: str) -> bool:
        """Valida formato de fecha y que no sea futura"""
        try:
            # Patrones de fecha comunes
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
            
            # Validar que no sea fecha futura (con margen de 1 día)
            tomorrow = datetime.now() + timedelta(days=1)
            return parsed_date <= tomorrow
            
        except Exception as e:
            logger.warning(f"Error validando fecha: {e}")
            return False
    
    def perform_cross_field_validation(self, extracted_data: Dict) -> Dict:
        """Realiza validación cruzada entre campos extraídos"""
        try:
            validation_results = {}
            
            # Validar consistencia entre campos
            monto = extracted_data.get('monto', {}).get('value', '')
            referencia = extracted_data.get('referencia', {}).get('value', '')
            fecha = extracted_data.get('fecha', {}).get('value', '')
            
            # Validación de monto
            if monto:
                monto_valid = self.validate_field_value('monto', monto)
                validation_results['monto_valid'] = monto_valid
                if not monto_valid:
                    logger.warning(f"Monto inválido detectado: {monto}")
            
            # Validación de referencia
            if referencia:
                ref_valid = self.validate_field_value('referencia', referencia)
                validation_results['referencia_valid'] = ref_valid
                if not ref_valid:
                    logger.warning(f"Referencia inválida detectada: {referencia}")
            
            # Validación de fecha
            if fecha:
                fecha_valid = self.validate_field_value('fecha', fecha)
                validation_results['fecha_valid'] = fecha_valid
                if not fecha_valid:
                    logger.warning(f"Fecha inválida detectada: {fecha}")
            
            # Validaciones de consistencia lógica
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
            
            # Colores para diferentes campos
            colors = {
                'monto': (0, 255, 0),      # Verde
                'referencia': (255, 0, 0),  # Rojo
                'fecha': (0, 0, 255),       # Azul
                'cedula_origen': (255, 255, 0),  # Amarillo
                'cedula_destino': (255, 0, 255), # Magenta
                'banco_origen': (0, 255, 255),   # Cian
                'banco_destino': (128, 128, 128) # Gris
            }
            
            for field_name, field_data in extracted_data.items():
                if isinstance(field_data, dict) and 'roi' in field_data:
                    roi = field_data['roi']
                    value = field_data.get('value', '')
                    confidence = field_data.get('confidence', 0)
                    
                    # Dibujar rectángulo
                    color = colors.get(field_name, (255, 255, 255))
                    cv2.rectangle(debug_image, 
                                (roi['left'], roi['top']),
                                (roi['left'] + roi['width'], roi['top'] + roi['height']),
                                color, 2)
                    
                    # Añadir etiqueta
                    label = f"{field_name}: {value} ({confidence:.0f}%)"
                    cv2.putText(debug_image, label,
                              (roi['left'], roi['top'] - 10),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            
            # Guardar imagen de debug
            debug_path = temp_dir / "debug_overlay.png"
            cv2.imwrite(str(debug_path), debug_image)
            logger.info(f"Debug overlay guardado: {debug_path}")
            
        except Exception as e:
            logger.warning(f"Error creando debug overlay: {e}")

def extract_data(preprocessed_image: np.ndarray, ocr_data_full: Dict, 
                template_or_zoi_data: Dict, temp_output_dir: Path, 
                learning_manager_instance) -> Dict:
    """
    Función principal de extracción de datos
    
    Args:
        preprocessed_image: Imagen preprocesada
        ocr_data_full: Datos completos de OCR
        template_or_zoi_data: Datos de plantilla o ZOI dinámicas
        temp_output_dir: Directorio temporal para debug
        learning_manager_instance: Instancia del gestor de aprendizaje
        
    Returns:
        Dict: Datos extraídos con validación y confianza
    """
    logger.info("Iniciando extracción dirigida de datos")
    
    extractor = DataExtractor()
    extraction_result = {
        'extraction_method': template_or_zoi_data.get('method', 'unknown'),
        'timestamp': datetime.now().isoformat(),
        'campos_extraidos': {},
        'validation_results': {},
        'overall_confidence': 0.0
    }
    
    try:
        # Obtener campos a extraer
        campos = template_or_zoi_data.get('campos', {})
        
        if not campos:
            logger.warning("No se encontraron campos para extraer")
            extraction_result['error'] = "no_fields_to_extract"
            return extraction_result
        
        total_confidence = 0.0
        successful_extractions = 0
        
        # Extraer cada campo
        for field_name, field_config in campos.items():
            logger.debug(f"Extrayendo campo: {field_name}")
            
            try:
                # Extraer ROI
                roi = extractor.extract_roi_from_image(preprocessed_image, field_config)
                
                if roi.size == 0:
                    logger.warning(f"ROI vacía para campo {field_name}")
                    continue
                
                # Guardar ROI para debug
                extractor.save_roi_debug_image(roi, field_name, temp_output_dir)
                
                # OCR dirigido
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
                   f"Confianza general: {extraction_result['overall_confidence']:.1f}%")
        
        return extraction_result
        
    except Exception as e:
        logger.error(f"Error durante extracción de datos: {e}", exc_info=True)
        extraction_result['error'] = str(e)
        extraction_result['status'] = 'extraction_error'
        return extraction_result
