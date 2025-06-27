"""
Procesador de imágenes OPTIMIZADO - Diagnóstico multimodal y preprocesamiento adaptativo
Optimizado específicamente para capturas de WhatsApp y recibos de pago móvil
Objetivo: Replicar automáticamente la calidad de test2.png desde test1.jpg
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
        logger.warning(f"Error detectando inclinación con Tesseract OSD: {e}")
        
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
            
        except Exception as e2:
            logger.warning(f"Error en fallback de detección de inclinación: {e2}")
        
        return 0.0, {"method": "failed", "error": str(e)}

def isolate_document_region(image: np.ndarray) -> Tuple[np.ndarray, Dict]:
    """
    NUEVA FUNCIÓN: Aislamiento y Recorte Inteligente del Documento
    Identifica y extrae la región del recibo eliminando el fondo circundante
    """
    isolation_info = {"method": "none", "success": False}
    
    try:
        original_height, original_width = image.shape[:2]
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        
        # Método 1: Detección de contornos para encontrar el recibo
        logger.debug("Intentando aislamiento por detección de contornos...")
        
        # Aplicar blur y threshold para encontrar contornos
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Threshold adaptativo para encontrar regiones de texto
        thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                     cv2.THRESH_BINARY_INV, 11, 2)
        
        # Operaciones morfológicas para conectar texto
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 20))
        morphed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        # Encontrar contornos
        contours, _ = cv2.findContours(morphed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            # Encontrar el contorno más grande que probablemente sea el recibo
            largest_contour = max(contours, key=cv2.contourArea)
            contour_area = cv2.contourArea(largest_contour)
            total_area = original_width * original_height
            
            # Si el contorno cubre al menos 20% del área total
            if contour_area > (total_area * 0.2):
                # Obtener bounding box del contorno
                x, y, w, h = cv2.boundingRect(largest_contour)
                
                # Añadir margen de seguridad
                margin = 20
                x = max(0, x - margin)
                y = max(0, y - margin)
                w = min(original_width - x, w + 2 * margin)
                h = min(original_height - y, h + 2 * margin)
                
                # Extraer región del documento
                document_region = image[y:y+h, x:x+w]
                
                isolation_info = {
                    "method": "contour_detection",
                    "success": True,
                    "original_size": (original_width, original_height),
                    "cropped_size": (w, h),
                    "crop_coordinates": (x, y, w, h),
                    "area_reduction": f"{(1 - (w*h)/(original_width*original_height))*100:.1f}%"
                }
                
                logger.info(f"Documento aislado exitosamente - Reducción de área: {isolation_info['area_reduction']}")
                return document_region, isolation_info
        
        # Método 2: Fallback - Recorte basado en detección de texto
        logger.debug("Fallback: Recorte basado en detección de texto...")
        
        # Usar Tesseract para encontrar regiones de texto
        try:
            pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            ocr_data = pytesseract.image_to_data(pil_image, output_type=pytesseract.Output.DICT)
            
            # Encontrar bounding box de todo el texto detectado
            valid_boxes = []
            for i, conf in enumerate(ocr_data['conf']):
                if int(conf) > 30:  # Confianza mínima
                    x, y, w, h = ocr_data['left'][i], ocr_data['top'][i], ocr_data['width'][i], ocr_data['height'][i]
                    valid_boxes.append((x, y, x+w, y+h))
            
            if valid_boxes:
                # Calcular bounding box que contenga todo el texto
                min_x = min(box[0] for box in valid_boxes)
                min_y = min(box[1] for box in valid_boxes)
                max_x = max(box[2] for box in valid_boxes)
                max_y = max(box[3] for box in valid_boxes)
                
                # Añadir margen
                margin = 30
                min_x = max(0, min_x - margin)
                min_y = max(0, min_y - margin)
                max_x = min(original_width, max_x + margin)
                max_y = min(original_height, max_y + margin)
                
                w = max_x - min_x
                h = max_y - min_y
                
                # Extraer región
                document_region = image[min_y:max_y, min_x:max_x]
                
                isolation_info = {
                    "method": "text_based_crop",
                    "success": True,
                    "original_size": (original_width, original_height),
                    "cropped_size": (w, h),
                    "crop_coordinates": (min_x, min_y, w, h),
                    "text_boxes_found": len(valid_boxes)
                }
                
                logger.info(f"Documento aislado por texto - {len(valid_boxes)} cajas de texto encontradas")
                return document_region, isolation_info
                
        except Exception as e:
            logger.warning(f"Error en recorte basado en texto: {e}")
        
        # Método 3: Recorte conservador del centro
        logger.debug("Fallback final: Recorte conservador del centro...")
        
        # Recortar 10% de cada borde para eliminar elementos de UI móvil
        crop_margin = 0.1
        x_margin = int(original_width * crop_margin)
        y_margin = int(original_height * crop_margin)
        
        document_region = image[y_margin:original_height-y_margin, 
                              x_margin:original_width-x_margin]
        
        isolation_info = {
            "method": "conservative_center_crop",
            "success": True,
            "original_size": (original_width, original_height),
            "cropped_size": (original_width - 2*x_margin, original_height - 2*y_margin),
            "crop_margin": f"{crop_margin*100}%"
        }
        
        logger.info("Aplicado recorte conservador del centro")
        return document_region, isolation_info
        
    except Exception as e:
        logger.error(f"Error durante aislamiento del documento: {e}")
        isolation_info = {"method": "failed", "success": False, "error": str(e)}
        return image, isolation_info

def apply_aggressive_denoising(image: np.ndarray, noise_level: float) -> Tuple[np.ndarray, list]:
    """
    MEJORADA: Denoising agresivo y adaptativo
    Elimina completamente el ruido antes de la binarización
    """
    applied_filters = []
    processed_image = image.copy()
    
    try:
        # Determinar intensidad de denoising basada en nivel de ruido
        if noise_level > config.NOISE_THRESHOLD_HIGH:
            # Ruido alto - denoising agresivo
            logger.debug(f"Aplicando denoising agresivo (ruido: {noise_level:.2f})")
            
            if len(processed_image.shape) == 3:
                # Imagen a color - usar fastNlMeansDenoisingColored
                processed_image = cv2.fastNlMeansDenoisingColored(processed_image, None, 15, 15, 7, 21)
                applied_filters.append("fastNlMeansDenoisingColored_aggressive")
            else:
                # Imagen en escala de grises
                processed_image = cv2.fastNlMeansDenoising(processed_image, None, 15, 7, 21)
                applied_filters.append("fastNlMeansDenoising_aggressive")
            
            # Filtro adicional para ruido extremo
            processed_image = cv2.medianBlur(processed_image, 5)
            applied_filters.append("medianBlur_5")
            
        elif noise_level > (config.NOISE_THRESHOLD_HIGH * 0.6):
            # Ruido moderado
            logger.debug(f"Aplicando denoising moderado (ruido: {noise_level:.2f})")
            
            if len(processed_image.shape) == 3:
                processed_image = cv2.fastNlMeansDenoisingColored(processed_image, None, 10, 10, 7, 21)
                applied_filters.append("fastNlMeansDenoisingColored_moderate")
            else:
                processed_image = cv2.fastNlMeansDenoising(processed_image, None, 10, 7, 21)
                applied_filters.append("fastNlMeansDenoising_moderate")
        
        else:
            # Ruido bajo - denoising suave
            logger.debug(f"Aplicando denoising suave (ruido: {noise_level:.2f})")
            processed_image = cv2.GaussianBlur(processed_image, (3, 3), 0)
            applied_filters.append("gaussianBlur_light")
        
        # Filtro bilateral adicional para preservar bordes mientras reduce ruido
        if len(processed_image.shape) == 3:
            processed_image = cv2.bilateralFilter(processed_image, 9, 75, 75)
        else:
            processed_image = cv2.bilateralFilter(processed_image, 9, 75, 75)
        applied_filters.append("bilateralFilter")
        
        logger.debug(f"Denoising completado - Filtros aplicados: {applied_filters}")
        return processed_image, applied_filters
        
    except Exception as e:
        logger.error(f"Error durante denoising: {e}")
        return image, ["denoising_failed"]

def apply_high_quality_upscaling(image: np.ndarray, sharpness: float, 
                                original_dimensions: Tuple[int, int]) -> Tuple[np.ndarray, Dict]:
    """
    MEJORADA: Escalado de alta calidad con factores más agresivos
    Objetivo: Replicar la ampliación x2-x3 con mejora de calidad
    """
    scaling_info = {"applied": False, "factor": 1.0, "method": "none"}
    
    try:
        height, width = image.shape[:2]
        orig_width, orig_height = original_dimensions
        
        # Determinar factor de escalado basado en múltiples criterios
        scale_factor = 1.0
        
        # Criterio 1: Baja nitidez requiere escalado agresivo
        if sharpness <= config.LAPLACIAN_VAR_MEDIUM:
            if sharpness <= (config.LAPLACIAN_VAR_MEDIUM * 0.5):
                scale_factor = max(scale_factor, 3.0)  # Nitidez muy baja
                logger.debug(f"Nitidez muy baja ({sharpness:.1f}) - Escalado x3.0")
            else:
                scale_factor = max(scale_factor, 2.5)  # Nitidez baja
                logger.debug(f"Nitidez baja ({sharpness:.1f}) - Escalado x2.5")
        
        # Criterio 2: Dimensiones pequeñas requieren escalado
        if width < 800 or height < 600:
            dimension_factor = max(800/width, 600/height)
            scale_factor = max(scale_factor, dimension_factor)
            logger.debug(f"Dimensiones pequeñas ({width}x{height}) - Factor: {dimension_factor:.1f}")
        
        # Criterio 3: Escalado mínimo para capturas de WhatsApp
        if width < 1000 or height < 800:
            scale_factor = max(scale_factor, 2.0)
            logger.debug("Aplicando escalado mínimo x2.0 para captura móvil")
        
        # Aplicar escalado si es necesario
        if scale_factor > 1.1:  # Solo escalar si el factor es significativo
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            
            # Usar la interpolación de más alta calidad disponible
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
                    "new_size": (new_width, new_height),
                    "reason": f"sharpness={sharpness:.1f}, dimensions={width}x{height}"
                }
                
                logger.info(f"Escalado aplicado: {scale_factor:.1f}x usando {method_used} "
                           f"({width}x{height} -> {new_width}x{new_height})")
                
                return scaled_image, scaling_info
        
        logger.debug(f"No se requiere escalado (factor calculado: {scale_factor:.1f})")
        return image, scaling_info
        
    except Exception as e:
        logger.error(f"Error durante escalado: {e}")
        scaling_info = {"applied": False, "error": str(e)}
        return image, scaling_info

def apply_extreme_binarization(image: np.ndarray) -> Tuple[np.ndarray, Dict]:
    """
    NUEVA FUNCIÓN: Binarización con contraste extremo
    Objetivo: Lograr el esquema "blanco puro y negro puro" como en test2.png
    """
    binarization_info = {"method": "none", "success": False}
    
    try:
        # Convertir a escala de grises si es necesario
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Método 1: Threshold adaptativo optimizado
        logger.debug("Aplicando binarización adaptativa optimizada...")
        
        # Probar diferentes configuraciones de threshold adaptativo
        adaptive_configs = [
            # (blockSize, C, method_name)
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
                # Aplicar threshold adaptativo
                adaptive_thresh = cv2.adaptiveThreshold(
                    gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                    cv2.THRESH_BINARY, block_size, C
                )
                
                # Evaluar calidad de la binarización
                # Criterio: Maximizar contraste y minimizar ruido
                unique_values = np.unique(adaptive_thresh)
                contrast_score = len(unique_values)  # Menos valores únicos = mejor binarización
                
                # Penalizar si hay demasiados valores intermedios
                if len(unique_values) == 2 and 0 in unique_values and 255 in unique_values:
                    score = 100  # Binarización perfecta
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
            # Aplicar operaciones morfológicas para limpiar la binarización
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
            
            # Cerrar pequeños huecos en el texto
            morphed = cv2.morphologyEx(best_result, cv2.MORPH_CLOSE, kernel)
            
            # Eliminar ruido pequeño
            kernel_open = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
            final_result = cv2.morphologyEx(morphed, cv2.MORPH_OPEN, kernel_open)
            
            # Convertir de vuelta a BGR para consistencia
            final_bgr = cv2.cvtColor(final_result, cv2.COLOR_GRAY2BGR)
            
            binarization_info = {
                "method": f"adaptive_threshold_{best_config}",
                "success": True,
                "quality_score": best_score,
                "unique_values": len(np.unique(final_result)),
                "morphological_ops": ["close_2x2", "open_1x1"]
            }
            
            logger.info(f"Binarización extrema aplicada - Método: {best_config}, "
                       f"Calidad: {best_score}, Valores únicos: {len(np.unique(final_result))}")
            
            return final_bgr, binarization_info
        
        # Fallback: Threshold simple con Otsu
        logger.debug("Fallback: Threshold Otsu...")
        _, otsu_thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        otsu_bgr = cv2.cvtColor(otsu_thresh, cv2.COLOR_GRAY2BGR)
        
        binarization_info = {
            "method": "otsu_fallback",
            "success": True,
            "unique_values": len(np.unique(otsu_thresh))
        }
        
        logger.info("Binarización Otsu aplicada como fallback")
        return otsu_bgr, binarization_info
        
    except Exception as e:
        logger.error(f"Error durante binarización extrema: {e}")
        binarization_info = {"method": "failed", "success": False, "error": str(e)}
        # Retornar imagen original convertida a BGR si falla
        if len(image.shape) == 2:
            return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR), binarization_info
        return image, binarization_info

def classify_image_type(diagnosis: Dict) -> str:
    """Clasifica heurísticamente el tipo de imagen basado en el diagnóstico"""
    sharpness = diagnosis.get('sharpness', 0)
    brightness = diagnosis.get('brightness', 128)
    noise = diagnosis.get('noise_level', 0)
    
    # Reglas heurísticas mejoradas para clasificación
    if sharpness < config.LAPLACIAN_VAR_MEDIUM and brightness > config.BRIGHTNESS_THRESHOLD_HIGH:
        return "Captura WhatsApp"  # Más específico
    elif sharpness > config.LAPLACIAN_VAR_HIGH and noise < config.NOISE_THRESHOLD_HIGH:
        return "Escaneo Digital"
    elif noise > config.NOISE_THRESHOLD_HIGH:
        return "Foto Física"
    else:
        return "Imagen Mixta"

def apply_preprocessing_profile(image: np.ndarray, image_type: str, diagnosis: Dict) -> Tuple[np.ndarray, Dict]:
    """
    COMPLETAMENTE REDISEÑADA: Perfil de preprocesamiento optimizado
    Objetivo: Transformar automáticamente test1.jpg en test2.png
    """
    processing_steps = {"applied_steps": [], "isolation_info": {}, "scaling_info": {}, 
                       "denoising_info": {}, "binarization_info": {}}
    processed_image = image.copy()
    original_dimensions = (image.shape[1], image.shape[0])  # (width, height)
    
    try:
        logger.info(f"Iniciando preprocesamiento optimizado para: {image_type}")
        
        # PASO 1: AISLAMIENTO DEL DOCUMENTO (Simular 'Eliminar Fondo')
        logger.info("PASO 1: Aislamiento del documento...")
        processed_image, isolation_info = isolate_document_region(processed_image)
        processing_steps["isolation_info"] = isolation_info
        processing_steps["applied_steps"].append(f"document_isolation_{isolation_info['method']}")
        
        # PASO 2: CORRECCIÓN DE INCLINACIÓN
        skew_angle = diagnosis.get('skew_angle', 0)
        if abs(skew_angle) > 1.0:
            height, width = processed_image.shape[:2]
            center = (width // 2, height // 2)
            rotation_matrix = cv2.getRotationMatrix2D(center, skew_angle, 1.0)
            processed_image = cv2.warpAffine(processed_image, rotation_matrix, (width, height), 
                                           flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
            processing_steps["applied_steps"].append(f"skew_correction_{skew_angle:.1f}deg")
            logger.debug(f"Corrección de inclinación aplicada: {skew_angle:.1f}°")
        
        # PASO 3: ESCALADO DE ALTA CALIDAD (Simular 'Ampliar x2 y Mejorar Calidad')
        logger.info("PASO 2: Escalado de alta calidad...")
        sharpness = diagnosis.get('sharpness', 0)
        processed_image, scaling_info = apply_high_quality_upscaling(
            processed_image, sharpness, original_dimensions
        )
        processing_steps["scaling_info"] = scaling_info
        if scaling_info["applied"]:
            processing_steps["applied_steps"].append(f"upscale_{scaling_info['factor']:.1f}x_{scaling_info['method']}")
        
        # PASO 4: DENOISING AGRESIVO (Simular 'Eliminar Todo Ruido')
        logger.info("PASO 3: Denoising agresivo...")
        noise_level = diagnosis.get('noise_level', 0)
        processed_image, denoising_filters = apply_aggressive_denoising(processed_image, noise_level)
        processing_steps["denoising_info"] = {"filters_applied": denoising_filters, "noise_level": noise_level}
        processing_steps["applied_steps"].extend(denoising_filters)
        
        # PASO 5: AJUSTES DE BRILLO/CONTRASTE ESPECÍFICOS POR TIPO
        logger.info("PASO 4: Ajustes específicos por tipo de imagen...")
        brightness = diagnosis.get('brightness', 128)
        
        if image_type == "Captura WhatsApp":
            # Optimización específica para capturas de WhatsApp
            pil_image = Image.fromarray(cv2.cvtColor(processed_image, cv2.COLOR_BGR2RGB))
            
            # Aumentar contraste agresivamente
            enhancer = ImageEnhance.Contrast(pil_image)
            pil_image = enhancer.enhance(1.5)  # Más agresivo
            
            # Ajustar brillo para eliminar fondos grises
            enhancer = ImageEnhance.Brightness(pil_image)
            pil_image = enhancer.enhance(0.85)
            
            processed_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            processing_steps["applied_steps"].append("whatsapp_optimization")
            
        elif image_type == "Foto Física":
            # Ajustes para fotos físicas
            processed_image = cv2.convertScaleAbs(processed_image, alpha=1.2, beta=10)
            processing_steps["applied_steps"].append("physical_photo_enhancement")
            
        elif image_type == "Escaneo Digital":
            # Mejora de nitidez para escaneos
            kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            processed_image = cv2.filter2D(processed_image, -1, kernel)
            processing_steps["applied_steps"].append("scan_sharpening")
        
        # Ajustes generales de brillo basados en diagnóstico
        if brightness < config.BRIGHTNESS_THRESHOLD_LOW:
            processed_image = cv2.convertScaleAbs(processed_image, alpha=1.0, beta=40)
            processing_steps["applied_steps"].append("brightness_boost_high")
        elif brightness > config.BRIGHTNESS_THRESHOLD_HIGH:
            processed_image = cv2.convertScaleAbs(processed_image, alpha=0.85, beta=-25)
            processing_steps["applied_steps"].append("brightness_reduction_high")
        
        # PASO 6: BINARIZACIÓN EXTREMA (Simular 'Blanco y Gris' -> 'Blanco Puro y Negro Puro')
        logger.info("PASO 5: Binarización con contraste extremo...")
        processed_image, binarization_info = apply_extreme_binarization(processed_image)
        processing_steps["binarization_info"] = binarization_info
        processing_steps["applied_steps"].append(f"extreme_binarization_{binarization_info['method']}")
        
        # Información final del procesamiento
        processing_steps["image_type"] = image_type
        processing_steps["success"] = True
        processing_steps["total_steps"] = len(processing_steps["applied_steps"])
        
        logger.info(f"Preprocesamiento completado - {processing_steps['total_steps']} pasos aplicados")
        logger.info(f"Pasos: {' -> '.join(processing_steps['applied_steps'][:5])}...")  # Mostrar primeros 5
        
    except Exception as e:
        logger.error(f"Error durante preprocesamiento optimizado: {e}", exc_info=True)
        processing_steps["error"] = str(e)
        processing_steps["success"] = False
        # Retornar imagen original si falla el preprocesamiento
        processed_image = image.copy()
    
    return processed_image, processing_steps

def diagnose_and_process_image(image_path: Path, temp_output_dir: Path) -> Tuple[np.ndarray, Dict, Dict]:
    """
    FUNCIÓN PRINCIPAL MEJORADA: Diagnóstico y procesamiento optimizado
    Objetivo: Replicar automáticamente la transformación test1.jpg -> test2.png
    """
    logger.info(f"Iniciando diagnóstico optimizado de imagen: {image_path}")
    
    try:
        # Cargar imagen original
        original_image = cv2.imread(str(image_path))
        if original_image is None:
            raise ValueError(f"No se pudo cargar la imagen: {image_path}")
        
        logger.info(f"Imagen cargada - Dimensiones: {original_image.shape}")
        
        # DIAGNÓSTICO MULTIMODAL MEJORADO
        logger.info("Realizando diagnóstico multimodal avanzado...")
        
        # Calcular métricas de calidad
        sharpness = calculate_sharpness(original_image)
        brightness, brightness_stats = calculate_brightness(original_image)
        noise_level = calculate_noise_level(original_image)
        skew_angle, skew_info = detect_skew_angle(original_image)
        
        # Compilar diagnóstico completo
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
        
        # Clasificar tipo de imagen con lógica mejorada
        image_type = classify_image_type(image_quality)
        image_quality["image_type"] = image_type
        
        logger.info(f"Diagnóstico completado:")
        logger.info(f"  - Tipo: {image_type}")
        logger.info(f"  - Nitidez: {sharpness:.1f} ({image_quality['sharpness_category']})")
        logger.info(f"  - Brillo: {brightness:.1f} ({image_quality['brightness_category']})")
        logger.info(f"  - Ruido: {noise_level:.1f} ({image_quality['noise_category']})")
        logger.info(f"  - Inclinación: {skew_angle:.1f}°")
        
        # APLICAR PREPROCESAMIENTO OPTIMIZADO
        logger.info("Aplicando preprocesamiento optimizado...")
        processed_image, processing_steps = apply_preprocessing_profile(
            original_image, image_type, image_quality
        )
        
        # Guardar imagen preprocesada para depuración
        preprocessed_path = temp_output_dir / "original_preprocessed.png"
        cv2.imwrite(str(preprocessed_path), processed_image)
        logger.info(f"Imagen preprocesada guardada: {preprocessed_path}")
        
        # Guardar imagen original para comparación
        if not config.CLEAN_TEMP_FILES:
            original_copy_path = temp_output_dir / "00_original_input.png"
            cv2.imwrite(str(original_copy_path), original_image)
            logger.debug(f"Copia original guardada: {original_copy_path}")
        
        logger.info("Preprocesamiento optimizado completado exitosamente")
        return processed_image, image_quality, processing_steps
        
    except Exception as e:
        logger.error(f"Error durante diagnóstico y procesamiento optimizado: {e}", exc_info=True)
        # Retornar imagen original en caso de error
        fallback_image = cv2.imread(str(image_path))
        return fallback_image, {"error": str(e)}, {"error": str(e), "success": False}
