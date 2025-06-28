# 🧹 Guía de Instalación Limpia OCR v3.0

## 🎯 Objetivo

Crear una instalación completamente nueva del sistema OCR v3.0 basado en la lógica exitosa de `direct_ocr_extractor_polished.py`, eliminando toda complejidad innecesaria.

## 🚀 Instalación en Un Comando

\`\`\`bash
# Crear directorio completamente nuevo
mkdir ~/ocr-v3-nuevo && cd ~/ocr-v3-nuevo

# Descargar e instalar automáticamente
curl -sSL https://raw.githubusercontent.com/juancspjr/sistemacompletOcr/main/scripts/install_v3.sh -o install_v3.sh && chmod +x install_v3.sh && ./install_v3.sh
\`\`\`

## 📋 Pasos Detallados

### 1. Preparación del Sistema

\`\`\`bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependencias
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    tesseract-ocr \
    tesseract-ocr-spa \
    git \
    curl
\`\`\`

### 2. Verificar Tesseract

\`\`\`bash
# Verificar instalación
tesseract --version
tesseract --list-langs | grep spa

# Si no tiene español
sudo apt install tesseract-ocr-spa -y
\`\`\`

### 3. Crear Directorio Limpio

\`\`\`bash
# Crear directorio completamente nuevo
mkdir ~/ocr-v3-limpio
cd ~/ocr-v3-limpio

# Verificar que está vacío
ls -la
\`\`\`

### 4. Ejecutar Instalación

\`\`\`bash
# Descargar script de instalación
curl -sSL https://raw.githubusercontent.com/juancspjr/sistemacompletOcr/main/scripts/install_v3.sh -o install_v3.sh

# Hacer ejecutable
chmod +x install_v3.sh

# Ejecutar instalación
./install_v3.sh
\`\`\`

## ✅ Verificación de Instalación

### Estructura Esperada

\`\`\`
ocr-v3-limpio/
├── src/
│   ├── config.py
│   ├── main.py
│   ├── image_processor.py
│   └── field_extractor.py
├── input/
│   └── test_comprobante.png
├── temp/
├── logs/
├── venv/
├── requirements.txt
└── README.md
\`\`\`

### Prueba Funcional

\`\`\`bash
# Activar entorno
source venv/bin/activate

# Procesar imagen de prueba
python3 src/main.py input/test_comprobante.png

# Verificar resultados
ls temp/test_comprobante_*/
cat temp/test_comprobante_*/extraction_result.json
\`\`\`

### Salida Esperada

\`\`\`json
{
  "version": "3.0",
  "final_status": "success",
  "extraction_result": {
    "success": true,
    "extracted_fields": {
      "monto": {
        "value": "522,70",
        "confidence": 95,
        "extraction_successful": true
      },
      "fecha": {
        "value": "28/12/2024",
        "confidence": 90,
        "extraction_successful": true
      }
    }
  }
}
\`\`\`

## 🎮 Uso del Sistema

### Comando Básico

\`\`\`bash
# Siempre activar entorno primero
source venv/bin/activate

# Procesar cualquier imagen
python3 src/main.py ruta/a/tu/imagen.png
\`\`\`

### Archivos Generados

Para cada procesamiento se crea un directorio en `temp/` con:

- `extraction_result.json`: Resultado completo
- `debug_extraction.png`: Imagen con marcas
- `preprocessed_image.png`: Imagen preprocesada
- `ocr_details.json`: Detalles del OCR

### Ver Logs

\`\`\`bash
# Logs en tiempo real
tail -f logs/ocr_system.log

# Último procesamiento
ls -la temp/ | tail -5
\`\`\`

## 🔧 Características v3.0

### Basado en Lógica Exitosa

- ✅ **Preprocesamiento optimizado**: Para fondos oscuros
- ✅ **Centro y expansión**: Técnica probada de extracción
- ✅ **Binarización extrema**: Mejora contraste
- ✅ **Escalado agresivo**: Aumenta calidad OCR
- ✅ **Validación por regex**: Campos más precisos

### Sin Complejidad Innecesaria

- ❌ **Sin templates complejos**: Lógica directa
- ❌ **Sin múltiples versiones**: Solo lo que funciona
- ❌ **Sin archivos basura**: Estructura limpia
- ❌ **Sin dependencias rotas**: Todo conectado

### Optimizado para Comprobantes

- 📱 **Capturas de WhatsApp**: Fondo oscuro optimizado
- 📄 **Escaneos digitales**: Alta resolución
- 📷 **Fotos físicas**: Reducción de ruido
- 🔄 **Imágenes mixtas**: Adaptativo

## 🎯 Campos Extraídos

| Campo | Descripción | Ejemplo |
|-------|-------------|---------|
| `monto` | Cantidad en Bs | `522,70` |
| `fecha` | Fecha transacción | `28/12/2024` |
| `operacion` | Número referencia | `003039965664` |
| `identificacion` | Cédula usuario | `27061025` |
| `origen_numero` | Teléfono origen | `0102****5071` |
| `destino_numero` | Teléfono destino | `04125318244` |
| `banco_completo` | Nombre banco | `BANCO MERCANTIL` |
| `concepto` | Descripción | `Pago móvil` |

## 🚨 Solución de Problemas

### Error: "Tesseract no encontrado"

\`\`\`bash
# Instalar Tesseract
sudo apt install tesseract-ocr tesseract-ocr-spa -y

# Verificar
tesseract --version
\`\`\`

### Error: "No se detectaron palabras"

\`\`\`bash
# Verificar imagen
file input/mi_imagen.png

# Ver logs
tail -20 logs/ocr_system.log

# Revisar imagen preprocesada
ls temp/mi_imagen_*/preprocessed_image.png
\`\`\`

### Error: "Módulo no encontrado"

\`\`\`bash
# Activar entorno virtual
source venv/bin/activate

# Reinstalar dependencias
pip install -r requirements.txt
\`\`\`

### Baja Confianza en Extracción

1. **Revisar imagen original**: ¿Está clara?
2. **Ver imagen preprocesada**: ¿Se procesó bien?
3. **Comprobar debug**: ¿Se detectaron las palabras clave?
4. **Verificar logs**: ¿Hay errores específicos?

## 🎉 ¡Sistema Listo!

Con esta instalación limpia tienes un sistema OCR v3.0 completamente funcional, basado en lógica probada y sin archivos innecesarios.

### Próximos Pasos

1. **Copiar tus imágenes** a `input/`
2. **Activar entorno**: `source venv/bin/activate`
3. **Procesar**: `python3 src/main.py input/tu_imagen.png`
4. **Ver resultados** en `temp/`

¡El sistema está optimizado para funcionar perfectamente con comprobantes de pago móvil!
