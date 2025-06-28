#!/bin/bash

# Instalador Sistema OCR v3.0 - Completamente Limpio
# Basado en lógica exitosa probada

set -e

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}"
echo "=================================================================="
echo "           INSTALADOR SISTEMA OCR v3.0 LIMPIO"
echo "=================================================================="
echo -e "${NC}"
echo "🚀 Basado en lógica exitosa probada"
echo "🧹 Sin archivos basura, solo lo esencial"
echo "⚡ Optimizado para comprobantes de pago móvil"
echo ""

# Verificar Ubuntu
if ! grep -q "Ubuntu" /etc/os-release; then
    echo -e "${RED}Error: Este script requiere Ubuntu${NC}"
    exit 1
fi

echo -e "${YELLOW}📋 Verificando sistema...${NC}"

# Actualizar sistema
echo -e "${BLUE}🔄 Actualizando sistema...${NC}"
sudo apt update -qq
sudo apt install -y python3 python3-pip python3-venv tesseract-ocr tesseract-ocr-spa git

# Verificar Tesseract
if ! command -v tesseract &> /dev/null; then
    echo -e "${RED}❌ Error: Tesseract no instalado${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Tesseract instalado: $(tesseract --version | head -1)${NC}"

# Crear directorio del proyecto
PROJECT_DIR="$HOME/ocr-v3-limpio"
echo -e "${BLUE}📁 Creando proyecto en: $PROJECT_DIR${NC}"

if [ -d "$PROJECT_DIR" ]; then
    echo -e "${YELLOW}⚠️  Directorio existe, creando backup...${NC}"
    mv "$PROJECT_DIR" "${PROJECT_DIR}_backup_$(date +%Y%m%d_%H%M%S)"
fi

mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

# Crear estructura de directorios
echo -e "${BLUE}🏗️  Creando estructura...${NC}"
mkdir -p src input output temp logs scripts

# Crear entorno virtual
echo -e "${BLUE}🐍 Configurando Python...${NC}"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip

# Instalar dependencias
echo -e "${BLUE}📦 Instalando dependencias...${NC}"
cat > requirements.txt << 'EOF'
opencv-python==4.8.1.78
pytesseract==0.3.10
Pillow==10.0.1
numpy==1.24.3
EOF

pip install -r requirements.txt

# Crear archivos del sistema
echo -e "${BLUE}📝 Creando archivos del sistema...${NC}"

# config.py
cat > src/config.py << 'EOF'
"""Configuración Sistema OCR v3.0"""
TESSERACT_LANG = 'spa'
TESSERACT_PSM = '3'
TESSERACT_PSM_OSD_DETECTION = '0'
TESSERACT_OEM = '3'

LAPLACIAN_VAR_HIGH = 1000.0
LAPLACIAN_VAR_MEDIUM = 400.0
BRIGHTNESS_THRESHOLD_HIGH = 180.0
BRIGHTNESS_THRESHOLD_LOW = 70.0
NOISE_THRESHOLD_HIGH = 25.0

OUTPUT_IMAGE_NAME = "debug_extraction.png"
PREPROCESSED_IMAGE_NAME = "preprocessed_image.png"
DEBUG_DRAWING_MARGIN = 10

LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

INPUT_DIR = "input"
OUTPUT_DIR = "output"
TEMP_DIR = "temp"
LOGS_DIR = "logs"

CLEAN_TEMP_FILES = False
EOF

# Script de prueba rápida
cat > test_quick.py << 'EOF'
#!/usr/bin/env python3
import sys
import os
sys.path.append('src')

try:
    import cv2
    import pytesseract
    import numpy as np
    from PIL import Image
    
    print("✅ Todas las dependencias importadas correctamente")
    
    # Verificar Tesseract
    version = pytesseract.get_tesseract_version()
    print(f"✅ Tesseract versión: {version}")
    
    # Verificar idiomas
    try:
        result = pytesseract.run_tesseract('', 'stdout', lang='spa', config='--list-langs')
        if 'spa' in result:
            print("✅ Idioma español disponible")
        else:
            print("⚠️  Idioma español no encontrado")
    except:
        print("⚠️  No se pudo verificar idiomas")
    
    print("\n🎉 Sistema OCR v3.0 listo para usar!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
EOF

chmod +x test_quick.py

# README básico
cat > README.md << 'EOF'
# Sistema OCR v3.0 - Limpio y Optimizado

Sistema de extracción de datos de comprobantes de pago móvil.
Basado en lógica exitosa probada.

## Uso Rápido

```bash
# 1. Activar entorno
source venv/bin/activate

# 2. Procesar imagen
python3 src/main.py input/comprobante.png

# 3. Ver resultados
ls temp/comprobante_*/
