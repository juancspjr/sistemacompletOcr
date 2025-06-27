# Guía de Usuario - Sistema OCR de Pagos Móviles

## Introducción

Esta guía te enseñará cómo usar el Sistema OCR de Pagos Móviles para extraer datos de recibos de transferencias y pagos móviles de manera automatizada.

## Inicio Rápido

### Activación del Sistema
\`\`\`bash
# Navegar al directorio del proyecto
cd /opt/ocr-pagos

# Activar entorno virtual
source venv/bin/activate

# Verificar que el sistema esté funcionando
python3 src/main.py --help
\`\`\`

## Procesamiento de Imágenes

### Método 1: Procesamiento Individual

#### Preparar la Imagen
\`\`\`bash
# Copiar imagen al directorio de entrada
cp /ruta/a/tu/recibo.jpg input/

# Generar ID único para la imagen
IMAGE_ID="img_$(date +%Y%m%d_%H%M%S)_$(openssl rand -hex 4)"
echo "ID generado: $IMAGE_ID"
\`\`\`

#### Ejecutar Procesamiento
\`\`\`bash
# Procesar imagen individual
python3 src/main.py input/recibo.jpg $IMAGE_ID

# El resultado se mostrará en formato JSON
\`\`\`

#### Ejemplo de Salida Exitosa
\`\`\`json
{
  "success": true,
  "timestamp": "2025-01-27T14:30:25",
  "reason": "processing_completed",
  "data": {
    "extraction_method": "template_based",
    "campos_extraidos": {
      "monto": {
        "value": "1.234,50",
        "confidence": 85.2,
        "extraction_successful": true
      },
      "referencia": {
        "value": "123456789012",
        "confidence": 92.1,
        "extraction_successful": true
      },
      "fecha": {
        "value": "27/01/2025",
        "confidence": 78.5,
        "extraction_successful": true
      }
    },
    "overall_confidence": 85.3,
    "status": "success"
  },
  "initial_image_quality": {
    "sharpness": 1250.5,
    "brightness": 145.2,
    "image_type": "Foto de Pantalla"
  }
}
\`\`\`

### Método 2: Procesamiento por Lotes

#### Script de Procesamiento Múltiple
\`\`\`bash
# Crear script para procesar múltiples imágenes
cat > process_batch.sh << 'EOF'
#!/bin/bash

INPUT_DIR="input"
RESULTS_DIR="results"

mkdir -p $RESULTS_DIR

for image in $INPUT_DIR/*.{jpg,jpeg,png,JPG,JPEG,PNG}; do
    if [ -f "$image" ]; then
        filename=$(basename "$image")
        image_id="batch_$(date +%Y%m%d_%H%M%S)_${filename%.*}"
        
        echo "Procesando: $filename (ID: $image_id)"
        
        python3 src/main.py "$image" "$image_id" > "$RESULTS_DIR/${image_id}.json"
        
        if [ $? -eq 0 ]; then
            echo "✓ Procesado exitosamente: $filename"
        else
            echo "✗ Error procesando: $filename"
        fi
        
        sleep 2  # Pausa entre procesamiento
    fi
done

echo "Procesamiento por lotes completado"
EOF

chmod +x process_batch.sh
./process_batch.sh
\`\`\`

## Interpretación de Resultados

### Estados de Procesamiento

#### ✅ Success (Éxito)
\`\`\`json
{
  "success": true,
  "reason": "processing_completed",
  "data": {
    "status": "success",
    "overall_confidence": 85.3
  }
}
\`\`\`
**Acción**: Los datos están listos para usar.

#### ⚠️ Low Confidence (Baja Confianza)
\`\`\`json
{
  "success": true,
  "reason": "processing_completed",
  "data": {
    "status": "low_confidence",
    "overall_confidence": 45.2
  }
}
\`\`\`
**Acción**: Revisar manualmente los datos extraídos.

#### ❌ No Receipt (No es Recibo)
\`\`\`json
{
  "success": false,
  "reason": "no_payment_receipt",
  "data": {
    "classification_details": {
      "keywords_count": 0,
      "text_area_ratio": 0.001
    }
  }
}
\`\`\`
**Acción**: Verificar que la imagen sea realmente un recibo de pago.

#### 🔧 Validation Failed (Validación Fallida)
\`\`\`json
{
  "success": true,
  "reason": "processing_completed",
  "data": {
    "status": "validation_failed",
    "validation_results": {
      "monto_valid": false,
      "cross_validation_passed": false
    }
  }
}
\`\`\`
**Acción**: Los datos extraídos no pasan las validaciones lógicas.

### Campos Extraídos

| Campo | Descripción | Formato Esperado | Ejemplo |
|-------|-------------|------------------|---------|
| `monto` | Cantidad transferida | X.XXX.XXX,XX | "1.234,50" |
| `referencia` | Número de operación | 8-15 dígitos | "123456789012" |
| `fecha` | Fecha de transacción | DD/MM/YYYY | "27/01/2025" |
| `cedula_origen` | Cédula del emisor | V-XXXXXXXX | "V-12345678" |
| `cedula_destino` | Cédula del receptor | V-XXXXXXXX | "V-87654321" |
| `banco_origen` | Banco emisor | Texto | "Banco de Venezuela" |
| `banco_destino` | Banco receptor | Texto | "Banesco" |

## Depuración y Diagnóstico

### Activar Modo Debug
\`\`\`bash
# Editar configuración para debug
nano src/config.py

# Cambiar estas variables:
CLEAN_TEMP_FILES = False  # Conservar archivos temporales
LOG_LEVEL = "DEBUG"       # Logs detallados
\`\`\`

### Archivos de Depuración

Cuando `CLEAN_TEMP_FILES = False`, se generan archivos útiles en `temp/<image_id>/`:

#### `original_preprocessed.png`
- **Propósito**: Imagen después del preprocesamiento
- **Uso**: Verificar si las mejoras de imagen son efectivas
- **Qué buscar**: Texto más claro, menos ruido, mejor contraste

#### `campo_recorte.png`
- **Propósito**: Recortes específicos de cada campo
- **Archivos**: `monto_recorte.png`, `referencia_recorte.png`, etc.
- **Uso**: Ver exactamente qué región está procesando Tesseract
- **Qué buscar**: Si el recorte captura correctamente el campo deseado

#### `debug_overlay.png`
- **Propósito**: Imagen con campos detectados marcados
- **Uso**: Visualizar dónde el sistema encontró cada campo
- **Elementos**: Rectángulos de colores con etiquetas y confianza

### Análisis de Logs

\`\`\`bash
# Ver logs en tiempo real
tail -f logs/system.log

# Buscar errores específicos
grep "ERROR" logs/system.log

# Filtrar por imagen específica
grep "img_20250127" logs/system.log

# Ver estadísticas de procesamiento
grep "Extracción completada" logs/system.log | tail -10
\`\`\`

## Sistema de Feedback y Corrección

### Proceso de Feedback Manual

Cuando el sistema comete errores, puedes corregirlos para que aprenda:

#### 1. Identificar Error
\`\`\`bash
# Revisar resultado con baja confianza
cat data/processed_receipts/20250127-143025-recibo_001.json
\`\`\`

#### 2. Añadir Corrección
\`\`\`bash
# El sistema crea automáticamente el CSV, pero puedes editarlo:
nano data/feedback_loop/manual_feedback.csv
\`\`\`

#### Formato del CSV de Feedback
\`\`\`csv
id_unico_imagen,campo_nombre,raw_ocr_output,valor_corregido,causa_raiz,timestamp_feedback
img_20250127_143025,monto,"1.23.45","1.234,50",caracter_mal_reconocido,2025-01-27T14:30:25
img_20250127_143025,referencia,"12345B789","123456789",caracter_mal_reconocido,2025-01-27T14:30:25
\`\`\`

#### Causas Raíz Disponibles
- `mala_segmentacion`: El recorte del campo no fue preciso
- `caracter_mal_reconocido`: Tesseract leyó mal algunos caracteres
- `campo_no_detectado`: El sistema no encontró el campo
- `error_de_plantilla`: La plantilla usada no era correcta
- `formato_erroneo`: El formato del dato no es el esperado
- `info_faltante`: Información incompleta en la imagen
- `ruido_imagen`: Mucho ruido visual interfirió
- `distorsion_imagen`: Problemas de perspectiva o inclinación
- `clasificacion_erronea_no_recibo`: Se clasificó mal como "no recibo"
- `otro`: Otras causas no categorizadas

#### 3. Ejecutar Reentrenamiento
\`\`\`bash
# Procesar feedback y actualizar modelo
python3 src/update_probabilistic_model.py

# Ver reporte de reentrenamiento
ls -la logs/retraining_report_*.json
cat logs/retraining_report_$(ls logs/retraining_report_*.json | tail -1 | cut -d'/' -f2)
\`\`\`

### Ejemplo Completo de Corrección

\`\`\`bash
# 1. Procesar imagen
python3 src/main.py input/recibo_problema.jpg img_problema_001

# 2. Revisar resultado (supongamos que el monto salió mal)
# Resultado: "1.23.45" pero debería ser "1.234,50"

# 3. Añadir corrección al CSV
echo "img_problema_001,monto,\"1.23.45\",\"1.234,50\",caracter_mal_reconocido,$(date -Iseconds)" >> data/feedback_loop/manual_feedback.csv

# 4. Reentrenar modelo
python3 src/update_probabilistic_model.py

# 5. Procesar imagen similar para verificar mejora
python3 src/main.py input/recibo_similar.jpg img_test_002
\`\`\`

## Gestión de Plantillas

### Crear Nueva Plantilla

#### 1. Analizar Recibo
\`\`\`bash
# Procesar con debug activado
CLEAN_TEMP_FILES=False python3 src/main.py input/nuevo_tipo_recibo.jpg test_plantilla

# Revisar archivos de debug
ls temp/test_plantilla/
\`\`\`

#### 2. Crear Archivo YAML
\`\`\`bash
# Copiar plantilla base
cp templates/APPPAGO-V-0102-v1.yaml templates/NUEVO-BANCO-v1.yaml

# Editar coordenadas y metadatos
nano templates/NUEVO-BANCO-v1.yaml
\`\`\`

#### 3. Configurar Campos
\`\`\`yaml
campos:
  monto:
    left: 200      # Ajustar según posición real
    top: 150
    width: 180
    height: 35
    palabras_clave_cercanas: ["Monto", "Total", "Bs"]
\`\`\`

#### 4. Probar Plantilla
\`\`\`bash
# Procesar con nueva plantilla
python3 src/main.py input/nuevo_tipo_recibo.jpg test_nueva_plantilla

# Verificar que use la plantilla correcta en los logs
grep "Plantilla identificada" logs/system.log
\`\`\`

## Integración con N8N

### Configuración Básica

#### 1. Nodo Execute Command en N8N
\`\`\`javascript
// Configuración del nodo
const imagePath = $input.first().binary.data.fileName;
const imageId = `n8n_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

