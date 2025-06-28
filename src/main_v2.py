#!/usr/bin/env python3
"""
Orquestador Principal v2.0 - Sistema OCR optimizado
Integra las mejoras de preprocesamiento y extracción flexible
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime
import shutil

# Importar módulos v2.0
import config
from document_classifier import is_payment_receipt
from image_processor_optimized import diagnose_and_process_image
from ocr_engine import perform_general_ocr
from template_manager_v2 import identify_template_or_zoi_v2
from data_extractor_v2 import extract_data_v2
from learning_manager import LearningManager

# Configurar logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def setup_temp_directory(base_temp_dir: Path, image_name: str) -> Path:
    """Configura directorio temporal para procesamiento"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_dir = base_temp_dir / f"{image_name}_{timestamp}"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Directorio temporal creado: {temp_dir}")
        return temp_dir
        
    except Exception as e:
        logger.error(f"Error creando directorio temporal: {e}")
        raise

def save_processing_results_v2(results: dict, temp_dir: Path):
    """Guarda resultados del procesamiento v2.0"""
    try:
        # Guardar resultado principal
        main_result_path = temp_dir / "extraction_result_v2.json"
        with open(main_result_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        # Guardar resumen ejecutivo
        summary = {
            'version': 'v2.0_optimized',
            'timestamp': results.get('timestamp'),
            'status': results.get('status', 'unknown'),
            'extraction_method': results.get('extraction_method'),
            'overall_confidence': results.get('overall_confidence', 0),
            'campos_extraidos_count': len(results.get('campos_extraidos', {})),
            'validation_passed': results.get('validation_results', {}).get('cross_validation_passed', False)
        }
        
        # Extraer valores principales para el resumen
        campos_extraidos = results.get('campos_extraidos', {})
        summary['extracted_values'] = {}
        
        for field_name, field_data in campos_extraidos.items():
            if isinstance(field_data, dict) and field_data.get('extraction_successful'):
                summary['extracted_values'][field_name] = {
                    'value': field_data.get('value', ''),
                    'confidence': field_data.get('confidence', 0)
                }
        
        summary_path = temp_dir / "extraction_summary_v2.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Resultados v2.0 guardados en: {temp_dir}")
        
    except Exception as e:
        logger.error(f"Error guardando resultados v2.0: {e}")

def cleanup_temp_files(temp_dir: Path):
    """Limpia archivos temporales si está configurado"""
    try:
        if config.CLEAN_TEMP_FILES:
            # Mantener solo archivos esenciales
            essential_files = [
                "extraction_result_v2.json",
                "extraction_summary_v2.json",
                "debug_overlay_v2.png"
            ]
            
            for file_path in temp_dir.iterdir():
                if file_path.name not in essential_files:
                    if file_path.is_file():
                        file_path.unlink()
                    elif file_path.is_dir():
                        shutil.rmtree(file_path)
            
            logger.info("Archivos temporales limpiados (modo optimizado)")
        else:
            logger.info("Archivos temporales conservados para debug")
            
    except Exception as e:
        logger.warning(f"Error durante limpieza de archivos temporales: {e}")

