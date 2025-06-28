"""
Procesador de imágenes OPTIMIZADO - Sin aislamiento de documento
Versión 2.0 - Enfoque simplificado basado en análisis de resultados exitosos
"""

import cv2
import numpy as np
import pytesseract
from PIL import Image, ImageEnhance
from pathlib import Path
from typing import Tuple, Dict
import logging
import config

logger = logging.getLogger(__name__)

def calculate_sharpness(image: np.ndarray) -> float:
    """Calcula la nitidez usando varianza Laplaciana"""
    try:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        return float(laplacian_var)
    except Exception as e:
        logger.warning(f"Error calculando nitidez: {e}")
        return 0.0

def calculate_brightness(image: np.ndarray) -> Tuple[float, Dict]:
    """Calcula brillo promedio y estadísticas del histograma"""
    try:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        brightness = np.mean(gray)
        
        hist_stats = {
            "mean": float(brightness),
            "std": float(np.std(gray)),
            "min": int(np.min(gray)),
            "max": int(np.max(gray))
        }
        
        return brightness, hist_stats
    except Exception as e:
        logger.warning(f"Error calculando brillo: {e}")
        return 128.0, {}

def calculate_noise_level(image: np.ndarray) -> float:
    """Calcula nivel de ruido basado en desviación estándar"""
    try:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        noise_map = cv2.absdiff(gray, blurred)
        noise_level = np.std(noise_map)
        return float(noise_level)
    except Exception as e:
        logger.warning(f"Error calculando nivel de ruido: {e}")
        return 0.0

def detect_skew_angle(image: np.ndarray) -> Tuple[float, Dict]:
    """Detecta ángulo de inclinación usando Tesseract OSD"""
    try:
        pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        
        osd_config = f'--psm {config.TESSERACT_PSM_OSD_DETECTION} --oem {config.TESSERACT_OEM}'
        osd_data = pytesseract.image_to_osd(pil_image, config=osd_config)
        
        osd_info = {}
        for line in osd_data.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                osd_info[key.strip()] = value.strip()
        
        rotate_angle = float(osd_info.get('Rotate', '0'))
        return rotate_angle, osd_info
        
    except Exception as e:
        logger.warning(f"Error detectando inclinación: {e}")
        return 0.0, {"method": "failed", "error": str(e)}

def apply_aggressive_denoising(image: np.ndarray, noise_level: float) -> Tuple[np.ndarray, list]:
    """Denoising agresivo y adaptativo"""
    applied_filters = []
    processed_image = image.copy()
    
    try:
        if noise_level > config.NOISE_THRESHOLD_HIGH:
            logger.debug(f"Aplicando denoising agresivo (ruido: {noise_level:.2f})")
            
            if len(processed_image.shape) == 3:
                processed_image = cv2.fastNlMeansDenoisingColored(processed_image, None, 15, 15, 7, 21)
                applied_filters.append("fastNlMeansDenoisingColored_aggressive")
            else:
                processed_image = cv2.fastNlMeansDenoising(processed_image, None, 15, 7, 21)
                applied_filters.append("fastNlMeansDenoising_aggressive")
            
            processed_image = cv2.medianBlur(processed_image, 5)
            applied_filters.append("medianBlur_5")
            
        elif noise_level > (config.NOISE_THRESHOLD_HIGH * 0.6):
            logger.debug(f"Aplicando denoising moderado (ruido: {noise_level:.2f})")
            
            if len(processed_image.shape) == 3:
                processed_image = cv2.fastNlMeansDenoisingColored(processed_image, None, 10, 10, 7, 21)
                applied_filters.append("fastNlMeansDenoisingColored_moderate")
            else:
                processed_image = cv2.fastNlMeansDenoising(processed_image, None, 10, 7, 21)
                applied_filters.append("fastNlMeansDenoising_moderate")
        else:
            logger.debug(f"Aplicando denoising suave (ruido: {noise_level:.2f})")
            processed_image = cv2.GaussianBlur(processed_image, (3, 3), 0)
            applied_filters.append("gaussianBlur_light")
        
        if len(processed_image.shape) == 3:
            processed_image = cv2.bilateralFilter(processed_image, 9, 75, 75)
        else:
            processed_image = cv2.bilateralFilter(processed_image, 9, 75, 75)
        applied_filters.append("bilateralFilter")
        
        return processed_image, applied_filters
        
    except Exception as e:
        logger.error(f"Error durante denoising: {e}")
        return image, ["denoising_failed"]

