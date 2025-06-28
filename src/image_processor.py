"""
Procesador de Imágenes v3.0 - Con Inversión Inteligente de Colores
Optimizado para fondos oscuros y comprobantes de pago móvil
"""

import cv2
import numpy as np
import pytesseract
from PIL import Image, ImageEnhance
from typing import Tuple, Dict, List
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
            "max": int(np.max(gray)),
            "median": float(np.median(gray))
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

def detect_dark_background(image: np.ndarray) -> Tuple[bool, Dict]:
    """
    Detecta si la imagen tiene fondo oscuro que requiere inversión
    """
    try:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        
        # Calcular estadísticas de brillo
        mean_brightness = np.mean(gray)
        median_brightness = np.median(gray)
        
        # Analizar histograma
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        
        # Porcentaje de píxeles oscuros (0-85) vs claros (170-255)
        dark_pixels = np.sum(hist[0:85])
        bright_pixels = np.sum(hist[170:255])
        total_pixels = gray.shape[0] * gray.shape[1]
        
        dark_percentage = (dark_pixels / total_pixels) * 100
        bright_percentage = (bright_pixels / total_pixels) * 100
        
        # Criterios para detectar fondo oscuro
        is_dark_background = (
            mean_brightness < config.DARK_BACKGROUND_THRESHOLD and
            median_brightness < config.DARK_BACKGROUND_THRESHOLD and
            dark_percentage > 60  # Más del 60% de píxeles oscuros
        )
        
        analysis = {
            "mean_brightness": float(mean_brightness),
            "median_brightness": float(median_brightness),
            "dark_percentage": float(dark_percentage),
            "bright_percentage": float(bright_percentage),
            "is_dark_background": is_dark_background,
            "confidence": float(dark_percentage / 100) if is_dark_background else 0.0
        }
        
        logger.info(f"Análisis de fondo: {'OSCURO' if is_dark_background else 'CLARO'} "
                   f"(brillo: {mean_brightness:.1f}, oscuros: {dark_percentage:.1f}%)")
        
        return is_dark_background, analysis
        
    except Exception as e:
        logger.error(f"Error detectando fondo oscuro: {e}")
        return False, {"error": str(e)}

def apply_smart_color_inversion(image: np.ndarray, dark_analysis: Dict) -> Tuple[np.ndarray, Dict]:
    """
    Aplica inversión inteligente de colores para fondos oscuros
    """
    inversion_info = {"applied": False, "method": "none", "confidence": 0.0}
    
    try:
        if not dark_analysis.get("is_dark_background", False):
            logger.info("Fondo claro detectado - No se requiere inversión")
            return image, inversion_info
        
        confidence = dark_analysis.get("confidence", 0.0)
        if confidence < config.INVERSION_CONFIDENCE_THRESHOLD:
            logger.info(f"Confianza insuficiente para inversión: {confidence:.2f}")
            return image, inversion_info
        
        logger.info(f"Aplicando inversión de colores (confianza: {confidence:.2f})")
        
        # Convertir a escala de grises si es necesario
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Aplicar inversión
        inverted = cv2.bitwise_not(gray)
        
        # Mejorar contraste después de la inversión
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(inverted)
        
        # Convertir de vuelta a BGR para consistencia
        if len(image.shape) == 3:
            result = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)
        else:
            result = enhanced
        
        inversion_info = {
            "applied": True,
            "method": "bitwise_not_with_clahe",
            "confidence": confidence,
            "original_brightness": dark_analysis.get("mean_brightness", 0),
            "inverted_brightness": float(np.mean(enhanced))
        }
        
        logger.info(f"Inversión aplicada exitosamente - Nuevo brillo: {inversion_info['inverted_brightness']:.1f}")
        
        return result, inversion_info
        
    except Exception as e:
        logger.error(f"Error durante inversión de colores: {e}")
        inversion_info = {"applied": False, "method": "failed", "error": str(e)}
        return image, inversion_info

def detect_skew_angle(image: np.ndarray) -> Tuple[float, Dict]:
    """Detecta ángulo de inclinación usando Tesseract OSD o fallback"""
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
        # Fallback a detección de líneas
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)
            lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)
            
            if lines is not None:
                angles = []
                for rho, theta in lines[:10]:
                    angle = np.degrees(theta) - 90
                    angles.append(angle)
                
                avg_angle = np.mean(angles) if angles else 0.0
                return float(avg_angle), {"method": "hough_lines", "lines_detected": len(lines)}
            
        except Exception:
            pass
        
        return 0.0, {"method": "failed", "error": str(e)}