return {
  command: 'python3',
  arguments: [
    '/opt/ocr-pagos/src/main.py',
    `/tmp/${imagePath}`,
    imageId
  ],
  workingDirectory: '/opt/ocr-pagos'
};
\`\`\`

#### 2. Procesamiento de Respuesta
\`\`\`javascript
// Nodo Function para procesar JSON
const result = JSON.parse($input.first().json.stdout);

if (result.success && result.data.status === 'success') {
  // Extraer datos para uso posterior
  const extractedData = {
    monto: result.data.campos_extraidos.monto?.value || '',
    referencia: result.data.campos_extraidos.referencia?.value || '',
    fecha: result.data.campos_extraidos.fecha?.value || '',
    confianza: result.data.overall_confidence || 0
  };
  
  return { json: extractedData };
} else {
  // Manejar errores o baja confianza
  return { 
    json: { 
      error: result.reason,
      requiresManualReview: true 
    } 
  };
}
\`\`\`

## Monitoreo y Mantenimiento

### Verificación Diaria
\`\`\`bash
# Script de verificación diaria
cat > daily_check.sh << 'EOF'
#!/bin/bash
echo "=== Verificación Diaria OCR System ==="
echo "Fecha: $(date)"

# Verificar espacio en disco
echo -e "\n📁 Espacio en disco:"
df -h /opt/ocr-pagos | tail -1

# Verificar logs recientes
echo -e "\n📋 Procesamiento últimas 24h:"
find logs/ -name "*.log" -mtime -1 -exec grep -c "processing_completed" {} \;

# Verificar errores recientes
echo -e "\n❌ Errores últimas 24h:"
find logs/ -name "*.log" -mtime -1 -exec grep -c "ERROR" {} \;

# Verificar feedback pendiente
echo -e "\n📝 Feedback pendiente:"
if [ -f "data/feedback_loop/manual_feedback.csv" ]; then
    wc -l data/feedback_loop/manual_feedback.csv
else
    echo "No hay feedback pendiente"
fi

echo -e "\n✅ Verificación completada"
EOF

chmod +x daily_check.sh
./daily_check.sh
\`\`\`

### Limpieza Automática
\`\`\`bash
# Script de limpieza semanal
cat > weekly_cleanup.sh << 'EOF'
#!/bin/bash
echo "=== Limpieza Semanal ==="

# Limpiar archivos temporales antiguos
find temp/ -type f -mtime +7 -delete
find temp/ -type d -empty -delete

# Comprimir logs antiguos
find logs/ -name "*.log" -mtime +30 -exec gzip {} \;

# Limpiar imágenes procesadas antiguas (opcional)
# find data/processed_receipts/images_archive/ -name "*.jpg" -mtime +90 -delete

echo "Limpieza completada"
EOF

chmod +x weekly_cleanup.sh
\`\`\`

### Configurar Cron Jobs
\`\`\`bash
# Editar crontab
crontab -e

# Añadir tareas programadas:
# Verificación diaria a las 8:00 AM
0 8 * * * /opt/ocr-pagos/daily_check.sh >> /opt/ocr-pagos/logs/daily_check.log 2>&1

# Limpieza semanal los domingos a las 2:00 AM
0 2 * * 0 /opt/ocr-pagos/weekly_cleanup.sh >> /opt/ocr-pagos/logs/cleanup.log 2>&1

# Reentrenamiento automático los lunes a las 3:00 AM
0 3 * * 1 cd /opt/ocr-pagos && source venv/bin/activate && python3 src/update_probabilistic_model.py >> logs/auto_retrain.log 2>&1
\`\`\`

## Solución de Problemas Comunes

### Problema: "No se detecta texto"
\`\`\`bash
# Verificar calidad de imagen
python3 -c "
import cv2
img = cv2.imread('input/problema.jpg')
print('Dimensiones:', img.shape)
print('Brillo promedio:', img.mean())
"

# Probar con diferentes configuraciones de Tesseract
tesseract input/problema.jpg stdout -l spa --psm 11
\`\`\`

### Problema: "Baja confianza constante"
\`\`\`bash
# Revisar configuración de umbrales
grep -n "THRESHOLD" src/config.py

# Analizar historial de confianza
grep "overall_confidence" data/processed_receipts/*.json | tail -10
\`\`\`

### Problema: "Plantilla no se identifica"
\`\`\`bash
# Verificar palabras clave en la imagen
tesseract input/problema.jpg stdout -l spa | grep -i "pago\|transferencia\|monto"

# Revisar configuración de plantilla
cat templates/APPPAGO-V-0102-v1.yaml | grep -A5 "huella_texto_clave"
\`\`\`

## Mejores Prácticas

### Calidad de Imágenes
- **Resolución mínima**: 800x600 píxeles
- **Formato preferido**: PNG o JPG de alta calidad
- **Evitar**: Imágenes borrosas, con mucho ruido o mal iluminadas
- **Orientación**: Mantener el recibo derecho (el sistema corrige inclinaciones menores)

### Organización de Archivos
\`\`\`bash
# Estructura recomendada para imágenes
input/
├── 2025-01/
│   ├── banco_venezuela/
│   ├── banesco/
│   └── mercantil/
└── 2025-02/
    └── ...
\`\`\`

### Backup de Datos Críticos
\`\`\`bash
# Script de backup
cat > backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backup/ocr-pagos/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# Backup de datos críticos
cp -r data/ $BACKUP_DIR/
cp -r templates/ $BACKUP_DIR/
cp -r logs/ $BACKUP_DIR/

# Comprimir backup
tar -czf "${BACKUP_DIR}.tar.gz" -C /backup/ocr-pagos/ $(basename $BACKUP_DIR)
rm -rf $BACKUP_DIR

echo "Backup completado: ${BACKUP_DIR}.tar.gz"
EOF
\`\`\`

---

**¿Necesitas ayuda adicional?** Consulta la sección de [Solución de Problemas](#solución-de-problemas-comunes) o revisa los logs del sistema para más detalles.