def apply_high_quality_upscaling(image: np.ndarray, sharpness: float) -> Tuple[np.ndarray, Dict]:
    """Escalado de alta calidad con factores agresivos"""
    scaling_info = {"applied": False, "factor": 1.0, "method": "none"}
    
    try:
        height, width = image.shape[:2]
        scale_factor = 1.0
        
        if sharpness <= config.LAPLACIAN_VAR_MEDIUM:
            if sharpness <= (config.LAPLACIAN_VAR_MEDIUM * 0.5):
                scale_factor = max(scale_factor, 3.0)
                logger.debug(f"Nitidez muy baja ({sharpness:.1f}) - Escalado x3.0")
            else:
                scale_factor = max(scale_factor, 2.5)
                logger.debug(f"Nitidez baja ({sharpness:.1f}) - Escalado x2.5")
        
        if width < 800 or height < 600:
            dimension_factor = max(800/width, 600/height)
            scale_factor = max(scale_factor, dimension_factor)
            logger.debug(f"Dimensiones pequeñas ({width}x{height}) - Factor: {dimension_factor:.1f}")
        
        if width < 1000 or height < 800:
            scale_factor = max(scale_factor, 2.0)
            logger.debug("Aplicando escalado mínimo x2.0 para captura móvil")
        
        if scale_factor > 1.1:
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            
            interpolation_methods = [
                (cv2.INTER_LANCZOS4, "LANCZOS4"),
                (cv2.INTER_CUBIC, "CUBIC"),
                (cv2.INTER_LINEAR, "LINEAR")
            ]
            
            scaled_image = None
            method_used = "none"
            
            for method, method_name in interpolation_methods:
                try:
                    scaled_image = cv2.resize(image, (new_width, new_height), interpolation=method)
                    method_used = method_name
                    break
                except Exception as e:
                    logger.warning(f"Error con interpolación {method_name}: {e}")
                    continue
            
            if scaled_image is not None:
                scaling_info = {
                    "applied": True,
                    "factor": scale_factor,
                    "method": method_used,
                    "original_size": (width, height),
                    "new_size": (new_width, new_height)
                }
                
                logger.info(f"Escalado aplicado: {scale_factor:.1f}x usando {method_used}")
                return scaled_image, scaling_info
        
        return image, scaling_info
        
    except Exception as e:
        logger.error(f"Error durante escalado: {e}")
        return image, {"applied": False, "error": str(e)}

def apply_extreme_binarization(image: np.ndarray) -> Tuple[np.ndarray, Dict]:
    """Binarización con contraste extremo"""
    binarization_info = {"method": "none", "success": False}
    
    try:
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        logger.debug("Aplicando binarización adaptativa optimizada...")
        
        adaptive_configs = [
            (15, 8, "adaptive_15_8"),
            (21, 10, "adaptive_21_10"),
            (11, 6, "adaptive_11_6"),
            (25, 12, "adaptive_25_12")
        ]
        
        best_result = None
        best_score = 0
        best_config = None
        
        for block_size, C, config_name in adaptive_configs:
            try:
                adaptive_thresh = cv2.adaptiveThreshold(
                    gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                    cv2.THRESH_BINARY, block_size, C
                )
                
                unique_values = np.unique(adaptive_thresh)
                
                if len(unique_values) == 2 and 0 in unique_values and 255 in unique_values:
                    score = 100
                else:
                    score = max(0, 100 - len(unique_values))
                
                if score > best_score:
                    best_score = score
                    best_result = adaptive_thresh
                    best_config = config_name
                    
            except Exception as e:
                logger.warning(f"Error con configuración {config_name}: {e}")
                continue
        
        if best_result is not None:
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
            morphed = cv2.morphologyEx(best_result, cv2.MORPH_CLOSE, kernel)
            
            kernel_open = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
            final_result = cv2.morphologyEx(morphed, cv2.MORPH_OPEN, kernel_open)
            
            final_bgr = cv2.cvtColor(final_result, cv2.COLOR_GRAY2BGR)
            
            binarization_info = {
                "method": f"adaptive_threshold_{best_config}",
                "success": True,
                "quality_score": best_score,
                "unique_values": len(np.unique(final_result))
            }
            
            logger.info(f"Binarización extrema aplicada - Método: {best_config}")
            return final_bgr, binarization_info
        
        # Fallback: Threshold Otsu
        _, otsu_thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        otsu_bgr = cv2.cvtColor(otsu_thresh, cv2.COLOR_GRAY2BGR)
        
        binarization_info = {
            "method": "otsu_fallback",
            "success": True,
            "unique_values": len(np.unique(otsu_thresh))
        }
        
        return otsu_bgr, binarization_info
        
    except Exception as e:
        logger.error(f"Error durante binarización extrema: {e}")
        binarization_info = {"method": "failed", "success": False, "error": str(e)}
        if len(image.shape) == 2:
            return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR), binarization_info
        return image, binarization_info