def process_image_v2(image_path: Path, output_dir: Path = None) -> dict:
    """
    FUNCIÓN PRINCIPAL v2.0: Procesamiento optimizado de imagen OCR
    Implementa la estrategia de extracción flexible sin aislamiento de documento
    """
    logger.info("="*80)
    logger.info(f"INICIANDO PROCESAMIENTO OCR v2.0 OPTIMIZADO")
    logger.info(f"Imagen: {image_path}")
    logger.info("="*80)
    
    start_time = datetime.now()
    
    # Configurar directorios
    if output_dir is None:
        output_dir = config.OUTPUT_DIR
    
    temp_dir = setup_temp_directory(config.TEMP_DIR, image_path.stem)
    
    # Inicializar resultado
    processing_result = {
        'version': 'v2.0_optimized_flexible_extraction',
        'image_path': str(image_path),
        'timestamp': start_time.isoformat(),
        'status': 'processing',
        'stages_completed': [],
        'errors': []
    }
    
    try:
        # ETAPA 1: Clasificación de documento
        logger.info("ETAPA 1: Clasificación de documento")
        
        is_payment_doc = is_payment_receipt(image_path)
        processing_result['document_classification'] = {
            'is_payment_receipt': is_payment_doc,
            'confidence': 'high' if is_payment_doc else 'low'
        }
        processing_result['stages_completed'].append('document_classification')
        
        if not is_payment_doc:
            logger.warning("Documento no clasificado como comprobante de pago")
            # Continuar procesamiento pero con advertencia
        
        # ETAPA 2: Preprocesamiento optimizado v2.0 (SIN aislamiento de documento)
        logger.info("ETAPA 2: Preprocesamiento optimizado v2.0")
        
        preprocessed_image, image_quality, preprocessing_steps = diagnose_and_process_image(
            image_path, temp_dir
        )
        
        processing_result['image_quality'] = image_quality
        processing_result['preprocessing_steps'] = preprocessing_steps
        processing_result['stages_completed'].append('preprocessing_v2')
        
        logger.info(f"Preprocesamiento completado - Tipo: {image_quality.get('image_type', 'unknown')}")
        
        # ETAPA 3: OCR global completo
        logger.info("ETAPA 3: OCR global completo sobre imagen preprocesada")
        
        ocr_data_full = perform_general_ocr(preprocessed_image, temp_dir)
        
        processing_result['ocr_global'] = {
            'words_detected': len(ocr_data_full.get('text', [])),
            'average_confidence': sum(ocr_data_full.get('conf', [])) / len(ocr_data_full.get('conf', [])) if ocr_data_full.get('conf') else 0,
            'full_text_length': len(ocr_data_full.get('full_text', ''))
        }
        processing_result['stages_completed'].append('ocr_global')
        
        logger.info(f"OCR global completado - {processing_result['ocr_global']['words_detected']} palabras detectadas")
        
        # ETAPA 4: Identificación de plantilla/ZOI v2.0 (Estrategia flexible)
        logger.info("ETAPA 4: Estrategia de extracción flexible v2.0")
        
        image_dimensions = (preprocessed_image.shape[1], preprocessed_image.shape[0])
        template_or_zoi_data = identify_template_or_zoi_v2(ocr_data_full, image_dimensions)
        
        processing_result['template_identification'] = {
            'method': template_or_zoi_data.get('method'),
            'fields_identified': len(template_or_zoi_data.get('campos', {})),
            'extraction_strategy': template_or_zoi_data.get('extraction_strategy', 'unknown')
        }
        processing_result['stages_completed'].append('template_identification_v2')
        
        logger.info(f"Identificación completada - Método: {template_or_zoi_data.get('method')}")
        
        # ETAPA 5: Extracción de datos v2.0 (Directa desde OCR global)
        logger.info("ETAPA 5: Extracción de datos v2.0 - Directa desde OCR global")
        
        # Inicializar learning manager
        learning_manager = None
        try:
            learning_manager = LearningManager()
        except Exception as e:
            logger.warning(f"Learning manager no disponible: {e}")
        
        extraction_result = extract_data_v2(
            preprocessed_image,
            ocr_data_full,
            template_or_zoi_data,
            temp_dir,
            learning_manager
        )
        
        processing_result.update(extraction_result)
        processing_result['stages_completed'].append('data_extraction_v2')
        
        # ETAPA 6: Finalización y guardado
        logger.info("ETAPA 6: Finalización y guardado de resultados")
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        processing_result.update({
            'end_timestamp': end_time.isoformat(),
            'processing_time_seconds': processing_time,
            'stages_completed_count': len(processing_result['stages_completed']),
            'final_status': processing_result.get('status', 'completed')
        })
        
        # Guardar resultados
        save_processing_results_v2(processing_result, temp_dir)
        
        # Limpiar archivos temporales
        cleanup_temp_files(temp_dir)
        
        # Log final
        logger.info("="*80)
        logger.info(f"PROCESAMIENTO v2.0 COMPLETADO")
        logger.info(f"Estado: {processing_result['final_status']}")
        logger.info(f"Tiempo total: {processing_time:.2f} segundos")
        logger.info(f"Campos extraídos: {len(processing_result.get('campos_extraidos', {}))}")
        logger.info(f"Confianza general: {processing_result.get('overall_confidence', 0):.1f}%")
        logger.info("="*80)
        
        return processing_result
        
    except Exception as e:
        logger.error(f"Error durante procesamiento v2.0: {e}", exc_info=True)
        
        processing_result.update({
            'status': 'error',
            'error': str(e),
            'end_timestamp': datetime.now().isoformat()
        })
        
        # Intentar guardar resultado con error
        try:
            save_processing_results_v2(processing_result, temp_dir)
        except:
            pass
        
        return processing_result

def main():
    """Función principal del sistema OCR v2.0"""
    if len(sys.argv) != 2:
        print("Uso: python main_v2.py <ruta_imagen>")
        print("Ejemplo: python main_v2.py input/test2.png")
        sys.exit(1)
    
    image_path = Path(sys.argv[1])
    
    if not image_path.exists():
        logger.error(f"La imagen no existe: {image_path}")
        sys.exit(1)
    
    if not image_path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
        logger.error(f"Formato de imagen no soportado: {image_path.suffix}")
        sys.exit(1)
    
    try:
        # Procesar imagen con estrategia v2.0
        result = process_image_v2(image_path)
        
        # Mostrar resumen en consola
        print("\n" + "="*60)
        print("RESUMEN DE PROCESAMIENTO OCR v2.0")
        print("="*60)
        print(f"Estado: {result.get('final_status', 'unknown')}")
        print(f"Método de extracción: {result.get('extraction_method', 'unknown')}")
        print(f"Campos extraídos: {len(result.get('campos_extraidos', {}))}")
        print(f"Confianza general: {result.get('overall_confidence', 0):.1f}%")
        print(f"Tiempo de procesamiento: {result.get('processing_time_seconds', 0):.2f}s")
        
        # Mostrar campos extraídos
        campos = result.get('campos_extraidos', {})
        if campos:
            print("\nCAMPOS EXTRAÍDOS:")
            print("-" * 40)
            for field_name, field_data in campos.items():
                if isinstance(field_data, dict) and field_data.get('extraction_successful'):
                    value = field_data.get('value', '')
                    confidence = field_data.get('confidence', 0)
                    print(f"{field_name:15}: {value:20} ({confidence:.1f}%)")
        
        print("="*60)
        
        # Código de salida basado en el resultado
        if result.get('final_status') == 'success':
            sys.exit(0)
        elif result.get('final_status') in ['low_confidence', 'validation_failed']:
            sys.exit(2)  # Advertencia
        else:
            sys.exit(1)  # Error
            
    except KeyboardInterrupt:
        logger.info("Procesamiento interrumpido por el usuario")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Error fatal en main v2.0: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
