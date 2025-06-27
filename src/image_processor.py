"""
Procesador de imágenes - Diagnóstico multimodal y preprocesamiento adaptativo
Optimiza imágenes para OCR basándose en análisis de calidad automático
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
        
        # Calcular histograma
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
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
    """Calcula nivel de ruido basado en desviación estándar en áreas uniformes"""
    try:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        
        # Aplicar filtro Gaussiano para encontrar áreas uniformes
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        noise_map = cv2.absdiff(gray, blurred)
        
        # Calcular desviación estándar del mapa de ruido
        noise_level = np.std(noise_map)
        return float(noise_level)
    except Exception as e:
        logger.warning(f"Error calculando nivel de ruido: {e}")
        return 0.0

def detect_skew_angle(image: np.ndarray) -> Tuple[float, Dict]:
    """Detecta ángulo de inclinación usando Tesseract OSD"""
    try:
        pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        
        # Intentar detección de orientación con Tesseract
        osd_config = f'--psm {config.TESSERACT_PSM_OSD_DETECTION} --oem {config.TESSERACT_OEM}'
        osd_data = pytesseract.image_to_osd(pil_image, config=osd_config)
        
        # Parsear datos OSD
        osd_info = {}
        for line in osd_data.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                osd_info[key.strip()] = value.strip()
        
        # Extraer ángulo de rotación
        rotate_angle = float(osd_info.get('Rotate', '0'))
        
        return rotate_angle, osd_info
        
    except Exception as e:
        logger.warning(f"Error detectando inclinación con Tesseract OSD: {e}")
        
        # Fallback: detección de líneas con Hough
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)
            lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)
            
            if lines is not None:
                angles = []
                for rho, theta in lines[:10]:  # Considerar solo las primeras 10 líneas
                    angle = np.degrees(theta) - 90
                    angles.append(angle)
                
                # Calcular ángulo promedio
                avg_angle = np.mean(angles) if angles else 0.0
                return float(avg_angle), {"method": "hough_lines", "lines_detected": len(lines)}
            
        except Exception as e2:
            logger.warning(f"Error en fallback de detección de inclinación: {e2}")
        
        return 0.0, {"method": "failed", "error": str(e)}

def classify_image_type(diagnosis: Dict) -> str:
    """Clasifica heurísticamente el tipo de imagen basado en el diagnóstico"""
    sharpness = diagnosis.get('sharpness', 0)
    brightness = diagnosis.get('brightness', 128)
    noise = diagnosis.get('noise_level', 0)
    
    # Reglas heurísticas para clasificación
    if sharpness < config.LAPLACIAN_VAR_MEDIUM and brightness > config.BRIGHTNESS_THRESHOLD_HIGH:
        return "Foto de Pantalla"
    elif sharpness > config.LAPLACIAN_VAR_HIGH and noise < config.NOISE_THRESHOLD_HIGH:
        return "Escaneo"
    elif noise > config.NOISE_THRESHOLD_HIGH:
        return "Foto Física"
    else:
        return "Imagen Mixta"

def apply_preprocessing_profile(image: np.ndarray, image_type: str, diagnosis: Dict) -> Tuple[np.ndarray, Dict]:
    """Aplica perfil de preprocesamiento específico según tipo de imagen y diagnóstico"""
    processing_steps = {"applied_steps": []}
    processed_image = image.copy()
    
    try:
        # Corrección de inclinación si es necesaria
        skew_angle = diagnosis.get('skew_angle', 0)
        if abs(skew_angle) > 1.0:  # Solo corregir si la inclinación es significativa
            height, width = processed_image.shape[:2]
            center = (width // 2, height // 2)
            rotation_matrix = cv2.getRotationMatrix2D(center, skew_angle, 1.0)
            processed_image = cv2.warpAffine(processed_image, rotation_matrix, (width, height), 
                                           flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
            processing_steps["applied_steps"].append(f"skew_correction_{skew_angle:.1f}deg")
        
        # Escalado inteligente para imágenes de baja resolución
        height, width = processed_image.shape[:2]
        if width < 800 or height < 600:
            scale_factor = max(800/width, 600/height)
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            processed_image = cv2.resize(processed_image, (new_width, new_height), 
                                       interpolation=cv2.INTER_LANCZOS4)
            processing_steps["applied_steps"].append(f"upscale_{scale_factor:.1f}x")
        
        # Ajustes específicos por tipo de imagen
        if image_type == "Foto de Pantalla":
            # Mejorar contraste y reducir brillo excesivo
            pil_image = Image.fromarray(cv2.cvtColor(processed_image, cv2.COLOR_BGR2RGB))
            enhancer = ImageEnhance.Contrast(pil_image)
            pil_image = enhancer.enhance(1.2)
            enhancer = ImageEnhance.Brightness(pil_image)
            pil_image = enhancer.enhance(0.9)
            processed_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            processing_steps["applied_steps"].append("screen_photo_enhancement")
            
        elif image_type == "Foto Física":
            # Reducción de ruido agresiva
            processed_image = cv2.fastNlMeansDenoisingColored(processed_image, None, 10, 10, 7, 21)
            processing_steps["applied_steps"].append("noise_reduction_aggressive")
            
        elif image_type == "Escaneo":
            # Mejora de nitidez ligera
            kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            processed_image = cv2.filter2D(processed_image, -1, kernel)
            processing_steps["applied_steps"].append("sharpening_filter")
        
        # Ajustes de brillo/contraste basados en diagnóstico
        brightness = diagnosis.get('brightness', 128)
        if brightness < config.BRIGHTNESS_THRESHOLD_LOW:
            # Imagen oscura - aumentar brillo
            processed_image = cv2.convertScaleAbs(processed_image, alpha=1.0, beta=30)
            processing_steps["applied_steps"].append("brightness_increase")
        elif brightness > config.BRIGHTNESS_THRESHOLD_HIGH:
            # Imagen muy brillante - reducir brillo
            processed_image = cv2.convertScaleAbs(processed_image, alpha=0.9, beta=-20)
            processing_steps["applied_steps"].append("brightness_decrease")
        
        # Binarización adaptativa como paso final
        gray = cv2.cvtColor(processed_image, cv2.COLOR_BGR2GRAY)
        adaptive_thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                              cv2.THRESH_BINARY, 11, 2)
        # Convertir de vuelta a BGR para consistencia
        processed_image = cv2.cvtColor(adaptive_thresh, cv2.COLOR_GRAY2BGR)
        processing_steps["applied_steps"].append("adaptive_binarization")
        
        processing_steps["image_type"] = image_type
        processing_steps["success"] = True
        
    except Exception as e:
        logger.error(f"Error durante preprocesamiento: {e}", exc_info=True)
        processing_steps["error"] = str(e)
        processing_steps["success"] = False
        # Retornar imagen original si falla el preprocesamiento
        processed_image = image.copy()
    
    return processed_image, processing_steps

def diagnose_and_process_image(image_path: Path, temp_output_dir: Path) -> Tuple[np.ndarray, Dict, Dict]:
    """
    Realiza diagnóstico multimodal completo y preprocesamiento adaptativo
    
    Args:
        image_path: Ruta a la imagen original
        temp_output_dir: Directorio para guardar archivos de depuración
        
    Returns:
        Tuple[np.ndarray, Dict, Dict]: (imagen_procesada, calidad_inicial, pasos_procesamiento)
    """
    logger.info(f"Iniciando diagnóstico de imagen: {image_path}")
    
    try:
        # Cargar imagen original
        original_image = cv2.imread(str(image_path))
        if original_image is None:
            raise ValueError(f"No se pudo cargar la imagen: {image_path}")
        
        # Diagnóstico multimodal
        logger.info("Realizando diagnóstico multimodal...")
        
        # Calcular métricas de calidad
        sharpness = calculate_sharpness(original_image)
        brightness, brightness_stats = calculate_brightness(original_image)
        noise_level = calculate_noise_level(original_image)
        skew_angle, skew_info = detect_skew_angle(original_image)
        
        # Compilar diagnóstico
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
        
        # Clasificar tipo de imagen
        image_type = classify_image_type(image_quality)
        image_quality["image_type"] = image_type
        
        logger.info(f"Diagnóstico completado - Tipo: {image_type}, Nitidez: {sharpness:.1f}, "
                   f"Brillo: {brightness:.1f}, Ruido: {noise_level:.1f}, Inclinación: {skew_angle:.1f}°")
        
        # Aplicar preprocesamiento adaptativo
        logger.info("Aplicando preprocesamiento adaptativo...")
        processed_image, processing_steps = apply_preprocessing_profile(
            original_image, image_type, image_quality
        )
        
        # Guardar imagen preprocesada para depuración
        preprocessed_path = temp_output_dir / "original_preprocessed.png"
        cv2.imwrite(str(preprocessed_path), processed_image)
        logger.info(f"Imagen preprocesada guardada: {preprocessed_path}")
        
        return processed_image, image_quality, processing_steps
        
    except Exception as e:
        logger.error(f"Error durante diagnóstico y procesamiento: {e}", exc_info=True)
        # Retornar imagen original en caso de error
        fallback_image = cv2.imread(str(image_path))
        return fallback_image, {"error": str(e)}, {"error": str(e), "success": False}
