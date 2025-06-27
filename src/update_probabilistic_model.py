#!/usr/bin/env python3
"""
Script de reentrenamiento - Procesa feedback manual y actualiza modelo probabilístico
Ejecutado periódicamente para incorporar aprendizaje del feedback humano
"""

import pandas as pd
import json
import shutil
from datetime import datetime
from pathlib import Path
import logging
import sys
import config
from learning_manager import LearningManager

def setup_logging():
    """Configura logging para el script de reentrenamiento"""
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL),
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(config.LOG_FILE_PATH),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def load_feedback_data() -> pd.DataFrame:
    """Carga datos de feedback desde CSV"""
    try:
        if not config.MANUAL_FEEDBACK_CSV_FILE.exists():
            logger.warning("Archivo de feedback no existe")
            return pd.DataFrame()
        
        df = pd.read_csv(config.MANUAL_FEEDBACK_CSV_FILE, encoding='utf-8')
        logger.info(f"Cargados {len(df)} registros de feedback")
        return df
        
    except Exception as e:
        logger.error(f"Error cargando datos de feedback: {e}")
        return pd.DataFrame()

def process_feedback_entries(df: pd.DataFrame, learning_manager: LearningManager) -> Dict:
    """
    Procesa entradas de feedback y actualiza modelo probabilístico
    
    Args:
        df: DataFrame con datos de feedback
        learning_manager: Instancia del gestor de aprendizaje
        
    Returns:
        Dict: Estadísticas del procesamiento
    """
    processing_stats = {
        'total_processed': 0,
        'fields_updated': {},
        'root_causes_analyzed': {},
        'confidence_adjustments': 0,
        'errors': []
    }
    
    try:
        for index, row in df.iterrows():
            try:
                image_id = row['id_unico_imagen']
                field_name = row['campo_nombre']
                raw_ocr = row['raw_ocr_output']
                corrected_value = row['valor_corregido']
                root_cause = row['causa_raiz']
                
                # Actualizar modelo probabilístico
                update_probabilistic_model_entry(
                    learning_manager, field_name, raw_ocr, corrected_value, root_cause
                )
                
                # Actualizar estadísticas
                processing_stats['total_processed'] += 1
                
                if field_name not in processing_stats['fields_updated']:
                    processing_stats['fields_updated'][field_name] = 0
                processing_stats['fields_updated'][field_name] += 1
                
                if root_cause not in processing_stats['root_causes_analyzed']:
                    processing_stats['root_causes_analyzed'][root_cause] = 0
                processing_stats['root_causes_analyzed'][root_cause] += 1
                
                # Aplicar ajustes de confianza basados en causa raíz
                confidence_adjustment = calculate_confidence_adjustment(root_cause)
                if confidence_adjustment != 0:
                    learning_manager.update_confidence_adjustment(
                        field_name, raw_ocr, confidence_adjustment
                    )
                    processing_stats['confidence_adjustments'] += 1
                
                logger.debug(f"Procesado feedback: {image_id}, {field_name}, causa: {root_cause}")
                
            except Exception as e:
                error_msg = f"Error procesando fila {index}: {e}"
                logger.error(error_msg)
                processing_stats['errors'].append(error_msg)
        
        return processing_stats
        
    except Exception as e:
        logger.error(f"Error durante procesamiento de feedback: {e}")
        processing_stats['errors'].append(str(e))
        return processing_stats

def update_probabilistic_model_entry(learning_manager: LearningManager, field_name: str,
                                    raw_ocr: str, corrected_value: str, root_cause: str):
    """Actualiza entrada específica en el modelo probabilístico"""
    try:
        # Inicializar estructura si no existe
        if field_name not in learning_manager.probabilistic_model:
            learning_manager.probabilistic_model[field_name] = {}
        
        field_model = learning_manager.probabilistic_model[field_name]
        
        if raw_ocr not in field_model:
            field_model[raw_ocr] = {
                'total_correcciones': 0,
                'last_updated': datetime.now().isoformat(),
                'confidence_adjustment': 0.0
            }
        
        ocr_entry = field_model[raw_ocr]
        
        # Actualizar contador de corrección específica
        if corrected_value not in ocr_entry:
            ocr_entry[corrected_value] = {
                'count': 0,
                'causas': {}
            }
        
        correction_entry = ocr_entry[corrected_value]
        correction_entry['count'] += 1
        
        # Actualizar contador de causa raíz
        if root_cause not in correction_entry['causas']:
            correction_entry['causas'][root_cause] = 0
        correction_entry['causas'][root_cause] += 1
        
        # Actualizar totales
        ocr_entry['total_correcciones'] += 1
        ocr_entry['last_updated'] = datetime.now().isoformat()
        
        logger.debug(f"Modelo actualizado: {field_name}[{raw_ocr}] -> {corrected_value}")
        
    except Exception as e:
        logger.error(f"Error actualizando entrada del modelo: {e}")

