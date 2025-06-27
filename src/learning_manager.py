"""
Gestor de aprendizaje - Manejo del feedback, modelo probabilístico y registro histórico
Implementa el bucle de aprendizaje semántico del sistema
"""

import json
import pandas as pd
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Tuple, Optional
import logging
import config

logger = logging.getLogger(__name__)

class LearningManager:
    """Gestor del modelo probabilístico y sistema de aprendizaje"""
    
    def __init__(self):
        self.probabilistic_model = {}
        self.load_probabilistic_model()
    
    def load_probabilistic_model(self):
        """Carga el modelo probabilístico desde archivo JSON"""
        try:
            if config.PROBABILISTIC_MODEL_PATH.exists():
                with open(config.PROBABILISTIC_MODEL_PATH, 'r', encoding='utf-8') as f:
                    self.probabilistic_model = json.load(f)
                logger.info(f"Modelo probabilístico cargado: {len(self.probabilistic_model)} campos")
            else:
                # Crear modelo vacío inicial
                self.probabilistic_model = {}
                self.save_probabilistic_model()
                logger.info("Modelo probabilístico inicializado vacío")
                
        except Exception as e:
            logger.error(f"Error cargando modelo probabilístico: {e}")
            self.probabilistic_model = {}
    
    def save_probabilistic_model(self):
        """Guarda el modelo probabilístico a archivo JSON"""
        try:
            with open(config.PROBABILISTIC_MODEL_PATH, 'w', encoding='utf-8') as f:
                json.dump(self.probabilistic_model, f, ensure_ascii=False, indent=2)
            logger.debug("Modelo probabilístico guardado")
            
        except Exception as e:
            logger.error(f"Error guardando modelo probabilístico: {e}")
    
    def get_probabilistic_correction(self, field_name: str, raw_ocr_output: str, 
                                   current_confidence: float) -> Tuple[str, float]:
        """
        Obtiene corrección probabilística basada en historial de feedback
        
        Args:
            field_name: Nombre del campo
            raw_ocr_output: Salida cruda de OCR
            current_confidence: Confianza actual
            
        Returns:
            Tuple[str, float]: (valor_sugerido, confianza_ajustada)
        """
        try:
            # Si no hay datos para este campo, retornar valores originales
            if field_name not in self.probabilistic_model:
                return raw_ocr_output, current_confidence
            
            field_model = self.probabilistic_model[field_name]
            
            # Si no hay datos para esta salida específica de OCR
            if raw_ocr_output not in field_model:
                return raw_ocr_output, current_confidence
            
            ocr_history = field_model[raw_ocr_output]
            
            # Encontrar la corrección más frecuente
            best_correction = None
            best_count = 0
            
            for correction, data in ocr_history.items():
                if correction in ['total_correcciones', 'last_updated', 'confidence_adjustment']:
                    continue
                
                count = data.get('count', 0)
                if count > best_count:
                    best_count = count
                    best_correction = correction
            
            if best_correction and best_count > 0:
                # Aplicar corrección probabilística
                confidence_adjustment = ocr_history.get('confidence_adjustment', 0.0)
                adjusted_confidence = max(0.0, min(100.0, current_confidence + confidence_adjustment))
                
                logger.debug(f"Corrección probabilística aplicada para {field_name}: "
                           f"'{raw_ocr_output}' -> '{best_correction}' "
                           f"(confianza: {current_confidence:.1f} -> {adjusted_confidence:.1f})")
                
                return best_correction, adjusted_confidence
            
            return raw_ocr_output, current_confidence
            
        except Exception as e:
            logger.error(f"Error en corrección probabilística para {field_name}: {e}")
            return raw_ocr_output, current_confidence
    
    def save_processing_record(self, extraction_result: Dict, original_image_path: Path):
        """
        Guarda registro de procesamiento y mueve imagen original al archivo
        
        Args:
            extraction_result: Resultado de la extracción
            original_image_path: Ruta de la imagen original
        """
        try:
            # Generar nombre único para el registro
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            image_name = original_image_path.stem
            
            # Guardar JSON de resultado
            json_filename = f"{timestamp}-{image_name}.json"
            json_path = config.PROCESSED_RECEIPTS_DIR / json_filename
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(extraction_result, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Registro de procesamiento guardado: {json_path}")
            
            # Mover imagen original al archivo
            archive_filename = f"{timestamp}-{original_image_path.name}"
            archive_path = config.PROCESSED_IMAGES_ARCHIVE_DIR / archive_filename
            
            if original_image_path.exists():
                shutil.move(str(original_image_path), str(archive_path))
                logger.info(f"Imagen original archivada: {archive_path}")
            
        except Exception as e:
            logger.error(f"Error guardando registro de procesamiento: {e}")
    
    def initialize_feedback_csv(self):
        """Inicializa el archivo CSV de feedback manual si no existe"""
        try:
            if not config.MANUAL_FEEDBACK_CSV_FILE.exists():
                # Crear CSV con headers
                headers = [
                    'id_unico_imagen',
                    'campo_nombre', 
                    'raw_ocr_output',
                    'valor_corregido',
                    'causa_raiz',
                    'timestamp_feedback'
                ]
                
                df = pd.DataFrame(columns=headers)
                df.to_csv(config.MANUAL_FEEDBACK_CSV_FILE, index=False, encoding='utf-8')
                
                logger.info(f"Archivo de feedback inicializado: {config.MANUAL_FEEDBACK_CSV_FILE}")
                
        except Exception as e:
            logger.error(f"Error inicializando archivo de feedback: {e}")
    
    def add_feedback_entry(self, image_id: str, field_name: str, raw_ocr: str, 
                          corrected_value: str, root_cause: str):
        """
        Añade entrada de feedback manual al CSV
        
        Args:
            image_id: ID único de la imagen
            field_name: Nombre del campo corregido
            raw_ocr: Salida original de OCR
            corrected_value: Valor corregido
            root_cause: Causa raíz del error
        """
        try:
            # Asegurar que el CSV existe
            self.initialize_feedback_csv()
            
            # Crear nueva entrada
            new_entry = {
                'id_unico_imagen': image_id,
                'campo_nombre': field_name,
                'raw_ocr_output': raw_ocr,
                'valor_corregido': corrected_value,
                'causa_raiz': root_cause,
                'timestamp_feedback': datetime.now().isoformat()
            }
            
            # Leer CSV existente y añadir entrada
            df = pd.read_csv(config.MANUAL_FEEDBACK_CSV_FILE, encoding='utf-8')
            df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
            df.to_csv(config.MANUAL_FEEDBACK_CSV_FILE, index=False, encoding='utf-8')
            
            logger.info(f"Entrada de feedback añadida para {image_id}, campo {field_name}")
            
        except Exception as e:
            logger.error(f"Error añadiendo entrada de feedback: {e}")
    
    def get_feedback_statistics(self) -> Dict:
        """Obtiene estadísticas del feedback acumulado"""
        try:
            if not config.MANUAL_FEEDBACK_CSV_FILE.exists():
                return {'total_entries': 0, 'fields': {}, 'root_causes': {}}
            
            df = pd.read_csv(config.MANUAL_FEEDBACK_CSV_FILE, encoding='utf-8')
            
            if df.empty:
                return {'total_entries': 0, 'fields': {}, 'root_causes': {}}
            
            stats = {
                'total_entries': len(df),
                'fields': df['campo_nombre'].value_counts().to_dict(),
                'root_causes': df['causa_raiz'].value_counts().to_dict(),
                'last_feedback': df['timestamp_feedback'].max() if 'timestamp_feedback' in df.columns else None
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de feedback: {e}")
            return {'error': str(e)}
    
    def update_confidence_adjustment(self, field_name: str, raw_ocr_output: str, 
                                   adjustment: float):
        """
        Actualiza el ajuste de confianza para una combinación específica
        
        Args:
            field_name: Nombre del campo
            raw_ocr_output: Salida de OCR
            adjustment: Ajuste de confianza (+/-)
        """
        try:
            if field_name not in self.probabilistic_model:
                self.probabilistic_model[field_name] = {}
            
            if raw_ocr_output not in self.probabilistic_model[field_name]:
                self.probabilistic_model[field_name][raw_ocr_output] = {
                    'total_correcciones': 0,
                    'last_updated': datetime.now().isoformat(),
                    'confidence_adjustment': 0.0
                }
            
            # Actualizar ajuste de confianza
            current_adjustment = self.probabilistic_model[field_name][raw_ocr_output].get('confidence_adjustment', 0.0)
            new_adjustment = (current_adjustment + adjustment) / 2  # Promedio para suavizar
            
            self.probabilistic_model[field_name][raw_ocr_output]['confidence_adjustment'] = new_adjustment
            self.probabilistic_model[field_name][raw_ocr_output]['last_updated'] = datetime.now().isoformat()
            
            self.save_probabilistic_model()
            
            logger.debug(f"Ajuste de confianza actualizado para {field_name}[{raw_ocr_output}]: {new_adjustment:.2f}")
            
        except Exception as e:
            logger.error(f"Error actualizando ajuste de confianza: {e}")

    def detect_persistent_issues(self, extraction_result: Dict, image_quality: Dict) -> Dict:
        """
        NUEVA FUNCIÓN: Detecta problemas persistentes que requieren actualización de código
        Parte del sistema de auto-mejora continua
        """
        try:
            persistent_issues = {
                "code_update_suggested": False,
                "issues_detected": [],
                "severity": "none",
                "recommendation": ""
            }
            
            # Criterio 1: Baja confianza persistente en múltiples campos
            overall_confidence = extraction_result.get('overall_confidence', 100)
            if overall_confidence < 50:
                campos_extraidos = extraction_result.get('campos_extraidos', {})
                low_confidence_fields = [
                    field for field, data in campos_extraidos.items() 
                    if isinstance(data, dict) and data.get('confidence', 100) < 40
                ]
                
                if len(low_confidence_fields) >= 3:
                    persistent_issues["issues_detected"].append("multiple_low_confidence_fields")
                    persistent_issues["severity"] = "high"
            
            # Criterio 2: Problemas de calidad de imagen no resueltos por preprocesamiento
            sharpness = image_quality.get('sharpness', 1000)
            noise_level = image_quality.get('noise_level', 0)
            
            if sharpness < config.LAPLACIAN_VAR_MEDIUM and noise_level > config.NOISE_THRESHOLD_HIGH:
                persistent_issues["issues_detected"].append("preprocessing_insufficient")
                persistent_issues["severity"] = "medium" if persistent_issues["severity"] == "none" else persistent_issues["severity"]
            
            # Criterio 3: Errores de validación cruzada frecuentes
            validation_results = extraction_result.get('validation_results', {})
            if not validation_results.get('cross_validation_passed', True):
                persistent_issues["issues_detected"].append("validation_failures")
                persistent_issues["severity"] = "medium" if persistent_issues["severity"] == "none" else persistent_issues["severity"]
            
            # Criterio 4: Verificar historial de feedback para patrones problemáticos
            try:
                if config.MANUAL_FEEDBACK_CSV_FILE.exists():
                    import pandas as pd
                    df = pd.read_csv(config.MANUAL_FEEDBACK_CSV_FILE, encoding='utf-8')
                    
                    if len(df) > 10:  # Solo si hay suficiente historial
                        # Contar errores recientes (últimos 7 días)
                        df['timestamp_feedback'] = pd.to_datetime(df['timestamp_feedback'])
                        recent_errors = df[df['timestamp_feedback'] > (pd.Timestamp.now() - pd.Timedelta(days=7))]
                        
                        if len(recent_errors) > 5:
                            persistent_issues["issues_detected"].append("frequent_recent_corrections")
                            persistent_issues["severity"] = "high"
                            
            except Exception as e:
                logger.debug(f"Error verificando historial de feedback: {e}")
            
            # Determinar si se sugiere actualización de código
            if persistent_issues["severity"] in ["high", "medium"] and len(persistent_issues["issues_detected"]) >= 2:
                persistent_issues["code_update_suggested"] = True
                persistent_issues["recommendation"] = (
                    "Problemas persistentes de calidad de OCR/extracción detectados. "
                    "Considere actualizar el código base del sistema desde el repositorio de GitHub. "
                    "Consulte la 'Guía para la Actualización del Sistema en el Servidor' para más detalles."
                )
                
                logger.warning("Sistema sugiere actualización de código debido a problemas persistentes")
                logger.warning(f"Problemas detectados: {persistent_issues['issues_detected']}")
            
            return persistent_issues
            
        except Exception as e:
            logger.error(f"Error detectando problemas persistentes: {e}")
            return {
                "code_update_suggested": False,
                "issues_detected": ["detection_error"],
                "error": str(e)
            }
