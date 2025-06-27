#!/usr/bin/env python3
"""
Orquestador Inteligente - Script principal del sistema OCR de pagos móviles
Coordina todo el flujo de procesamiento desde la recepción hasta la salida de datos
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime
import shutil

# Importar módulos del proyecto
import config
from document_classifier import is_payment_receipt
from image_processor import diagnose_and_process_image
from ocr_engine import perform_general_ocr
from template_manager import identify_template_or_zoi
from data_extractor import extract_data
from learning_manager import LearningManager

def setup_logging(image_id: str):
    """Configura el sistema de logging"""
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL),
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(config.LOG_FILE_PATH),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)
    logger.info(f"Iniciando procesamiento para imagen: {image_id}")
    return logger

def create_temp_directory(image_id: str) -> Path:
    """Crea directorio temporal para la imagen"""
    temp_image_dir = config.TEMP_DIR / image_id
    temp_image_dir.mkdir(parents=True, exist_ok=True)
    return temp_image_dir

def generate_output_json(success: bool, reason: str = "", data: dict = None, 
                        image_quality: dict = None, processing_steps: dict = None) -> dict:
    """Genera el JSON de salida estandarizado"""
    output = {
        "success": success,
        "timestamp": datetime.now().isoformat(),
        "reason": reason,
        "data": data or {},
        "initial_image_quality": image_quality or {},
        "processing_steps_taken": processing_steps or {}
    }
    return output

def cleanup_temp_files(temp_image_dir: Path, logger):
    """Limpia archivos temporales si está configurado"""
    if config.CLEAN_TEMP_FILES:
        try:
            shutil.rmtree(temp_image_dir)
            logger.info(f"Archivos temporales eliminados: {temp_image_dir}")
        except Exception as e:
            logger.warning(f"Error al eliminar archivos temporales: {e}")

def main():
    """Función principal del orquestador"""
    if len(sys.argv) != 3:
        print(json.dumps({
            "success": False,
            "reason": "invalid_arguments",
            "message": "Uso: python main.py <image_path> <image_id>"
        }))
        sys.exit(1)
    
    image_path = Path(sys.argv[1])
    image_id = sys.argv[2]
    
    # Configurar logging
    logger = setup_logging(image_id)
    
    try:
        # Validar que la imagen existe
        if not image_path.exists():
            output = generate_output_json(False, "image_not_found")
            print(json.dumps(output))
            return
        
        # Crear directorio temporal
        temp_image_dir = create_temp_directory(image_id)
        logger.info(f"Directorio temporal creado: {temp_image_dir}")
        
        # Paso 1: Detección rápida de "No Recibo"
        logger.info("Iniciando clasificación de documento...")
        is_receipt, classification_data = is_payment_receipt(image_path)
        
        if not is_receipt:
            logger.info("Imagen clasificada como 'no recibo'")
            output = generate_output_json(
                False, 
                "no_payment_receipt",
                data={"classification_details": classification_data}
            )
            print(json.dumps(output))
            cleanup_temp_files(temp_image_dir, logger)
            return
        
        # Paso 2: Diagnóstico multimodal y preprocesamiento
        logger.info("Iniciando diagnóstico y preprocesamiento de imagen...")
        preprocessed_image, image_quality, processing_steps = diagnose_and_process_image(
            image_path, temp_image_dir
        )
        
        # Paso 3: OCR general
        logger.info("Realizando OCR general...")
        ocr_data_full = perform_general_ocr(preprocessed_image)
        
        # Paso 4: Identificación de plantilla o ZOI dinámicas
        logger.info("Identificando plantilla o calculando ZOI dinámicas...")
        image_dimensions = (preprocessed_image.shape[1], preprocessed_image.shape[0])
        template_or_zoi_data = identify_template_or_zoi(ocr_data_full, image_dimensions)
        
        # Paso 5: Extracción dirigida y refinamiento
        logger.info("Iniciando extracción dirigida de datos...")
        learning_manager = LearningManager()
        extraction_result = extract_data(
            preprocessed_image, 
            ocr_data_full, 
            template_or_zoi_data, 
            temp_image_dir, 
            learning_manager
        )
        
        # Paso 6: Detección de problemas persistentes y sugerencias de actualización
        logger.info("Analizando problemas persistentes del sistema...")
        persistent_issues = learning_manager.detect_persistent_issues(extraction_result, image_quality)
        
        if persistent_issues.get("code_update_suggested", False):
            logger.warning("RECOMENDACIÓN DEL SISTEMA: Actualización de código sugerida")
            logger.warning(persistent_issues.get("recommendation", ""))
            
            # Añadir información al resultado de extracción
            extraction_result["system_status_hint"] = persistent_issues.get("recommendation", "")
            extraction_result["persistent_issues_detected"] = persistent_issues.get("issues_detected", [])

        # Paso 7: Registro histórico
        logger.info("Guardando registro histórico...")
        learning_manager.save_processing_record(extraction_result, image_path)
        
        # Generar salida final
        output = generate_output_json(
            True,
            "processing_completed",
            data=extraction_result,
            image_quality=image_quality,
            processing_steps=processing_steps
        )
        
        print(json.dumps(output, ensure_ascii=False, indent=2))
        logger.info("Procesamiento completado exitosamente")
        
    except Exception as e:
        logger.error(f"Error durante el procesamiento: {str(e)}", exc_info=True)
        output = generate_output_json(False, "processing_error", data={"error": str(e)})
        print(json.dumps(output))
    
    finally:
        # Limpieza de archivos temporales
        if 'temp_image_dir' in locals():
            cleanup_temp_files(temp_image_dir, logger)

if __name__ == "__main__":
    main()