def classify_image_type(diagnosis: Dict) -> str:
    """Clasifica el tipo de imagen basado en el diagnóstico"""
    sharpness = diagnosis.get('sharpness', 0)
    brightness = diagnosis.get('brightness', 128)
    noise = diagnosis.get('noise_level', 0)
    
    if sharpness < config.LAPLACIAN_VAR_MEDIUM and brightness > config.BRIGHTNESS_THRESHOLD_HIGH:
        return "Captura WhatsApp"
    elif sharpness > config.LAPLACIAN_VAR_HIGH and noise < config.NOISE_THRESHOLD_HIGH:
        return "Escaneo Digital"
    elif noise > config.NOISE_THRESHOLD_HIGH:
        return "Foto Física"
    else:
        return "Imagen Mixta"

def apply_preprocessing_profile_optimized(image: np.ndarray, image_type: str, diagnosis: Dict) -> Tuple[np.ndarray, Dict]:
    """
    VERSIÓN 2.0 OPTIMIZADA: Sin aislamiento de documento
    Basado en análisis exitoso de direct_ocr_extractor_polished.py
    """
    processing_steps = {
        "applied_steps": [], 
        "scaling_info": {}, 
        "denoising_info": {}, 
        "binarization_info": {},
        "document_isolation": "DISABLED_FOR_OPTIMIZATION"
    }
    processed_image = image.copy()
    
    try:
        logger.info(f"Iniciando preprocesamiento optimizado v2.0 para: {image_type}")
        
        # === PASO 1: AISLAMIENTO DEL DOCUMENTO (DESACTIVADO) ===
        # El análisis ha demostrado que Tesseract funciona óptimamente sobre la imagen completa preprocesada.
        # Desactivamos el aislamiento inicial para evitar recortes erróneos y simplificar el pipeline.
        logger.info("PASO 1: Aislamiento de documento DESACTIVADO (optimización v2.0)")
        processing_steps["applied_steps"].append("document_isolation_disabled_for_optimization")
        
        # === PASO 2: CORRECCIÓN DE INCLINACIÓN ===
        skew_angle = diagnosis.get('skew_angle', 0)
        if abs(skew_angle) > 1.0:
            height, width = processed_image.shape[:2]
            center = (width // 2, height // 2)
            rotation_matrix = cv2.getRotationMatrix2D(center, skew_angle, 1.0)
            processed_image = cv2.warpAffine(processed_image, rotation_matrix, (width, height), 
                                           flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
            processing_steps["applied_steps"].append(f"skew_correction_{skew_angle:.1f}deg")
            logger.debug(f"Corrección de inclinación aplicada: {skew_angle:.1f}°")
        
        # === PASO 3: ESCALADO DE ALTA CALIDAD ===
        logger.info("PASO 2: Escalado de alta calidad...")
        sharpness = diagnosis.get('sharpness', 0)
        processed_image, scaling_info = apply_high_quality_upscaling(processed_image, sharpness)
        processing_steps["scaling_info"] = scaling_info
        if scaling_info["applied"]:
            processing_steps["applied_steps"].append(f"upscale_{scaling_info['factor']:.1f}x_{scaling_info['method']}")
        
        # === PASO 4: DENOISING AGRESIVO ===
        logger.info("PASO 3: Denoising agresivo...")
        noise_level = diagnosis.get('noise_level', 0)
        processed_image, denoising_filters = apply_aggressive_denoising(processed_image, noise_level)
        processing_steps["denoising_info"] = {"filters_applied": denoising_filters, "noise_level": noise_level}
        processing_steps["applied_steps"].extend(denoising_filters)
        
        # === PASO 5: AJUSTES ESPECÍFICOS POR TIPO ===
        logger.info("PASO 4: Ajustes específicos por tipo de imagen...")
        brightness = diagnosis.get('brightness', 128)
        
        if image_type == "Captura WhatsApp":
            pil_image = Image.fromarray(cv2.cvtColor(processed_image, cv2.COLOR_BGR2RGB))
            
            enhancer = ImageEnhance.Contrast(pil_image)
            pil_image = enhancer.enhance(1.5)
            
            enhancer = ImageEnhance.Brightness(pil_image)
            pil_image = enhancer.enhance(0.85)
            
            processed_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            processing_steps["applied_steps"].append("whatsapp_optimization")
            
        elif image_type == "Foto Física":
            processed_image = cv2.convertScaleAbs(processed_image, alpha=1.2, beta=10)
            processing_steps["applied_steps"].append("physical_photo_enhancement")
            
        elif image_type == "Escaneo Digital":
            kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            processed_image = cv2.filter2D(processed_image, -1, kernel)
            processing_steps["applied_steps"].append("scan_sharpening")
        
        # Ajustes generales de brillo
        if brightness < config.BRIGHTNESS_THRESHOLD_LOW:
            processed_image = cv2.convertScaleAbs(processed_image, alpha=1.0, beta=40)
            processing_steps["applied_steps"].append("brightness_boost_high")
        elif brightness > config.BRIGHTNESS_THRESHOLD_HIGH:
            processed_image = cv2.convertScaleAbs(processed_image, alpha=0.85, beta=-25)
            processing_steps["applied_steps"].append("brightness_reduction_high")
        
        # === PASO 6: BINARIZACIÓN EXTREMA ===
        logger.info("PASO 5: Binarización con contraste extremo...")
        processed_image, binarization_info = apply_extreme_binarization(processed_image)
        processing_steps["binarization_info"] = binarization_info
        processing_steps["applied_steps"].append(f"extreme_binarization_{binarization_info['method']}")
        
        processing_steps["image_type"] = image_type
        processing_steps["success"] = True
        processing_steps["total_steps"] = len(processing_steps["applied_steps"])
        processing_steps["optimization_version"] = "v2.0_no_document_isolation"
        
        logger.info(f"Preprocesamiento v2.0 completado - {processing_steps['total_steps']} pasos aplicados")
        
    except Exception as e:
        logger.error(f"Error durante preprocesamiento optimizado v2.0: {e}", exc_info=True)
        processing_steps["error"] = str(e)
        processing_steps["success"] = False
        processed_image = image.copy()
    
    return processed_image, processing_steps

def diagnose_and_process_image(image_path: Path, temp_output_dir: Path) -> Tuple[np.ndarray, Dict, Dict]:
    """
    FUNCIÓN PRINCIPAL OPTIMIZADA v2.0: Sin aislamiento de documento
    Objetivo: Maximizar la calidad para OCR global completo
    """
    logger.info(f"Iniciando diagnóstico optimizado v2.0 de imagen: {image_path}")
    
    try:
        original_image = cv2.imread(str(image_path))
        if original_image is None:
            raise ValueError(f"No se pudo cargar la imagen: {image_path}")
        
        logger.info(f"Imagen cargada - Dimensiones: {original_image.shape}")
        
        # DIAGNÓSTICO MULTIMODAL
        logger.info("Realizando diagnóstico multimodal...")
        
        sharpness = calculate_sharpness(original_image)
        brightness, brightness_stats = calculate_brightness(original_image)
        noise_level = calculate_noise_level(original_image)
        skew_angle, skew_info = detect_skew_angle(original_image)
        
        image_quality = {
            "sharpness": sharpness,
            "sharpness_category": (
                "high" if sharpness > config.LAPLACIAN_VAR_HIGH else
                "medium" if sharpness > config.LAPLACIAN_VAR_MEDIUM else "low"
            ),
            "brightness": brightness,
            "brightness_category": (
                "high" if brightness > config.BRIGHTNESS_THRESHOLD_HIGH else
                "low" if brightness < config.BRIGHTNESS_THRESHOLD_LOW else "normal"
            ),
            "brightness_stats": brightness_stats,
            "noise_level": noise_level,
            "noise_category": "high" if noise_level > config.NOISE_THRESHOLD_HIGH else "normal",
            "skew_angle": skew_angle,
            "skew_info": skew_info,
            "original_dimensions": {
                "width": original_image.shape[1],
                "height": original_image.shape[0]
            }
        }
        
        image_type = classify_image_type(image_quality)
        image_quality["image_type"] = image_type
        
        logger.info(f"Diagnóstico completado:")
        logger.info(f"  - Tipo: {image_type}")
        logger.info(f"  - Nitidez: {sharpness:.1f} ({image_quality['sharpness_category']})")
        logger.info(f"  - Brillo: {brightness:.1f} ({image_quality['brightness_category']})")
        logger.info(f"  - Ruido: {noise_level:.1f} ({image_quality['noise_category']})")
        
        # APLICAR PREPROCESAMIENTO OPTIMIZADO v2.0
        logger.info("Aplicando preprocesamiento optimizado v2.0...")
        processed_image, processing_steps = apply_preprocessing_profile_optimized(
            original_image, image_type, image_quality
        )
        
        # Guardar imagen preprocesada
        preprocessed_path = temp_output_dir / "original_preprocessed.png"
        cv2.imwrite(str(preprocessed_path), processed_image)
        logger.info(f"Imagen preprocesada v2.0 guardada: {preprocessed_path}")
        
        if not config.CLEAN_TEMP_FILES:
            original_copy_path = temp_output_dir / "00_original_input.png"
            cv2.imwrite(str(original_copy_path), original_image)
        
        logger.info("Preprocesamiento optimizado v2.0 completado exitosamente")
        return processed_image, image_quality, processing_steps
        
    except Exception as e:
        logger.error(f"Error durante diagnóstico y procesamiento v2.0: {e}", exc_info=True)
        fallback_image = cv2.imread(str(image_path))
        return fallback_image, {"error": str(e)}, {"error": str(e), "success": False}
