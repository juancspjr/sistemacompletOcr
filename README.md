# Sistema OCR v3.0 - Completamente Limpio

🚀 **Sistema de extracción de datos de comprobantes de pago móvil**  
✨ **Basado en lógica exitosa probada**  
🧹 **Sin archivos basura, solo lo esencial**

## 🎯 Características

- **Lógica Probada**: Basado en script exitoso `direct_ocr_extractor_polished.py`
- **Centro y Expansión**: Técnica de extracción por anclaje de palabras clave
- **Optimizado para Fondos Oscuros**: Como comprobantes de WhatsApp
- **Debug Visual**: Imágenes con marcas de extracción
- **Estructura Limpia**: Solo archivos necesarios

## ⚡ Instalación Rápida

\`\`\`bash
# Crear directorio y descargar
mkdir ~/ocr-v3-limpio && cd ~/ocr-v3-limpio

# Instalar automáticamente
curl -sSL https://raw.githubusercontent.com/tu-repo/install_v3.sh | bash
\`\`\`

## 🚀 Uso

\`\`\`bash
# 1. Activar entorno (siempre)
source venv/bin/activate

# 2. Copiar imagen
cp /ruta/a/comprobante.png input/

# 3. Procesar
python3 src/main.py input/comprobante.png

# 4. Ver resultados
cat temp/comprobante_*/extraction_result.json
\`\`\`

## 📊 Campos Extraídos

| Campo | Ejemplo | Descripción |
|-------|---------|-------------|
| `monto` | `522,70 Bs` | Cantidad transferida |
| `fecha` | `20/06/2025` | Fecha de operación |
| `operacion` | `003039965664` | Número de referencia |
| `identificacion` | `27061025` | Cédula del usuario |
| `origen_numero` | `0102****5071` | Cuenta origen |
| `destino_numero` | `04125318244` | Cuenta destino |
| `banco_completo` | `BANCO MERCANTIL` | Banco receptor |
| `concepto` | `Pago servicios` | Descripción |

## 📁 Estructura del Proyecto

\`\`\`
ocr-v3-limpio/
├── src/
│   ├── config.py           # Configuración
│   ├── image_processor.py  # Preprocesamiento
│   ├── field_extractor.py  # Extracción de campos
│   └── main.py            # Script principal
├── input/                 # Imágenes a procesar
├── temp/                  # Resultados temporales
├── logs/                  # Logs del sistema
├── requirements.txt       # Dependencias
└── README.md             # Esta documentación
\`\`\`

## 🔧 Archivos Generados

Para cada imagen procesada se crea un directorio en `temp/` con:

- **`extraction_result.json`** - Resultado completo con todos los datos
- **`debug_extraction.png`** - Imagen con marcas de extracción
- **`preprocessed_image.png`** - Imagen después del preprocesamiento
- **`ocr_details.json`** - Datos detallados del OCR

## 🎯 Ejemplo de Resultado

\`\`\`json
{
  "success": true,
  "extracted_fields": {
    "monto": {
      "value": "522,70",
      "confidence": 96,
      "keyword_anchor": "Bs"
    },
    "fecha": {
      "value": "20/06/2025",
      "confidence": 95,
      "keyword_anchor": "Fecha:"
    },
    "operacion": {
      "value": "003039965664",
      "confidence": 94,
      "keyword_anchor": "Operación:"
    }
  }
}
\`\`\`

## 🛠️ Solución de Problemas

### Error: "No se encontró Tesseract"
\`\`\`bash
sudo apt install tesseract-ocr tesseract-ocr-spa
\`\`\`

### Error: "Módulo no encontrado"
\`\`\`bash
source venv/bin/activate
pip install -r requirements.txt
\`\`\`

### Baja precisión de extracción
- Verificar que la imagen sea clara
- Comprobar que el texto esté en español
- Revisar archivos de debug en `temp/`

## 🎉 ¡Listo!

El sistema está optimizado para procesar comprobantes como el de tu ejemplo con fondo oscuro y extraerá todos los campos con alta precisión.
\`\`\`