def calculate_confidence_adjustment(root_cause: str) -> float:
    """
    Calcula ajuste de confianza basado en causa raíz
    
    Args:
        root_cause: Causa raíz del error
        
    Returns:
        float: Ajuste de confianza (+/-)
    """
    # Mapeo de causas raíz a ajustes de confianza
    confidence_adjustments = {
        'mala_segmentacion': -10.0,      # Reducir confianza para problemas de segmentación
        'caracter_mal_reconocido': -5.0,  # Reducir ligeramente para errores de OCR
        'campo_no_detectado': -15.0,     # Reducir significativamente si no se detecta
        'error_de_plantilla': -8.0,      # Reducir para errores de plantilla
        'formato_erroneo': -3.0,         # Reducir ligeramente para errores de formato
        'info_faltante': -12.0,          # Reducir para información faltante
        'ruido_imagen': -7.0,            # Reducir para problemas de ruido
        'distorsion_imagen': -6.0,       # Reducir para distorsión
        'clasificacion_erronea_no_recibo': -20.0,  # Reducir mucho para clasificación errónea
        'otro': -2.0                     # Reducir mínimamente para otros casos
    }
    
    return confidence_adjustments.get(root_cause, 0.0)

def analyze_patterns_and_suggest_improvements(processing_stats: Dict) -> Dict:
    """Analiza patrones en el feedback y sugiere mejoras"""
    suggestions = {
        'field_improvements': {},
        'root_cause_priorities': {},
        'system_recommendations': []
    }
    
    try:
        # Analizar campos con más errores
        fields_updated = processing_stats.get('fields_updated', {})
        if fields_updated:
            most_problematic_field = max(fields_updated, key=fields_updated.get)
            suggestions['field_improvements'][most_problematic_field] = {
                'error_count': fields_updated[most_problematic_field],
                'recommendation': 'Revisar configuración de ROI y patrones de validación'
            }
        
        # Analizar causas raíz más frecuentes
        root_causes = processing_stats.get('root_causes_analyzed', {})
        if root_causes:
            most_common_cause = max(root_causes, key=root_causes.get)
            suggestions['root_cause_priorities'][most_common_cause] = {
                'frequency': root_causes[most_common_cause],
                'priority': 'high'
            }
            
            # Generar recomendaciones específicas
            if most_common_cause == 'mala_segmentacion':
                suggestions['system_recommendations'].append(
                    'Considerar ajustar ROI base en plantillas o mejorar lógica de ZOI dinámicas'
                )
            elif most_common_cause == 'caracter_mal_reconocido':
                suggestions['system_recommendations'].append(
                    'Evaluar mejoras en preprocesamiento de imagen o configuración de Tesseract'
                )
            elif most_common_cause == 'campo_no_detectado':
                suggestions['system_recommendations'].append(
                    'Revisar palabras clave y heurísticas contextuales para detección de campos'
                )
        
        return suggestions
        
    except Exception as e:
        logger.error(f"Error analizando patrones: {e}")
        return suggestions

def archive_processed_feedback(df: pd.DataFrame):
    """Archiva el CSV de feedback procesado"""
    try:
        if df.empty:
            logger.info("No hay datos de feedback para archivar")
            return
        
        # Generar nombre de archivo archivado
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_filename = f"manual_feedback_processed_{timestamp}.csv"
        archive_path = config.PROCESSED_FEEDBACK_ARCHIVE_DIR / archive_filename
        
        # Mover archivo actual al archivo
        shutil.move(str(config.MANUAL_FEEDBACK_CSV_FILE), str(archive_path))
        
        # Crear nuevo archivo vacío
        learning_manager = LearningManager()
        learning_manager.initialize_feedback_csv()
        
        logger.info(f"Feedback archivado: {archive_path}")
        
    except Exception as e:
        logger.error(f"Error archivando feedback: {e}")

def main():
    """Función principal del script de reentrenamiento"""
    global logger
    logger = setup_logging()
    
    logger.info("=== Iniciando reentrenamiento del modelo probabilístico ===")
    
    try:
        # Cargar datos de feedback
        feedback_df = load_feedback_data()
        
        if feedback_df.empty:
            logger.info("No hay datos de feedback para procesar")
            return
        
        # Inicializar gestor de aprendizaje
        learning_manager = LearningManager()
        
        # Procesar entradas de feedback
        logger.info("Procesando entradas de feedback...")
        processing_stats = process_feedback_entries(feedback_df, learning_manager)
        
        # Guardar modelo actualizado
        learning_manager.save_probabilistic_model()
        
        # Analizar patrones y generar sugerencias
        suggestions = analyze_patterns_and_suggest_improvements(processing_stats)
        
        # Archivar feedback procesado
        archive_processed_feedback(feedback_df)
        
        # Generar reporte de reentrenamiento
        report = {
            'timestamp': datetime.now().isoformat(),
            'processing_stats': processing_stats,
            'improvement_suggestions': suggestions,
            'model_size': len(learning_manager.probabilistic_model)
        }
        
        # Guardar reporte
        report_path = config.LOGS_DIR / f"retraining_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # Mostrar resumen
        logger.info("=== Reentrenamiento completado ===")
        logger.info(f"Registros procesados: {processing_stats['total_processed']}")
        logger.info(f"Campos actualizados: {list(processing_stats['fields_updated'].keys())}")
        logger.info(f"Ajustes de confianza aplicados: {processing_stats['confidence_adjustments']}")
        logger.info(f"Errores encontrados: {len(processing_stats['errors'])}")
        logger.info(f"Reporte guardado: {report_path}")
        
        if processing_stats['errors']:
            logger.warning("Errores durante procesamiento:")
            for error in processing_stats['errors'][:5]:  # Mostrar solo los primeros 5
                logger.warning(f"  - {error}")
        
        # Mostrar sugerencias principales
        if suggestions['system_recommendations']:
            logger.info("Recomendaciones del sistema:")
            for rec in suggestions['system_recommendations']:
                logger.info(f"  - {rec}")
        
    except Exception as e:
        logger.error(f"Error durante reentrenamiento: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
