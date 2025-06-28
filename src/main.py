"""
Sistema OCR v3.0 - Script Principal
Basado en la lógica exitosa con inversión inteligente de colores
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
import config
from image_processor import process_image
from field_extractor import extract_fields

def setup_logging():
    """Configurar sistema de logging"""
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL),
        format=config.LOG_FORMAT,
        handlers=[
            logging.FileHandler(f"{config.LOGS_DIR}/ocr_system.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )

def create_directories():
    """Crear directorios necesarios"""
    for directory in [config.INPUT_DIR, config.OUTPUT_DIR, config.TEMP_DIR, config.LOGS_DIR]:
        Path(directory).mkdir(parents=True, exist_ok=True)

def process_receipt(image_path: str) -> Dict:
    """
    Procesa un comprobante de pago completo con inversión inteligente
    """
    logger = logging.getLogger(__name__)
    
    # Validar archivo
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Imagen no encontrada: {image_path}")
    
    # Crear directorio de salida único
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    image_name = Path(image_path).stem
    output_dir = f"{config.TEMP_DIR}/{image_name}_{timestamp}"
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    logger.info(f"=== PROCESANDO COMPROBANTE CON INVERSIÓN INTELIGENTE ===")
    logger.info(f"Imagen: {image_path}")
    logger.info(f"Directorio de salida: {output_dir}")
    
    try:
        # 1. Procesar imagen (incluye detección de fondo oscuro e inversión)
        logger.info("PASO 1: Procesamiento de imagen con inversión inteligente")
        processed_image, diagnosis, processing_steps = process_image(image_path, output_dir)
        
        # Mostrar información de inversión
        inversion_info = processing_steps.get("inversion_info", {})
        if inversion_info.get("applied", False):
            logger.info(f"🔄 INVERSIÓN APLICADA: {inversion_info['method']}")
            logger.info(f"   Confianza: {inversion_info['confidence']:.2f}")
            logger.info(f"   Brillo original: {inversion_info.get('original_brightness', 0):.1f}")
            logger.info(f"   Brillo invertido: {inversion_info.get('inverted_brightness', 0):.1f}")
        else:
            logger.info("ℹ️  No se requirió inversión de colores")
        
        # 2. Extraer campos
        logger.info("PASO 2: Extracción de campos con lógica de centro y expansión")
        extracted_fields = extract_fields(processed_image, output_dir)
        
        # 3. Calcular estadísticas
        successful_extractions = len([f for f in extracted_fields.values() 
                                    if f.get('extraction_successful', False)])
        total_fields = len(extracted_fields)
        extraction_rate = (successful_extractions / total_fields) * 100 if total_fields > 0 else 0
        
        # Calcular confianza general
        confidences = [f.get('confidence', 0) for f in extracted_fields.values() 
                      if f.get('extraction_successful', False)]
        overall_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        # 4. Compilar resultado final
        result = {
            "success": successful_extractions > 0,
            "version": "3.0",
            "timestamp": datetime.now().isoformat(),
            "image_path": image_path,
            "output_directory": output_dir,
            "image_diagnosis": diagnosis,
            "processing_steps": processing_steps,
            "extracted_fields": extracted_fields,
            "statistics": {
                "total_fields": total_fields,
                "successful_extractions": successful_extractions,
                "failed_extractions": total_fields - successful_extractions,
                "extraction_rate": extraction_rate,
                "overall_confidence": overall_confidence
            },
            "final_status": "extraction_successful" if successful_extractions > 0 else "extraction_failed"
        }
        
        # Guardar resultado
        result_path = f"{output_dir}/{config.EXTRACTION_RESULT_FILE}"
        with open(result_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        logger.info("=== PROCESAMIENTO COMPLETADO ===")
        logger.info(f"Resultado guardado en: {result_path}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error durante procesamiento: {e}", exc_info=True)
        error_result = {
            "success": False,
            "version": "3.0",
            "timestamp": datetime.now().isoformat(),
            "image_path": image_path,
            "error": str(e),
            "error_type": type(e).__name__,
            "final_status": "processing_error"
        }
        return error_result

def print_summary(result: Dict):
    """Imprime resumen de resultados con información de inversión"""
    if result["success"]:
        print("\n" + "="*70)
        print("🎯 RESUMEN DE EXTRACCIÓN OCR v3.0 CON INVERSIÓN INTELIGENTE")
        print("="*70)
        print(f"Estado: ✅ EXITOSO")
        
        # Información de imagen
        diagnosis = result.get("image_diagnosis", {})
        processing_steps = result.get("processing_steps", {})
        
        print(f"Tipo de imagen: {diagnosis.get('image_type', 'Desconocido')}")
        
        # Información de inversión
        inversion_info = processing_steps.get("inversion_info", {})
        if inversion_info.get("applied", False):
            print(f"🔄 Inversión aplicada: SÍ ({inversion_info.get('method', 'unknown')})")
            print(f"   Confianza inversión: {inversion_info.get('confidence', 0):.2f}")
        else:
            print(f"🔄 Inversión aplicada: NO")
        
        # Estadísticas de extracción
        stats = result.get("statistics", {})
        print(f"Campos extraídos: {stats.get('successful_extractions', 0)}/{stats.get('total_fields', 0)}")
        print(f"Tasa de extracción: {stats.get('extraction_rate', 0):.1f}%")
        print(f"Confianza general: {stats.get('overall_confidence', 0):.1f}%")
        print(f"Directorio de salida: {result['output_directory']}")
        
        print("\n📋 CAMPOS EXTRAÍDOS:")
        print("-" * 50)
        for field_name, field_data in result["extracted_fields"].items():
            if field_data.get('extraction_successful', False):
                value = field_data.get('value', '')
                confidence = field_data.get('confidence', 0)
                print(f"{field_name:15}: {value} ({confidence:.0f}%)")
            else:
                reason = field_data.get('reason', 'No extraído')
                print(f"{field_name:15}: ❌ {reason}")
        
        print("="*70)
    else:
        print("\n" + "="*70)
        print("❌ ERROR EN PROCESAMIENTO")
        print("="*70)
        print(f"Error: {result.get('error', 'Error desconocido')}")
        print(f"Tipo: {result.get('error_type', 'Desconocido')}")
        print("="*70)

def main():
    """Función principal"""
    if len(sys.argv) != 2:
        print("Uso: python3 src/main.py <ruta_imagen>")
        print("Ejemplo: python3 src/main.py input/comprobante.png")
        print("\n🆕 NUEVA FUNCIONALIDAD v3.0:")
        print("   • Inversión inteligente de colores para fondos oscuros")
        print("   • Detección automática de fondos negros")
        print("   • Conversión automática: letras blancas → letras negras")
        print("   • Optimizado para comprobantes de fondo oscuro")
        sys.exit(1)
    
    # Configurar sistema
    create_directories()
    setup_logging()
    
    # Procesar imagen
    image_path = sys.argv[1]
    result = process_receipt(image_path)
    
    # Mostrar resumen
    print_summary(result)
    
    # Código de salida
    sys.exit(0 if result["success"] else 1)

if __name__ == "__main__":
    main()
