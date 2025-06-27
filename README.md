# Sistema Inteligente de OCR para Pagos Móviles

## Descripción General

Este sistema implementa una solución avanzada de OCR (Reconocimiento Óptico de Caracteres) específicamente diseñada para la extracción automatizada de datos de recibos de pagos móviles y transferencias bancarias. La solución está optimizada para entornos de bajos recursos y utiliza exclusivamente Tesseract OCR y OpenCV.

## Características Principales

### 🔍 Clasificación Inteligente
- Detección automática de recibos legítimos vs contenido irrelevante
- Filtrado rápido para optimizar recursos de procesamiento

### 🖼️ Preprocesamiento Multimodal y Adaptativo
- Diagnóstico automático de calidad de imagen (nitidez, brillo, ruido, distorsión)
- Aplicación de perfiles de optimización específicos según el tipo de imagen
- Corrección automática de inclinación y mejoras de contraste

### 📍 Extracción Híbrida y Robusta
- Sistema de plantillas preestablecidas para recibos conocidos
- Zonas de Interés (ZOI) dinámicas como fallback inteligente
- Heurísticas contextuales para campos críticos (montos, referencias)

### 🧠 Bucle de Aprendizaje Semántico
- Auto-mejora continua basada en feedback estructurado
- Modelo probabilístico que aprende de correcciones manuales
- Análisis de causas raíz para optimización dirigida

### ⚡ Optimización de Recursos
- Diseñado exclusivamente con Tesseract y OpenCV
- Sin dependencias de modelos de IA pesados (ONNX, CRAFT, CRNN)
- Rendimiento óptimo en servidores con recursos limitados

## Arquitectura del Sistema