def apply_aggressive_denoising(image: np.ndarray, noise_level: float) -> Tuple[np.ndarray, List[str]]:
    """Denoising agresivo y adaptativo"""
    applied_filters = []
    processed_image = image.copy()
    
    try:
        if noise_level > config.NOISE_THRESHOLD_HIGH:
            if len(processed_image.shape) == 3:
                processed_image = cv2.fastNlMeansDenoisingColored(processed_image, None, 15, 15, 7, 21)
                applied_filters.append("fastNlMeansDenoisingColored_aggressive")
            else:
                processed_image = cv2.fastNlMeansDenoising(processed_image, None, 15, 7, 21)
                applied_filters.append("fastNlMeansDenoising_aggressive")
            
            processed_image = cv2.medianBlur(processed_image, 5)
            applied_filters.append("medianBlur_5")
            
        elif noise_level > config.NOISE_THRESHOLD_MEDIUM:
            if len(processed_image.shape) == 3:
                processed_image = cv2.fastNlMeansDenoisingColored(processed_image, None, 10, 10, 7, 21)
                applied_filters.append("fastNlMeansDenoisingColored_moderate")
            else:
                processed_image = cv2.fastNlMeansDenoising(processed_image, None, 10, 7, 21)
                applied_filters.append("fastNlMeansDenoising_moderate")
        else:
            processed_image = cv2.GaussianBlur(processed_image, (3, 3), 0)
            applied_filters.append("gaussianBlur_light")
        
        # Filtro bilateral siempre
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
        
        # Determinar factor de escalado basado en nitidez y dimensiones
        if sharpness <= config.LAPLACIAN_VAR_MEDIUM:
            scale_factor = max(scale_factor, 2.5)
            
        if width < 800 or height < 600:
            dimension_factor = max(800/width, 600/height)
            scale_factor = max(scale_factor, dimension_factor)
            
        if width < 1000 or height < 800:
            scale_factor = max(scale_factor, 2.0)
        
        if scale_factor > 1.1:
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            
            # Usar LANCZOS4 para mejor calidad
            scaled_image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)
            
            scaling_info = {
                "applied": True,
                "factor": scale_factor,
                "method": "LANCZOS4",
                "original_size": (width, height),
                "new_size": (new_width, new_height)
            }
            
            logger.info(f"Escalado aplicado: {scale_factor:.1f}x usando LANCZOS4")
            return scaled_image, scaling_info
        
        return image, scaling_info
        
    except Exception as e:
        logger.error(f"Error durante escalado: {e}")
        return image, {"applied": False, "error": str(e)}

def apply_extreme_binarization(image: np.ndarray) -> Tuple[np.ndarray, Dict]:
    """
    Binarización extrema optimizada para texto negro sobre fondo claro
    """
    binarization_info = {"method": "none", "success": False}
    
    try:
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        best_result = None
        best_score = 0
        best_config = None
        
        # Configuraciones adaptativas optimizadas
        adaptive_configs = [
            (15, 8, "adaptive_15_8"),
            (21, 10, "adaptive_21_10"),
            (11, 6, "adaptive_11_6"),
            (25, 12, "adaptive_25_12")
        ]
        
        for block_size, C, config_name in adaptive_configs:
            try:
                adaptive_thresh = cv2.adaptiveThreshold(
                    gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                    cv2.THRESH_BINARY, block_size, C
                )
                
                # Evaluar calidad de binarización
                unique_values = np.unique(adaptive_thresh)
                score = 100 if len(unique_values) == 2 else max(0, 100 - len(unique_values))
                
                if score > best_score:
                    best_score = score
                    best_result = adaptive_thresh
                    best_config = config_name
                    
            except Exception as e:
                logger.warning(f"Error con configuración {config_name}: {e}")
                continue
        
        if best_result is not None:
            # Aplicar operaciones morfológicas para limpiar
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
            morphed = cv2.morphologyEx(best_result, cv2.MORPH_CLOSE, kernel)
            
            kernel_open = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
            final_result = cv2.morphologyEx(morphed, cv2.MORPH_OPEN, kernel_open)
            
            # Asegurar que el texto sea negro sobre fondo blanco
            # Contar píxeles blancos vs negros
            white_pixels = np.sum(final_result == 255)
            black_pixels = np.sum(final_result == 0)
            
            # Si hay más píxeles negros que blancos, invertir
            if black_pixels > white_pixels:
                final_result = cv2.bitwise_not(final_result)
                logger.info("Inversión aplicada para asegurar texto negro sobre fondo blanco")
            
            # Convertir a BGR para consistencia
            final_bgr = cv2.cvtColor(final_result, cv2.COLOR_GRAY2BGR)
            
            binarization_info = {
                "method": f"adaptive_threshold_{best_config}",
                "success": True,
                "quality_score": best_score,
                "inverted_for_text": black_pixels > white_pixels
            }
            
            logger.info(f"Binarización aplicada: {best_config} (score: {best_score})")
            return final_bgr, binarization_info
        
        # Fallback: Threshold Otsu
        _, otsu_thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Verificar orientación del texto
        white_pixels = np.sum(otsu_thresh == 255)
        black_pixels = np.sum(otsu_thresh == 0)
        
        if black_pixels > white_pixels:
            otsu_thresh = cv2.bitwise_not(otsu_thresh)
        
        otsu_bgr = cv2.cvtColor(otsu_thresh, cv2.COLOR_GRAY2BGR)
        
        binarization_info = {
            "method": "otsu_fallback",
            "success": True,
            "inverted_for_text": black_pixels > white_pixels
        }
        
        return otsu_bgr, binarization_info
        
    except Exception as e:
        logger.error(f"Error durante binarización: {e}")
        binarization_info = {"method": "failed", "success": False, "error": str(e)}
        if len(image.shape) == 2:
            return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR), binarization_info
        return image, binarization_info