\`\`\`
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   N8N/Sistema   │───▶│  Orquestador     │───▶│   Clasificador  │
│    Externo      │    │  Inteligente     │    │   Documentos    │
└─────────────────┘    │   (main.py)      │    └─────────────────┘
                       └──────────────────┘             │
                                │                       ▼
                                │              ┌─────────────────┐
                                │              │ ¿Es un recibo?  │
                                │              └─────────────────┘
                                │                       │
                                ▼                       ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │   Procesador     │    │   Salida JSON   │
                       │   de Imágenes    │    │  "no_receipt"   │
                       └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │   Motor OCR      │
                       │  (Tesseract)     │
                       └──────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │ Gestor Plantillas│
                       │  y ZOI Dinámicas │
                       └──────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │  Extractor de    │
                       │     Datos        │
                       └──────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │ Gestor Aprendizaje│
                       │   y Feedback     │
                       └──────────────────┘
\`\`\`

## Estructura del Proyecto

\`\`\`
proyecto_ocr_pagos/
├── src/                          # Código fuente modular
│   ├── main.py                   # Orquestador principal
│   ├── config.py                 # Variables globales y configuraciones
│   ├── image_processor.py        # Preprocesamiento y diagnóstico
│   ├── template_manager.py       # Gestión de plantillas y ZOI
│   ├── ocr_engine.py            # Interfaz con Tesseract
│   ├── data_extractor.py        # Extracción dirigida y validación
│   ├── learning_manager.py      # Gestión de feedback y aprendizaje
│   ├── document_classifier.py   # Clasificación de documentos
│   └── update_probabilistic_model.py # Script de reentrenamiento
├── templates/                    # Plantillas visuales y metadatos
│   ├── APPPAGO-V-0102-v1.png
│   └── APPPAGO-V-0102-v1.yaml
├── data/                        # Datos persistentes
│   ├── processed_receipts/      # Historial de procesamiento
│   ├── feedback_loop/           # Feedback manual
│   └── probabilistic_model.json # Modelo de aprendizaje
├── input/                       # Imágenes de entrada (temporal)
├── temp/                        # Archivos temporales de depuración
├── logs/                        # Archivos de registro
├── requirements.txt             # Dependencias Python
└── README.md                    # Esta documentación
\`\`\`

## Flujo de Procesamiento

1. **Recepción**: N8N sube imagen a `input/` con ID único
2. **Clasificación**: Detección rápida de "no recibo" para ahorrar recursos
3. **Diagnóstico**: Análisis multimodal de calidad de imagen
4. **Preprocesamiento**: Optimización adaptativa según diagnóstico
5. **OCR General**: Extracción de todo el texto con coordenadas
6. **Identificación**: Selección de plantilla o cálculo de ZOI dinámicas
7. **Extracción**: Procesamiento dirigido de campos específicos
8. **Validación**: Verificación cruzada y heurísticas contextuales
9. **Aprendizaje**: Consulta y actualización del modelo probabilístico
10. **Salida**: JSON estructurado con datos y métricas de confianza

## Campos Extraídos

- **Monto**: Cantidad en bolívares con validación de formato
- **Referencia**: Número de operación (8-15 dígitos)
- **Fecha**: Fecha y hora de la transacción
- **Cédula Origen**: Identificación del emisor
- **Cédula Destino**: Identificación del beneficiario
- **Banco Origen**: Entidad bancaria emisora
- **Banco Destino**: Entidad bancaria receptora

## Sistema de Feedback y Aprendizaje

### Feedback Manual
El administrador puede corregir errores mediante el archivo `manual_feedback.csv`:

\`\`\`csv
id_unico_imagen,campo_nombre,raw_ocr_output,valor_corregido,causa_raiz,timestamp_feedback
img_123,monto,"BS.1,23.45","1.234,50",formato_erroneo,2025-01-27T10:00:00
\`\`\`

### Causas Raíz Disponibles
- `mala_segmentacion`: Problema en la delimitación del campo
- `caracter_mal_reconocido`: Error de OCR en caracteres específicos
- `campo_no_detectado`: Campo no encontrado por el sistema
- `error_de_plantilla`: Plantilla incorrecta o desactualizada
- `formato_erroneo`: Formato de datos incorrecto
- `info_faltante`: Información incompleta en la imagen
- `ruido_imagen`: Interferencia visual en la imagen
- `distorsion_imagen`: Problemas geométricos de la imagen
- `clasificacion_erronea_no_recibo`: Error en clasificación inicial
- `otro`: Otras causas no categorizadas

### Reentrenamiento Automático
El script `update_probabilistic_model.py` procesa el feedback y actualiza el modelo:

\`\`\`bash
python3 src/update_probabilistic_model.py
\`\`\`

## Configuración y Personalización

### Variables Principales (config.py)
- `CLEAN_TEMP_FILES`: Controla limpieza de archivos de depuración
- `LOG_LEVEL`: Nivel de detalle en logs (DEBUG/INFO/WARNING/ERROR)
- `TESSERACT_LANG`: Idioma(s) para Tesseract ("spa", "eng", "spa+eng")
- Umbrales de calidad de imagen y validación

### Depuración Visual
Establecer `CLEAN_TEMP_FILES = False` para conservar:
- `original_preprocessed.png`: Imagen después del preprocesamiento
- `campo_recorte.png`: Recortes específicos por campo
- `debug_overlay.png`: Imagen con campos detectados marcados

## Integración con N8N

### Llamada al Sistema
\`\`\`bash
python3 /ruta/proyecto/src/main.py /ruta/imagen.jpg id_unico_imagen
\`\`\`

### Respuesta JSON
\`\`\`json
{
  "success": true,
  "timestamp": "2025-01-27T10:00:00",
  "data": {
    "monto": {"value": "1.234,50", "confidence": 85.2},
    "referencia": {"value": "123456789", "confidence": 92.1}
  },
  "initial_image_quality": {
    "sharpness": 1250.5,
    "brightness": 145.2,
    "image_type": "Foto de Pantalla"
  }
}
\`\`\`

## Requisitos del Sistema

### Software Base
- Ubuntu Server LTS (22.04 recomendado)
- Python 3.9+ (idealmente 3.10+)
- Tesseract OCR 4.0+
- Paquetes de idioma para Tesseract

### Recursos Mínimos
- RAM: 2GB (4GB recomendado)
- CPU: 2 cores
- Almacenamiento: 5GB libres
- Ancho de banda: Mínimo para transferencia de imágenes

## Instalación

Ver `INSTALLATION_GUIDE.md` para instrucciones detalladas de instalación paso a paso.

## Uso

Ver `USER_GUIDE.md` para guía completa de operación y mantenimiento.

## Soporte y Mantenimiento

### Monitoreo
- Revisar logs en `logs/system.log`
- Monitorear estadísticas de feedback
- Verificar rendimiento de plantillas

### Mantenimiento Periódico
- Ejecutar reentrenamiento semanal/mensual
- Actualizar plantillas según cambios en apps
- Limpiar archivos temporales antiguos
- Revisar y optimizar umbrales de configuración

### Solución de Problemas
1. Verificar instalación de Tesseract: `which tesseract`
2. Comprobar permisos de directorios
3. Revisar logs para errores específicos
4. Validar formato de imágenes de entrada
5. Verificar configuración de variables en `config.py`

## Licencia y Créditos

Sistema desarrollado siguiendo las especificaciones de la "Guía Completa para la Solución Inteligente de OCR de Pagos Móviles V.1.0.1".

**Tecnologías Utilizadas:**
- Tesseract OCR (Apache License