def classify_image_type(diagnosis: Dict) -> str:
    """Clasifica el tipo de imagen basado en el diagnóstico"""
    sharpness = diagnosis.get('sharpness', 0)
    brightness = diagnosis.get('brightness', 128)
    noise = diagnosis.get('noise_level', 0)
    is_dark = diagnosis.get('dark_background_analysis', {}).get('is_dark_background', False)
    
    if is_dark:
        return "Captura Fondo Oscuro"
    elif sharpness < config.LAPLACIAN_VAR_MEDIUM and brightness > config.BRIGHTNESS_THRESHOLD_HIGH:
        return "Captura WhatsApp"
    elif sharpness > config.LAPLACIAN_VAR_HIGH and noise < config.NOISE_THRESHOLD_HIGH:
        return "Escaneo Digital"
    elif noise > config.NOISE_THRESHOLD_HIGH:
        return "Foto Física"
    else:
        return "Imagen Mixta"

def apply_preprocessing_profile(image: np.ndarray, image_type: str, diagnosis: Dict) -> Tuple[np.ndarray, Dict]:
    """
    Perfil de preprocesamiento optimizado con inversión inteligente
    """
    processing_steps = {
        "applied_steps": [],
        "scaling_info": {},
        "denoising_info": {},
        "binarization_info": {},
        "inversion_info": {},
        "image_type": image_type
    }
    
    processed_image = image.copy()
    
    try:
        logger.info(f"Aplicando preprocesamiento para: {image_type}")
        
        # 1. INVERSIÓN INTELIGENTE DE COLORES (NUEVO)
        dark_analysis = diagnosis.get('dark_background_analysis', {})
        processed_image, inversion_info = apply_smart_color_inversion(processed_image, dark_analysis)
        processing_steps["inversion_info"] = inversion_info
        if inversion_info["applied"]:
            processing_steps["applied_steps"].append(f"smart_color_inversion_{inversion_info['method']}")
        
        # 2. Corrección de inclinación
        skew_angle = diagnosis.get('skew_angle', 0)
        if abs(skew_angle) > 1.0:
            height, width = processed_image.shape[:2]
            center = (width // 2, height // 2)
            rotation_matrix = cv2.getRotationMatrix2D(center, skew_angle, 1.0)
            processed_image = cv2.warpAffine(
                processed_image, rotation_matrix, (width, height),
                flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
            )
            processing_steps["applied_steps"].append(f"skew_correction_{skew_angle:.1f}deg")
            logger.debug(f"Corrección de inclinación: {skew_angle:.1f}°")
        
        # 3. Escalado de alta calidad
        sharpness = diagnosis.get('sharpness', 0)
        processed_image, scaling_info = apply_high_quality_upscaling(processed_image, sharpness)
        processing_steps["scaling_info"] = scaling_info
        if scaling_info["applied"]:
            processing_steps["applied_steps"].append(f"upscale_{scaling_info['factor']:.1f}x_{scaling_info['method']}")
        
        # 4. Denoising agresivo
        noise_level = diagnosis.get('noise_level', 0)
        processed_image, denoising_filters = apply_aggressive_denoising(processed_image, noise_level)
        processing_steps["denoising_info"] = {
            "filters_applied": denoising_filters,
            "noise_level": noise_level
        }
        processing_steps["applied_steps"].extend(denoising_filters)
        
        # 5. Ajustes específicos por tipo de imagen
        brightness = diagnosis.get('brightness', 128)
        
        if image_type == "Captura Fondo Oscuro":
            # Optimización específica para fondos oscuros ya invertidos
            processed_image = cv2.convertScaleAbs(processed_image, alpha=1.1, beta=5)
            processing_steps["applied_steps"].append("dark_background_optimization")
            
        elif image_type == "Captura WhatsApp":
            # Optimización específica para capturas de WhatsApp
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
        
        # 6. Ajustes generales de brillo (solo si no se aplicó inversión)
        if not inversion_info.get("applied", False):
            if brightness < config.BRIGHTNESS_THRESHOLD_LOW:
                processed_image = cv2.convertScaleAbs(processed_image, alpha=1.0, beta=40)
                processing_steps["applied_steps"].append("brightness_boost_high")
            elif brightness > config.BRIGHTNESS_THRESHOLD_HIGH:
                processed_image = cv2.convertScaleAbs(processed_image, alpha=0.85, beta=-25)
                processing_steps["applied_steps"].append("brightness_reduction_high")
        
        # 7. Binarización extrema (MEJORADA)
        processed_image, binarization_info = apply_extreme_binarization(processed_image)
        processing_steps["binarization_info"] = binarization_info
        processing_steps["applied_steps"].append(f"extreme_binarization_{binarization_info['method']}")
        
        processing_steps["success"] = True
        processing_steps["total_steps"] = len(processing_steps["applied_steps"])
        
        logger.info(f"Preprocesamiento completado - {processing_steps['total_steps']} pasos aplicados")
        
        return processed_image, processing_steps
        
    except Exception as e:
        logger.error(f"Error durante preprocesamiento: {e}")
        processing_steps["error"] = str(e)
        processing_steps["success"] = False
        return image, processing_steps

def process_image(image_path: str, output_dir: str) -> Tuple[np.ndarray, Dict, Dict]:
    """
    Función principal de procesamiento de imagen con inversión inteligente
    """
    logger.info(f"Procesando imagen: {image_path}")
    
    # Cargar imagen
    raw_image = cv2.imread(image_path)
    if raw_image is None:
        raise ValueError(f"No se pudo cargar la imagen: {image_path}")
    
    logger.info(f"Imagen cargada - Dimensiones: {raw_image.shape}")
    
    # Diagnóstico completo de imagen
    sharpness = calculate_sharpness(raw_image)
    brightness, brightness_stats = calculate_brightness(raw_image)
    noise_level = calculate_noise_level(raw_image)
    skew_angle, skew_info = detect_skew_angle(raw_image)
    
    # NUEVO: Análisis de fondo oscuro
    is_dark_background, dark_analysis = detect_dark_background(raw_image)
    
    diagnosis = {
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
        "dark_background_analysis": dark_analysis,  # NUEVO
        "original_dimensions": {
            "width": raw_image.shape[1],
            "height": raw_image.shape[0]
        }
    }
    
    # Clasificar tipo de imagen
    image_type = classify_image_type(diagnosis)
    diagnosis["image_type"] = image_type
    
    logger.info(f"Diagnóstico completado:")
    logger.info(f"  - Tipo: {image_type}")
    logger.info(f"  - Nitidez: {sharpness:.1f} ({diagnosis['sharpness_category']})")
    logger.info(f"  - Brillo: {brightness:.1f} ({diagnosis['brightness_category']})")
    logger.info(f"  - Ruido: {noise_level:.1f} ({diagnosis['noise_category']})")
    logger.info(f"  - Fondo oscuro: {'SÍ' if is_dark_background else 'NO'}")
    
    # Aplicar preprocesamiento
    processed_image, processing_steps = apply_preprocessing_profile(raw_image, image_type, diagnosis)
    
    # Guardar imagen preprocesada
    if config.SAVE_PREPROCESSED_IMAGES:
        preprocessed_path = f"{output_dir}/{config.PREPROCESSED_IMAGE_NAME}"
        cv2.imwrite(preprocessed_path, processed_image)
        logger.info(f"Imagen preprocesada guardada: {preprocessed_path}")
    
    logger.info("Procesamiento de imagen completado exitosamente")
    return processed_image, diagnosis, processing_steps
